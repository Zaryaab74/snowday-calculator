import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional

# ─────────────────────────────────────────
# Nominatim — ZIP/Postal Code → Lat/Lon
# FREE, no API key needed
# ─────────────────────────────────────────
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# ─────────────────────────────────────────
# Weather.gov — US Weather (FREE, no key)
# ─────────────────────────────────────────
WEATHER_GOV_URL = "https://api.weather.gov/points/{lat},{lon}"

# ─────────────────────────────────────────
# Environment Canada — CA Weather (FREE)
# ─────────────────────────────────────────
ENV_CANADA_URL = "https://api.weather.gc.ca/collections/weather:observations/items"


async def get_weather_data(zip_code: str, country: str) -> Optional[dict]:
    """
    ZIP/Postal code se weather data fetch karo
    """
    # Step 1: ZIP → Lat/Lon
    location = await get_coordinates(zip_code, country)
    if not location:
        return None

    lat, lon = location["lat"], location["lon"]
    city = location["city"]
    region = location["region"]

    # Step 2: Weather fetch karo
    if country == "US":
        weather_days = await get_us_weather(lat, lon)
    else:
        weather_days = await get_canada_weather(lat, lon)

    if not weather_days:
        return None

    return {
        "city": city,
        "region": region,
        "lat": lat,
        "lon": lon,
        "tomorrow": weather_days[0] if len(weather_days) > 0 else {},
        "day_after": weather_days[1] if len(weather_days) > 1 else {},
    }


async def get_coordinates(zip_code: str, country: str) -> Optional[dict]:
    """
    Nominatim se ZIP code → coordinates
    """
    country_code = "us" if country == "US" else "ca"
    params = {
        "q": zip_code,
        "countrycodes": country_code,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }
    headers = {"User-Agent": "SnowDayCalculator/1.0"}  # Nominatim requires User-Agent

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(NOMINATIM_URL, params=params, headers=headers)
            data = resp.json()
            if not data:
                return None

            result = data[0]
            address = result.get("address", {})

            city = (
                address.get("city") or
                address.get("town") or
                address.get("village") or
                address.get("county") or
                "Unknown"
            )
            region = address.get("state") or address.get("province") or ""

            return {
                "lat": float(result["lat"]),
                "lon": float(result["lon"]),
                "city": city,
                "region": region,
            }
        except Exception as e:
            print(f"Nominatim error: {e}")
            return None


async def get_us_weather(lat: float, lon: float) -> list:
    """
    Weather.gov API se US forecast fetch karo
    Step 1: /points → forecast URL
    Step 2: forecast URL → actual weather
    """
    headers = {"User-Agent": "SnowDayCalculator/1.0 (contact@yourdomain.com)"}

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            # Step 1: Get forecast office URL
            points_url = f"https://api.weather.gov/points/{lat},{lon}"
            points_resp = await client.get(points_url, headers=headers)
            points_data = points_resp.json()

            forecast_url = points_data["properties"]["forecast"]

            # Step 2: Get actual forecast
            forecast_resp = await client.get(forecast_url, headers=headers)
            forecast_data = forecast_resp.json()

            periods = forecast_data["properties"]["periods"]

            # Tomorrow aur day after extract karo
            days = []
            seen_dates = []

            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            target_dates = [tomorrow, day_after]

            for period in periods:
                start = period["startTime"][:10]
                if start in target_dates and start not in seen_dates:
                    seen_dates.append(start)
                    days.append(parse_us_period(period))
                if len(days) == 2:
                    break

            # Agar kam data aaya
            while len(days) < 2:
                days.append(empty_weather_day())

            return days

        except Exception as e:
            print(f"Weather.gov error: {e}")
            return []


def parse_us_period(period: dict) -> dict:
    """Weather.gov period ko standard format mein convert karo"""
    detail = period.get("detailedForecast", "").lower()
    short = period.get("shortForecast", "").lower()

    # Snow detect karo
    snow_inches = 0
    if "snow" in detail or "blizzard" in detail:
        # Text se inches parse karo (e.g. "3 to 5 inches")
        import re
        match = re.search(r'(\d+)\s*to\s*(\d+)\s*inch', detail)
        if match:
            snow_inches = (int(match.group(1)) + int(match.group(2))) / 2
        else:
            match = re.search(r'(\d+)\s*inch', detail)
            if match:
                snow_inches = int(match.group(1))
            else:
                snow_inches = 2  # Default agar mention ho but inches nahi

    return {
        "date": period["startTime"][:10],
        "temperature_f": period.get("temperature", 32),
        "temperature_c": round((period.get("temperature", 32) - 32) * 5 / 9, 1),
        "wind_speed": period.get("windSpeed", "0 mph"),
        "short_forecast": period.get("shortForecast", ""),
        "detailed_forecast": period.get("detailedForecast", ""),
        "snow_inches": snow_inches,
        "snow_cm": round(snow_inches * 2.54, 1),
        "is_daytime": period.get("isDaytime", True),
        "precip_chance": extract_precip_chance(detail),
        "conditions": extract_conditions(short),
    }


async def get_canada_weather(lat: float, lon: float) -> list:
    """
    Environment Canada API se CA forecast
    """
    # MSC GeoMet API — free, no key
    url = "https://api.weather.gc.ca/collections/weather:forecast/items"
    params = {
        "bbox": f"{lon-0.1},{lat-0.1},{lon+0.1},{lat+0.1}",
        "f": "json",
        "limit": 50,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, params=params)
            data = resp.json()

            features = data.get("features", [])
            if not features:
                # Fallback: nominatim se nearest station
                return await get_canada_weather_fallback(lat, lon)

            days = []
            seen_dates = []
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            target_dates = [tomorrow, day_after]

            for feature in features:
                props = feature.get("properties", {})
                date_str = props.get("forecast_period_utc", "")[:10]
                if date_str in target_dates and date_str not in seen_dates:
                    seen_dates.append(date_str)
                    days.append(parse_canada_feature(props))
                if len(days) == 2:
                    break

            while len(days) < 2:
                days.append(empty_weather_day())

            return days

        except Exception as e:
            print(f"Environment Canada error: {e}")
            return await get_canada_weather_fallback(lat, lon)


async def get_canada_weather_fallback(lat: float, lon: float) -> list:
    """
    Fallback: Open-Meteo (free, no key) — both US and CA support karta hai
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,snowfall_sum,windspeed_10m_max,precipitation_probability_max",
        "forecast_days": 3,
        "timezone": "auto",
        "temperature_unit": "celsius",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, params=params)
            data = resp.json()
            daily = data.get("daily", {})

            days = []
            # Index 1 = tomorrow, 2 = day after
            for i in [1, 2]:
                snow_cm = daily.get("snowfall_sum", [0, 0, 0])[i] or 0
                temp_c = daily.get("temperature_2m_max", [0, 0, 0])[i] or 0
                wind = daily.get("windspeed_10m_max", [0, 0, 0])[i] or 0
                precip = daily.get("precipitation_probability_max", [0, 0, 0])[i] or 0

                days.append({
                    "date": daily.get("time", ["", "", ""])[i],
                    "temperature_c": temp_c,
                    "temperature_f": round(temp_c * 9 / 5 + 32, 1),
                    "wind_speed": f"{wind} km/h",
                    "snow_cm": snow_cm,
                    "snow_inches": round(snow_cm / 2.54, 1),
                    "precip_chance": precip,
                    "short_forecast": "Snow" if snow_cm > 0 else "Clear",
                    "detailed_forecast": f"{snow_cm}cm snow expected" if snow_cm > 0 else "No snow expected",
                    "is_daytime": True,
                    "conditions": ["snow"] if snow_cm > 2 else [],
                })

            return days

        except Exception as e:
            print(f"Open-Meteo fallback error: {e}")
            return []


def parse_canada_feature(props: dict) -> dict:
    snow_cm = props.get("total_snow_cm", 0) or 0
    temp_c = props.get("air_temperature_max", 0) or 0
    return {
        "date": props.get("forecast_period_utc", "")[:10],
        "temperature_c": temp_c,
        "temperature_f": round(temp_c * 9 / 5 + 32, 1),
        "wind_speed": f"{props.get('wind_speed_kmh', 0)} km/h",
        "snow_cm": snow_cm,
        "snow_inches": round(snow_cm / 2.54, 1),
        "precip_chance": props.get("precipitation_probability", 0) or 0,
        "short_forecast": props.get("weather_condition", ""),
        "detailed_forecast": props.get("forecast_text", ""),
        "is_daytime": True,
        "conditions": extract_conditions(props.get("weather_condition", "").lower()),
    }


def extract_precip_chance(text: str) -> int:
    import re
    match = re.search(r'(\d+)\s*percent', text)
    return int(match.group(1)) if match else 0


def extract_conditions(text: str) -> list:
    conditions = []
    if "snow" in text or "blizzard" in text: conditions.append("snow")
    if "ice" in text or "freezing" in text: conditions.append("ice")
    if "wind" in text: conditions.append("wind")
    if "rain" in text: conditions.append("rain")
    return conditions


def empty_weather_day() -> dict:
    return {
        "date": "", "temperature_f": 32, "temperature_c": 0,
        "wind_speed": "0", "snow_inches": 0, "snow_cm": 0,
        "precip_chance": 0, "short_forecast": "Unknown",
        "detailed_forecast": "", "is_daytime": True, "conditions": []
    }
