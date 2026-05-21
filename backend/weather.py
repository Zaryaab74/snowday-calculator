"""
Snow Day Calculator — Weather Module
======================================
🇺🇸 USA:
  Coordinates : Zippopotam.us     (free, unlimited, no key)
  Weather     : Weather.gov/NWS   (official, unlimited, no key)
                → Open-Meteo      (fallback, 10k/day, no key)

🇨🇦 Canada:
  Coordinates : Zippopotam.us     (free, unlimited, no key)
  Weather     : Open-Meteo        (free, 10k/day, no key)
                → wttr.in         (fallback, unlimited, no key)
"""

import httpx
import re
from datetime import datetime, timedelta
from typing import Optional

HEADERS = {
    "User-Agent": "SnowDayCalculator/1.0 (contact@snowdaycalculator.com)",
    "Accept":     "application/json",
}


# ═════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════
async def get_weather_data(zip_code: str, country: str) -> Optional[dict]:
    location = await get_coordinates(zip_code, country)
    if not location:
        print(f"[weather] ❌ Could not find coordinates for {zip_code}")
        return None

    lat, lon = location["lat"], location["lon"]
    print(f"[weather] 📍 {location['city']}, {location['region']} ({lat}, {lon})")

    if country == "US":
        weather_days = await get_us_weather(lat, lon)
    else:
        weather_days = await get_canada_weather(lat, lon)

    if not weather_days:
        print(f"[weather] ❌ Could not fetch weather")
        return None

    return {
        "city":      location["city"],
        "region":    location["region"],
        "lat":       lat,
        "lon":       lon,
        "tomorrow":  weather_days[0] if len(weather_days) > 0 else empty_weather_day(),
        "day_after": weather_days[1] if len(weather_days) > 1 else empty_weather_day(),
    }


# ═════════════════════════════════════════════════════════════════════════════
# COORDINATES — Zippopotam (US + Canada)
# No key · No rate limits · Unlimited
# https://docs.zippopotam.us
# ═════════════════════════════════════════════════════════════════════════════
async def get_coordinates(zip_code: str, country: str) -> Optional[dict]:
    cleaned = zip_code.replace(" ", "").upper()
    if country == "US":
        result = await zippopotam_us(cleaned)
        if result:
            print(f"[coords] 🇺🇸 Zippopotam ✅")
            return result
        print(f"[coords] 🇺🇸 Zippopotam ❌ — invalid ZIP?")
        return None
    else:
        result = await zippopotam_ca(cleaned)
        if result:
            print(f"[coords] 🇨🇦 Zippopotam ✅")
            return result
        print(f"[coords] 🇨🇦 Zippopotam ❌ — invalid postal code?")
        return None


async def zippopotam_us(zip_code: str) -> Optional[dict]:
    """
    🇺🇸 Zippopotam.us — US ZIP → Lat/Lon
    Free · Unlimited · No key
    """
    async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
        try:
            resp = await client.get(f"https://api.zippopotam.us/us/{zip_code}")
            if resp.status_code != 200:
                print(f"[zippopotam_us] status: {resp.status_code}")
                return None
            data  = resp.json()
            place = data["places"][0]
            return {
                "lat":    float(place["latitude"]),
                "lon":    float(place["longitude"]),
                "city":   place["place name"],
                "region": place["state abbreviation"],
            }
        except Exception as e:
            print(f"[zippopotam_us] error: {e}")
            return None


async def zippopotam_ca(postal_code: str) -> Optional[dict]:
    """
    🇨🇦 Zippopotam.us — Canada Postal → Lat/Lon
    Uses FSA (first 3 chars) e.g. K1A from K1A0A6
    Free · Unlimited · No key
    """
    fsa = postal_code[:3].upper()
    async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
        try:
            resp = await client.get(f"https://api.zippopotam.us/ca/{fsa}")
            if resp.status_code != 200:
                print(f"[zippopotam_ca] status: {resp.status_code}")
                return None
            data  = resp.json()
            place = data["places"][0]
            return {
                "lat":    float(place["latitude"]),
                "lon":    float(place["longitude"]),
                "city":   place["place name"],
                "region": place.get("province abbreviation", "CA"),
            }
        except Exception as e:
            print(f"[zippopotam_ca] error: {e}")
            return None


# ═════════════════════════════════════════════════════════════════════════════
# 🇺🇸 US WEATHER
# ═════════════════════════════════════════════════════════════════════════════
async def get_us_weather(lat: float, lon: float) -> list:
    # Primary: Weather.gov (official US government)
    result = await weather_gov(lat, lon)
    if result:
        print("[weather_us] 🇺🇸 Weather.gov ✅")
        return result

    # Fallback: Open-Meteo
    print("[weather_us] Weather.gov ❌ → trying Open-Meteo")
    result = await open_meteo(lat, lon)
    if result:
        print("[weather_us] Open-Meteo fallback ✅")
        return result

    print("[weather_us] ❌ All weather APIs failed")
    return []


async def weather_gov(lat: float, lon: float) -> list:
    """
    🇺🇸 OFFICIAL — National Weather Service
    https://api.weather.gov — No key · Unlimited · US government
    Step 1: /points/{lat},{lon} → get forecast URL
    Step 2: forecast URL → actual forecast data
    """
    headers = {**HEADERS, "Accept": "application/geo+json"}
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        try:
            # Step 1: Get gridpoint info
            points_resp = await client.get(
                f"https://api.weather.gov/points/{lat},{lon}"
            )
            if points_resp.status_code != 200:
                print(f"[weather_gov] points: {points_resp.status_code}")
                return []

            forecast_url = points_resp.json()["properties"]["forecast"]

            # Step 2: Get forecast
            forecast_resp = await client.get(forecast_url)
            if forecast_resp.status_code != 200:
                print(f"[weather_gov] forecast: {forecast_resp.status_code}")
                return []

            periods   = forecast_resp.json()["properties"]["periods"]
            tomorrow  = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            targets   = [tomorrow, day_after]
            days, seen = [], []

            for period in periods:
                date = period["startTime"][:10]
                if date in targets and date not in seen:
                    seen.append(date)
                    days.append(_parse_weather_gov(period))
                if len(days) == 2:
                    break

            while len(days) < 2:
                days.append(empty_weather_day())

            return days

        except Exception as e:
            print(f"[weather_gov] error: {e}")
            return []


def _parse_weather_gov(period: dict) -> dict:
    detail      = period.get("detailedForecast", "").lower()
    short       = period.get("shortForecast",   "").lower()
    snow_inches = 0

    if "snow" in detail or "blizzard" in detail:
        m = re.search(r'(\d+)\s*to\s*(\d+)\s*inch', detail)
        if m:
            snow_inches = (int(m.group(1)) + int(m.group(2))) / 2
        else:
            m = re.search(r'(\d+)\s*inch', detail)
            snow_inches = int(m.group(1)) if m else 2

    temp_f = period.get("temperature", 32)
    return {
        "date":              period["startTime"][:10],
        "temperature_f":     temp_f,
        "temperature_c":     round((temp_f - 32) * 5 / 9, 1),
        "wind_speed":        period.get("windSpeed", "0 mph"),
        "short_forecast":    period.get("shortForecast", ""),
        "detailed_forecast": period.get("detailedForecast", ""),
        "snow_inches":       snow_inches,
        "snow_cm":           round(snow_inches * 2.54, 1),
        "is_daytime":        period.get("isDaytime", True),
        "precip_chance":     _extract_precip(detail),
        "conditions":        _extract_conditions(short),
    }


# ═════════════════════════════════════════════════════════════════════════════
# 🇨🇦 CANADA WEATHER
# ═════════════════════════════════════════════════════════════════════════════
async def get_canada_weather(lat: float, lon: float) -> list:
    # Primary: Open-Meteo (includes Canadian GEM model)
    result = await open_meteo(lat, lon)
    if result:
        print("[weather_ca] 🇨🇦 Open-Meteo ✅")
        return result

    # Fallback: wttr.in
    print("[weather_ca] Open-Meteo ❌ → trying wttr.in")
    result = await wttr_in(lat, lon)
    if result:
        print("[weather_ca] wttr.in fallback ✅")
        return result

    print("[weather_ca] ❌ All weather APIs failed")
    return []


# ═════════════════════════════════════════════════════════════════════════════
# SHARED WEATHER APIs
# ═════════════════════════════════════════════════════════════════════════════
async def open_meteo(lat: float, lon: float) -> list:
    """
    Open-Meteo — Free · 10,000 calls/day · No key
    Includes Canadian GEM model for accurate CA forecasts
    https://open-meteo.com
    """
    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
        try:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude":             lat,
                    "longitude":            lon,
                    "daily": [
                        "temperature_2m_max",
                        "snowfall_sum",
                        "windspeed_10m_max",
                        "precipitation_probability_max",
                        "weathercode",
                    ],
                    "forecast_days":        3,
                    "timezone":             "auto",
                    "temperature_unit":     "celsius",
                    "windspeed_unit":       "mph",
                    "precipitation_unit":   "inch",
                }
            )
            if resp.status_code != 200:
                print(f"[open_meteo] status: {resp.status_code}")
                return []

            daily = resp.json().get("daily", {})
            times = daily.get("time", [])
            days  = []

            for i in [1, 2]:
                if i >= len(times):
                    days.append(empty_weather_day())
                    continue

                snow_in  = float(daily.get("snowfall_sum",                 [0,0,0])[i] or 0)
                temp_c   = float(daily.get("temperature_2m_max",           [0,0,0])[i] or 0)
                wind_mph = float(daily.get("windspeed_10m_max",             [0,0,0])[i] or 0)
                precip   = float(daily.get("precipitation_probability_max", [0,0,0])[i] or 0)
                wcode    = int(  daily.get("weathercode",                   [0,0,0])[i] or 0)
                txt      = _wmo_text(wcode)

                days.append({
                    "date":              times[i],
                    "temperature_c":     round(temp_c, 1),
                    "temperature_f":     round(temp_c * 9 / 5 + 32, 1),
                    "wind_speed":        f"{wind_mph} mph",
                    "snow_cm":           round(snow_in * 2.54, 1),
                    "snow_inches":       round(snow_in, 1),
                    "precip_chance":     precip,
                    "short_forecast":    txt,
                    "detailed_forecast": f"{txt}. Snow: {round(snow_in,1)}in. Wind: {wind_mph}mph",
                    "is_daytime":        True,
                    "conditions":        _wmo_conditions(wcode),
                })

            return days

        except Exception as e:
            print(f"[open_meteo] error: {e}")
            return []


async def wttr_in(lat: float, lon: float) -> list:
    """
    wttr.in — Free · Unlimited · No key
    Fallback for Canada weather
    https://wttr.in
    """
    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
        try:
            resp = await client.get(
                f"https://wttr.in/{lat},{lon}",
                params={"format": "j1"},  # JSON format
            )
            if resp.status_code != 200:
                print(f"[wttr_in] status: {resp.status_code}")
                return []

            data    = resp.json()
            weather = data.get("weather", [])
            days    = []

            # weather[0]=today, [1]=tomorrow, [2]=day after
            for i in [1, 2]:
                if i >= len(weather):
                    days.append(empty_weather_day())
                    continue

                day       = weather[i]
                date_str  = day.get("date", "")
                temp_max_c = float(day.get("maxtempC", 0))
                snow_cm   = float(day.get("totalSnow_cm", 0))
                hourly    = day.get("hourly", [{}])
                wind_mph  = float(hourly[4].get("windspeedMiles", 0)) if len(hourly) > 4 else 0
                desc      = hourly[4].get("weatherDesc", [{}])[0].get("value", "") if len(hourly) > 4 else ""
                precip    = float(hourly[4].get("chanceofrain", 0)) if len(hourly) > 4 else 0

                days.append({
                    "date":              date_str,
                    "temperature_c":     round(temp_max_c, 1),
                    "temperature_f":     round(temp_max_c * 9 / 5 + 32, 1),
                    "wind_speed":        f"{wind_mph} mph",
                    "snow_cm":           snow_cm,
                    "snow_inches":       round(snow_cm / 2.54, 1),
                    "precip_chance":     precip,
                    "short_forecast":    desc,
                    "detailed_forecast": desc,
                    "is_daytime":        True,
                    "conditions":        _extract_conditions(desc.lower()),
                })

            return days

        except Exception as e:
            print(f"[wttr_in] error: {e}")
            return []


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════
def _extract_precip(text: str) -> int:
    m = re.search(r'(\d+)\s*percent', text)
    return int(m.group(1)) if m else 0


def _extract_conditions(text: str) -> list:
    c = []
    if "snow"    in text or "blizzard" in text: c.append("snow")
    if "ice"     in text or "freezing" in text: c.append("ice")
    if "wind"    in text or "gale"     in text: c.append("wind")
    if "rain"    in text or "drizzle"  in text: c.append("rain")
    return c


def _wmo_conditions(code: int) -> list:
    c = []
    if code in range(71, 78) or code in [85, 86]:      c.append("snow")
    if code in [56, 57, 66, 67]:                        c.append("ice")
    if code in range(95, 100):                          c.append("wind")
    if code in range(51, 68) or code in range(80, 83):  c.append("rain")
    return c


def _wmo_text(code: int) -> str:
    wmo = {
        0:  "Clear sky",          1:  "Mainly clear",       2:  "Partly cloudy",
        3:  "Overcast",           45: "Foggy",              48: "Icy fog",
        51: "Light drizzle",      53: "Drizzle",            55: "Heavy drizzle",
        61: "Slight rain",        63: "Moderate rain",      65: "Heavy rain",
        71: "Slight snow",        73: "Moderate snow",      75: "Heavy snow",
        77: "Snow grains",        80: "Rain showers",       81: "Moderate showers",
        82: "Violent showers",    85: "Snow showers",       86: "Heavy snow showers",
        95: "Thunderstorm",       96: "Thunderstorm + hail", 99: "Severe thunderstorm",
    }
    return wmo.get(code, "Mixed conditions")


def empty_weather_day() -> dict:
    return {
        "date": "", "temperature_f": 32, "temperature_c": 0,
        "wind_speed": "0 mph", "snow_inches": 0, "snow_cm": 0,
        "precip_chance": 0, "short_forecast": "Unknown",
        "detailed_forecast": "", "is_daytime": True, "conditions": [],
    }
