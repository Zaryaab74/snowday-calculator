"""
Snow Day Probability Calculator

Factors jo consider hote hain:
1. Snowfall amount
2. Temperature
3. Wind speed
4. School type (rural schools zyada close hote hain)
5. Snow days already used this year
6. Ice/freezing rain conditions
"""


# School type multipliers — rural schools zyada sensitive hain
SCHOOL_TYPE_MULTIPLIERS = {
    "public": 1.0,
    "urban_public": 0.85,   # Cities mein plowing better hoti hai
    "rural_public": 1.25,   # Rural mein roads clear hone mein waqt lagta hai
    "private": 0.80,        # Private schools kam close hote hain
    "boarding": 0.60,       # Boarding schools almost kabhi nahi closey
}

# Snow days already used — agar zyada use ho gaye toh district reluctant hota hai
SNOW_DAY_BUDGET_FACTOR = {
    0: 1.0,
    1: 1.0,
    2: 0.95,
    3: 0.90,
    4: 0.80,
    5: 0.70,
}


def calculate_snow_day(weather: dict, snow_days_this_year: int, school_type: str, country: str) -> dict:
    """
    Weather data se snow day probability calculate karo
    Returns: probability (0-100), label, breakdown
    """
    if not weather or not weather.get("date"):
        return empty_result()

    # Country ke hisaab se units
    if country == "US":
        snow_amount = weather.get("snow_inches", 0)
        temp = weather.get("temperature_f", 32)
        snow_score = calculate_snow_score_us(snow_amount)
        temp_score = calculate_temp_score_us(temp)
    else:
        snow_amount = weather.get("snow_cm", 0)
        temp = weather.get("temperature_c", 0)
        snow_score = calculate_snow_score_ca(snow_amount)
        temp_score = calculate_temp_score_ca(temp)

    # Wind score
    wind_score = calculate_wind_score(weather.get("wind_speed", "0"))

    # Ice/freezing rain bonus
    conditions = weather.get("conditions", [])
    ice_score = 20 if "ice" in conditions else 0

    # Base probability
    base_prob = snow_score + temp_score + wind_score + ice_score

    # Precip chance bhi factor karo
    precip_chance = weather.get("precip_chance", 100)
    if precip_chance < 50:
        base_prob *= (precip_chance / 100)

    # School type multiplier
    school_mult = SCHOOL_TYPE_MULTIPLIERS.get(school_type, 1.0)
    base_prob *= school_mult

    # Snow day budget factor
    budget_key = min(snow_days_this_year, 5)
    budget_factor = SNOW_DAY_BUDGET_FACTOR.get(budget_key, 0.65)
    base_prob *= budget_factor

    # 0-100 ke beech rakhna
    probability = max(0, min(100, round(base_prob)))

    return {
        "date": weather.get("date", ""),
        "probability": probability,
        "label": get_label(probability),
        "emoji": get_emoji(probability),
        "snow_amount": snow_amount,
        "temperature": temp,
        "unit_snow": "inches" if country == "US" else "cm",
        "unit_temp": "°F" if country == "US" else "°C",
        "short_forecast": weather.get("short_forecast", ""),
        "breakdown": {
            "snow_score": round(snow_score),
            "temp_score": round(temp_score),
            "wind_score": round(wind_score),
            "ice_bonus": ice_score,
            "school_type": school_type,
            "school_multiplier": school_mult,
        }
    }


def calculate_snow_score_us(inches: float) -> float:
    """US: inches of snow → score"""
    if inches == 0:     return 0
    if inches < 1:      return 10
    if inches < 2:      return 25
    if inches < 4:      return 45
    if inches < 6:      return 65
    if inches < 8:      return 80
    if inches < 12:     return 90
    return 95


def calculate_snow_score_ca(cm: float) -> float:
    """Canada: cm of snow → score"""
    if cm == 0:         return 0
    if cm < 2:          return 10
    if cm < 5:          return 25
    if cm < 10:         return 45
    if cm < 15:         return 65
    if cm < 20:         return 80
    if cm < 30:         return 90
    return 95


def calculate_temp_score_us(temp_f: float) -> float:
    """Temperature jitni kam, utna zyada chance"""
    if temp_f > 35:     return 0
    if temp_f > 32:     return 5
    if temp_f > 28:     return 10
    if temp_f > 20:     return 15
    if temp_f > 10:     return 20
    return 25


def calculate_temp_score_ca(temp_c: float) -> float:
    if temp_c > 2:      return 0
    if temp_c > 0:      return 5
    if temp_c > -5:     return 10
    if temp_c > -10:    return 15
    if temp_c > -20:    return 20
    return 25


def calculate_wind_score(wind_str) -> float:
    """Wind speed → score (blizzard conditions)"""
    try:
        # "15 mph" ya "25 km/h" se number nikalo
        speed = float(str(wind_str).split()[0])
        if "km" in str(wind_str):
            speed = speed * 0.621  # km/h → mph

        if speed < 15:  return 0
        if speed < 25:  return 5
        if speed < 35:  return 10
        if speed < 45:  return 15
        return 20
    except:
        return 0


def get_label(probability: int) -> str:
    if probability >= 90:   return "Almost Certain Snow Day! ❄️"
    if probability >= 75:   return "Very Likely Snow Day"
    if probability >= 60:   return "Likely Snow Day"
    if probability >= 40:   return "Possible Snow Day"
    if probability >= 20:   return "Unlikely Snow Day"
    return "No Snow Day Expected"


def get_emoji(probability: int) -> str:
    if probability >= 75:   return "🌨️"
    if probability >= 50:   return "❄️"
    if probability >= 25:   return "🌥️"
    return "☀️"


def empty_result() -> dict:
    return {
        "date": "",
        "probability": 0,
        "label": "No data available",
        "emoji": "❓",
        "snow_amount": 0,
        "temperature": 0,
        "unit_snow": "inches",
        "unit_temp": "°F",
        "short_forecast": "",
        "breakdown": {}
    }
