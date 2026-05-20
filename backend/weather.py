import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional

# ─────────────────────────────────────────
# Zippopotam — ZIP → City/Lat/Lon (FREE, no key, no User-Agent issues)
# ─────────────────────────────────────────
# Canada postal codes → postcodes.io
# ─────────────────────────────────────────


async def get_weather_data(zip_code: str, country: str) -> Optional[dict]:
    location = await get_coordinates(zip_code, country)
    if not location:
        return None

    lat, lon = location["lat"], location["lon"]

    # Both US and Canada — Open-Meteo (free, no key, very reliable)
    weather_days = await get_openmeteo_weather(lat, lon, country)

    if not weather_days:
        return None

    return {
        "city": location["city"],
        "region": location["region"],
        "lat": lat,
        "lon": lon,
        "tomorrow": weather_days[0] if len(weather_days) > 0 else {},
        "day_after": weather_days[1] if len(weather_days) > 1 else {},
    }


async def get_coordinates(zip_code: str, country: str) -> Optional[dict]:
    cleaned = zip_code.replace(" ", "").upper()

    if country == "US":
        return await get_us_coordinates(cleaned)
    else:
        return await get_canada_coordinates(cleaned)


async def get_us_coordinates(zip_code: str) -> Optional[dict]:
    """
    Zippopotam.us — free, no key, no rate limits
    """
    url = f"https://api.zippopotam.us/us/{zip_code}"

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            data = resp.json()
            place = data["places"][0]
            return {
                "lat": float(place["latitude"]),
                "lon": float(place["longitude"]),
                "city": place["place name"],
                "region": place["state"],
            }
        except Exception as e:
            print(f"Zippopotam error: {e}")
            return None


async def get_canada_coordinates(postal_code: str) -> Optional[dict]:
    """
    Geocoder.ca / Zippopotam for Canada
    Format: first 3 chars (FSA) is enough
    """
    # Try full postal code first
    fsa = postal_code[:3]  # Forward Sortation Area
    url = f"https://api.zippopotam.us/ca/{fsa}"

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                place = data["places"][0]
                return {
                    "lat": float(place["latitude"]),
                    "lon": float(place["longitude"]),
                    "city": place["place name"],
                    "region": place["province abbreviation"],
                }
        except Exception as e:
            print(f"Canada coords error: {e}")

        # Fallback: geocode.maps.co (free, no key)
        try:
            url2 = f"https://geocode.maps.co/search?q={postal_code}+Canada&limit=1"
            resp2 = await client.get(url2)
            if resp2.status_code == 200:
                data2 = resp2.json()
                if data2:
                    return {
                        "lat": float(data2[0]["lat"]),
                        "lon": float(data2[0]["lon"]),
                        "city": data2[0].get("display_name", "").split(",")[0],
                        "region": "",
                    }
        except Exception as e2:
            print(f"Geocode fallback error: {e2}")

        return None


async def get_openmeteo_weather(lat: float, lon: float, country: str) -> list:
    """
    Open-Meteo — completely free, no API key, works worldwide
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "snowfall_sum",
            "windspeed_10m_max",
            "precipitation_probability_max",
            "weathercode",
        ],
        "forecast_days": 3,
        "timezone": "auto",
        "temperature_unit": "celsius",
        "windspeed_unit": "mph",
        "precipitation_unit": "inch",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, params=params)
            data = resp.json()
            daily = data.get("daily", {})

            days = []
            for i in [1, 2]:  # tomorrow, day after
                snow_cm = (daily.get("snowfall_sum", [0, 0, 0])[i] or 0) * 2.54  # inches → cm
                snow_inches = daily.get("snowfall_sum", [0, 0, 0])[i] or 0
                temp_c = daily.get("temperature_2m_max", [0, 0, 0])[i] or 0
                temp_f = round(temp_c * 9 / 5 + 32, 1)
                wind_mph = daily.get("windspeed_10m_max", [0, 0, 0])[i] or 0
                precip = daily.get("precipitation_probability_max", [0, 0, 0])[i] or 0
                wcode = daily.get("weathercode", [0, 0, 0])[i] or 0

                conditions = get_conditions_from_wmo(wcode)
                forecast_text = get_forecast_text(wcode)

                days.append({
                    "date": daily.get("time", ["", "", ""])[i],
                    "temperature_c": round(temp_c, 1),
                    "temperature_f": temp_f,
                    "wind_speed": f"{wind_mph} mph",
                    "snow_cm": round(snow_cm, 1),
                    "snow_inches": round(snow_inches, 1),
                    "precip_chance": precip,
                    "short_forecast": forecast_text,
                    "detailed_forecast": f"{forecast_text}. Snow: {round(snow_inches,1)}in. Wind: {wind_mph}mph",
                    "is_daytime": True,
                    "conditions": conditions,
                })

            return days

        except Exception as e:
            print(f"Open-Meteo error: {e}")
            return []


def get_conditions_from_wmo(code: int) -> list:
    """WMO weather codes → conditions list"""
    conditions = []
    # Snow codes: 71-77, 85-86
    if code in range(71, 78) or code in [85, 86]:
        conditions.append("snow")
    # Freezing rain: 56-57, 66-67
    if code in [56, 57, 66, 67]:
        conditions.append("ice")
    # Heavy wind / storm: 95-99
    if code in range(95, 100):
        conditions.append("wind")
    # Rain: 51-67, 80-82
    if code in range(51, 68) or code in range(80, 83):
        conditions.append("rain")
    return conditions


def get_forecast_text(code: int) -> str:
    """WMO weather interpretation codes → human readable"""
    wmo_map = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Icy fog",
        51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        77: "Snow grains",
        80: "Rain showers", 81: "Moderate showers", 82: "Violent showers",
        85: "Snow showers", 86: "Heavy snow showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Severe thunderstorm",
    }
    return wmo_map.get(code, "Mixed conditions")


def empty_weather_day() -> dict:
    return {
        "date": "", "temperature_f": 32, "temperature_c": 0,
        "wind_speed": "0 mph", "snow_inches": 0, "snow_cm": 0,
        "precip_chance": 0, "short_forecast": "Unknown",
        "detailed_forecast": "", "is_daytime": True, "conditions": []
    }
