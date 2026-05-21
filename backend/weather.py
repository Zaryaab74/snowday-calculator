"""
Snow Day Calculator — Weather Module
=====================================
🇺🇸 USA:
  Coordinates : Census Geocoder (official) → Zippopotam (fallback)
  Weather     : Weather.gov/NWS (official) → Open-Meteo (fallback)

🇨🇦 Canada:
  Coordinates : Geogratis.gc.ca (official) → Zippopotam (fallback)
  Weather     : ECCC MSC (official) → Open-Meteo (fallback)
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
        print(f"[weather] Could not find coordinates for {zip_code}")
        return None

    lat, lon = location["lat"], location["lon"]
    print(f"[weather] Location: {location['city']}, {location['region']} ({lat}, {lon})")

    if country == "US":
        weather_days = await get_us_weather(lat, lon)
    else:
        weather_days = await get_canada_weather(lat, lon)

    if not weather_days:
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
# COORDINATES
# ═════════════════════════════════════════════════════════════════════════════
async def get_coordinates(zip_code: str, country: str) -> Optional[dict]:
    cleaned = zip_code.replace(" ", "").upper()
    if country == "US":
        result = await us_census_geocoder(cleaned)
        if result:
            print("[coords] US: Census Geocoder ✅")
            return result
        print("[coords] US: Census failed → trying Zippopotam")
        result = await us_zippopotam(cleaned)
        if result:
            print("[coords] US: Zippopotam fallback ✅")
            return result
        print("[coords] US: All APIs failed ❌")
        return None
    else:
        result = await ca_geogratis(cleaned)
        if result:
            print("[coords] CA: Geogratis ✅")
            return result
        print("[coords] CA: Geogratis failed → trying Zippopotam")
        result = await ca_zippopotam(cleaned)
        if result:
            print("[coords] CA: Zippopotam fallback ✅")
            return result
        print("[coords] CA: All APIs failed ❌")
        return None


async def us_census_geocoder(zip_code: str) -> Optional[dict]:
    """
    🇺🇸 OFFICIAL — US Census Bureau Geocoder
    Fixed: using 'zip' param directly with returntype=locations
    """
    # Method 1: ZIP code lookup endpoint
    url = "https://geocoding.geo.census.gov/geocoder/locations/address"
    params = {
        "street":    "",
        "city":      "",
        "state":     "",
        "zip":       zip_code,
        "benchmark": "2020",
        "format":    "json",
    }
    async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                matches = resp.json().get("result", {}).get("addressMatches", [])
                if matches:
                    coords = matches[0]["coordinates"]
                    comps  = matches[0].get("addressComponents", {})
                    return {
                        "lat":    float(coords["y"]),
                        "lon":    float(coords["x"]),
                        "city":   comps.get("city", "Unknown"),
                        "region": comps.get("state", ""),
                    }

            # Method 2: batch geocoder with zip
            url2 = f"https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
            params2 = {
                "address":   zip_code,
                "benchmark": "Public_AR_Current",
                "format":    "json",
            }
            resp2 = await client.get(url2, params=params2)
            if resp2.status_code == 200:
                matches2 = resp2.json().get("result", {}).get("addressMatches", [])
                if matches2:
                    coords = matches2[0]["coordinates"]
                    comps  = matches2[0].get("addressComponents", {})
                    return {
                        "lat":    float(coords["y"]),
                        "lon":    float(coords["x"]),
                        "city":   comps.get("city", "Unknown"),
                        "region": comps.get("state", ""),
                    }
        except Exception as e:
            print(f"[census] error: {e}")
        return None


async def us_zippopotam(zip_code: str) -> Optional[dict]:
    """🇺🇸 FALLBACK — Zippopotam.us"""
    async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
        try:
            resp = await client.get(f"https://api.zippopotam.us/us/{zip_code}")
            if resp.status_code != 200:
                return None
            place = resp.json()["places"][0]
            return {
                "lat":    float(place["latitude"]),
                "lon":    float(place["longitude"]),
                "city":   place["place name"],
                "region": place["state abbreviation"],
            }
        except Exception as e:
            print(f"[zippopotam_us] error: {e}")
            return None


async def ca_geogratis(postal_code: str) -> Optional[dict]:
    """
    🇨🇦 OFFICIAL — Natural Resources Canada / Geogratis
    Fixed: search by city name derived from postal prefix
    """
    fsa = postal_code[:3]
    async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
        try:
            # Method 1: search geonames with postal code
            resp = await client.get(
                "https://geogratis.gc.ca/services/geoname/en/geonames.json",
                params={"q": postal_code, "num": 1}
            )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    item = items[0]
                    lat = float(item.get("latitude",  0))
                    lon = float(item.get("longitude", 0))
                    if lat != 0 and lon != 0:
                        print(f"[geogratis] method1 found: {item.get('name')}")
                        return {
                            "lat":    lat,
                            "lon":    lon,
                            "city":   item.get("name", "Unknown"),
                            "region": item.get("province", {}).get("code", "CA") if isinstance(item.get("province"), dict) else str(item.get("province", "CA")),
                        }

            # Method 2: FSA only
            resp2 = await client.get(
                "https://geogratis.gc.ca/services/geoname/en/geonames.json",
                params={"q": fsa, "num": 1}
            )
            if resp2.status_code == 200:
                items2 = resp2.json().get("items", [])
                if items2:
                    item = items2[0]
                    lat = float(item.get("latitude",  0))
                    lon = float(item.get("longitude", 0))
                    if lat != 0 and lon != 0:
                        return {
                            "lat":    lat,
                            "lon":    lon,
                            "city":   item.get("name", "Unknown"),
                            "region": item.get("province", {}).get("code", "CA") if isinstance(item.get("province"), dict) else str(item.get("province", "CA")),
                        }
        except Exception as e:
            print(f"[geogratis] error: {e}")
        return None


async def ca_zippopotam(postal_code: str) -> Optional[dict]:
    """🇨🇦 FALLBACK — Zippopotam for Canada (FSA)"""
    fsa = postal_code[:3].upper()
    async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
        try:
            resp = await client.get(f"https://api.zippopotam.us/ca/{fsa}")
            if resp.status_code != 200:
                return None
            place = resp.json()["places"][0]
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
    result = await weather_gov(lat, lon)
    if result:
        print("[weather_us] Weather.gov ✅")
        return result
    print("[weather_us] Weather.gov failed → trying Open-Meteo")
    result = await open_meteo(lat, lon)
    if result:
        print("[weather_us] Open-Meteo fallback ✅")
        return result
    print("[weather_us] All APIs failed ❌")
    return []


async def weather_gov(lat: float, lon: float) -> list:
    """
    🇺🇸 OFFICIAL — National Weather Service
    https://api.weather.gov — No key, US government
    """
    headers = {**HEADERS, "Accept": "application/geo+json"}
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        try:
            points_resp = await client.get(f"https://api.weather.gov/points/{lat},{lon}")
            if points_resp.status_code != 200:
                print(f"[weather_gov] points failed: {points_resp.status_code}")
                return []

            forecast_url = points_resp.json()["properties"]["forecast"]

            forecast_resp = await client.get(forecast_url)
            if forecast_resp.status_code != 200:
                print(f"[weather_gov] forecast failed: {forecast_resp.status_code}")
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
                    days.append(parse_weather_gov_period(period))
                if len(days) == 2:
                    break

            while len(days) < 2:
                days.append(empty_weather_day())

            return days
        except Exception as e:
            print(f"[weather_gov] error: {e}")
            return []


def parse_weather_gov_period(period: dict) -> dict:
    detail = period.get("detailedForecast", "").lower()
    short  = period.get("shortForecast",   "").lower()
    snow_inches = 0
    if "snow" in detail or "blizzard" in detail:
        match = re.search(r'(\d+)\s*to\s*(\d+)\s*inch', detail)
        if match:
            snow_inches = (int(match.group(1)) + int(match.group(2))) / 2
        else:
            match = re.search(r'(\d+)\s*inch', detail)
            snow_inches = int(match.group(1)) if match else 2
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
        "precip_chance":     extract_precip_chance(detail),
        "conditions":        extract_conditions(short),
    }


# ═════════════════════════════════════════════════════════════════════════════
# 🇨🇦 CANADA WEATHER
# ═════════════════════════════════════════════════════════════════════════════
async def get_canada_weather(lat: float, lon: float) -> list:
    result = await eccc_weather(lat, lon)
    if result:
        print("[weather_ca] ECCC ✅")
        return result
    print("[weather_ca] ECCC failed → trying Open-Meteo")
    result = await open_meteo(lat, lon)
    if result:
        print("[weather_ca] Open-Meteo fallback ✅")
        return result
    print("[weather_ca] All APIs failed ❌")
    return []


async def eccc_weather(lat: float, lon: float) -> list:
    """
    🇨🇦 OFFICIAL — Environment & Climate Change Canada (ECCC)
    Fixed endpoint: using correct MSC GeoMet OGC API URL
    https://api.weather.gc.ca
    """
    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:

        # Method 1: forecast collections endpoint
        try:
            url = "https://api.weather.gc.ca/collections/weather:forecast/items"
            params = {
                "bbox":  f"{lon-0.2},{lat-0.2},{lon+0.2},{lat+0.2}",
                "f":     "json",
                "limit": 100,
            }
            resp = await client.get(url, params=params)
            print(f"[eccc] method1 status: {resp.status_code}")
            if resp.status_code == 200:
                features = resp.json().get("features", [])
                if features:
                    days = parse_eccc_features(features)
                    if days:
                        return days

        except Exception as e:
            print(f"[eccc] method1 error: {e}")

        # Method 2: AHCCD climate normals / MSC datamart XML
        try:
            url2 = "https://api.weather.gc.ca/collections/climate-normals/items"
            params2 = {
                "bbox":  f"{lon-0.5},{lat-0.5},{lon+0.5},{lat+0.5}",
                "f":     "json",
                "limit": 5,
            }
            resp2 = await client.get(url2, params=params2)
            print(f"[eccc] method2 status: {resp2.status_code}")
        except Exception as e:
            print(f"[eccc] method2 error: {e}")

        # Method 3: MSC GeoMet WMS GetFeatureInfo style
        try:
            url3 = "https://api.weather.gc.ca/collections/weather:current-conditions/items"
            params3 = {
                "bbox":  f"{lon-0.3},{lat-0.3},{lon+0.3},{lat+0.3}",
                "f":     "json",
                "limit": 10,
            }
            resp3 = await client.get(url3, params=params3)
            print(f"[eccc] method3 status: {resp3.status_code}")
            if resp3.status_code == 200:
                features3 = resp3.json().get("features", [])
                if features3:
                    days3 = parse_eccc_features(features3)
                    if days3:
                        return days3
        except Exception as e:
            print(f"[eccc] method3 error: {e}")

        return []


def parse_eccc_features(features: list) -> list:
    tomorrow  = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    targets   = [tomorrow, day_after]
    days, seen = [], []

    for feature in features:
        props    = feature.get("properties", {})
        date_str = (props.get("forecast_period_utc") or
                    props.get("datetime") or
                    props.get("date") or "")[:10]
        if date_str in targets and date_str not in seen:
            seen.append(date_str)
            snow_cm  = float(props.get("total_snow_cm", 0) or 0)
            temp_c   = float(props.get("air_temperature_max", 0) or
                             props.get("air_temperature", 0) or 0)
            wind_kmh = float(props.get("wind_speed_kmh", 0) or 0)
            condition = str(props.get("weather_condition", "") or
                           props.get("weather", "") or "")
            days.append({
                "date":              date_str,
                "temperature_c":     round(temp_c, 1),
                "temperature_f":     round(temp_c * 9 / 5 + 32, 1),
                "wind_speed":        f"{wind_kmh} km/h",
                "snow_cm":           snow_cm,
                "snow_inches":       round(snow_cm / 2.54, 1),
                "precip_chance":     float(props.get("precipitation_probability", 0) or 0),
                "short_forecast":    condition,
                "detailed_forecast": props.get("forecast_text", condition),
                "is_daytime":        True,
                "conditions":        extract_conditions(condition.lower()),
            })
        if len(days) == 2:
            break

    return days


# ═════════════════════════════════════════════════════════════════════════════
# 🌍 SHARED FALLBACK — Open-Meteo
# ═════════════════════════════════════════════════════════════════════════════
async def open_meteo(lat: float, lon: float) -> list:
    """FALLBACK — Open-Meteo, free, no key, US + Canada"""
    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
        try:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude":   lat, "longitude": lon,
                    "daily": ["temperature_2m_max","snowfall_sum",
                              "windspeed_10m_max","precipitation_probability_max","weathercode"],
                    "forecast_days": 3, "timezone": "auto",
                    "temperature_unit": "celsius",
                    "windspeed_unit": "mph",
                    "precipitation_unit": "inch",
                }
            )
            if resp.status_code != 200:
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
                txt      = get_forecast_text(wcode)
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
                    "conditions":        get_conditions_from_wmo(wcode),
                })
            return days
        except Exception as e:
            print(f"[open_meteo] error: {e}")
            return []


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════
def extract_precip_chance(text: str) -> int:
    match = re.search(r'(\d+)\s*percent', text)
    return int(match.group(1)) if match else 0

def extract_conditions(text: str) -> list:
    c = []
    if "snow"  in text or "blizzard" in text: c.append("snow")
    if "ice"   in text or "freezing" in text: c.append("ice")
    if "wind"  in text or "gale"     in text: c.append("wind")
    if "rain"  in text or "drizzle"  in text: c.append("rain")
    return c

def get_conditions_from_wmo(code: int) -> list:
    c = []
    if code in range(71,78) or code in [85,86]:       c.append("snow")
    if code in [56,57,66,67]:                          c.append("ice")
    if code in range(95,100):                          c.append("wind")
    if code in range(51,68) or code in range(80,83):   c.append("rain")
    return c

def get_forecast_text(code: int) -> str:
    wmo = {
        0:"Clear sky", 1:"Mainly clear", 2:"Partly cloudy", 3:"Overcast",
        45:"Foggy", 48:"Icy fog",
        51:"Light drizzle", 53:"Drizzle", 55:"Heavy drizzle",
        61:"Slight rain", 63:"Moderate rain", 65:"Heavy rain",
        71:"Slight snow", 73:"Moderate snow", 75:"Heavy snow", 77:"Snow grains",
        80:"Rain showers", 81:"Moderate showers", 82:"Violent showers",
        85:"Snow showers", 86:"Heavy snow showers",
        95:"Thunderstorm", 96:"Thunderstorm + hail", 99:"Severe thunderstorm",
    }
    return wmo.get(code, "Mixed conditions")

def empty_weather_day() -> dict:
    return {
        "date":"", "temperature_f":32, "temperature_c":0,
        "wind_speed":"0 mph", "snow_inches":0, "snow_cm":0,
        "precip_chance":0, "short_forecast":"Unknown",
        "detailed_forecast":"", "is_daytime":True, "conditions":[],
    }
