"""
Snow Day Probability Calculator
=================================
Auto Mode  : Real weather data se calculate (Weather.gov / Open-Meteo)
Manual Mode: User-entered storm data se calculate
"""

# ─── School Type Multipliers ─────────────────────────────────────────────────
SCHOOL_TYPE_MULTIPLIERS = {
    "public":       1.0,
    "urban_public": 0.85,
    "rural_public": 1.25,
    "private":      0.80,
    "boarding":     0.60,
}

# ─── Snow Day Budget ──────────────────────────────────────────────────────────
SNOW_DAY_BUDGET_FACTOR = {
    0: 1.0, 1: 1.0, 2: 0.95, 3: 0.90, 4: 0.80, 5: 0.70,
}

# ─── Storm Type Base Scores ───────────────────────────────────────────────────
STORM_TYPE_SCORES = {
    "none":           0,
    "flurries":      15,
    "snow_showers":  35,
    "wintry_mix":    45,
    "snow":          55,
    "freezing_rain": 70,
    "heavy_snow":    85,
}

# ─── Leniency Multipliers ─────────────────────────────────────────────────────
LENIENCY_MULTIPLIERS = {
    "easy":  1.25,
    "okay":  1.0,
    "harsh": 0.75,
}

# ─── Day of Week Bonus ────────────────────────────────────────────────────────
# Friday/Monday closures are more common
DAY_BONUS = {
    "monday":    5,
    "tuesday":   0,
    "wednesday": 0,
    "thursday":  0,
    "friday":    8,
    "saturday":  0,
    "sunday":    0,
}


# ═════════════════════════════════════════════════════════════════════════════
# AUTO MODE — Real weather data
# ═════════════════════════════════════════════════════════════════════════════
def calculate_snow_day(weather: dict, snow_days_this_year: int, school_type: str, country: str) -> dict:
    if not weather or not weather.get("date"):
        return empty_result()

    if country == "US":
        snow_amount = weather.get("snow_inches", 0)
        temp        = weather.get("temperature_f", 32)
        snow_score  = _snow_score_us(snow_amount)
        temp_score  = _temp_score_us(temp)
    else:
        snow_amount = weather.get("snow_cm", 0)
        temp        = weather.get("temperature_c", 0)
        snow_score  = _snow_score_ca(snow_amount)
        temp_score  = _temp_score_ca(temp)

    wind_score  = _wind_score(weather.get("wind_speed", "0"))
    conditions  = weather.get("conditions", [])
    ice_score   = 20 if "ice" in conditions else 0
    base_prob   = snow_score + temp_score + wind_score + ice_score

    precip_chance = weather.get("precip_chance", 100)
    if precip_chance < 50:
        base_prob *= (precip_chance / 100)

    school_mult  = SCHOOL_TYPE_MULTIPLIERS.get(school_type, 1.0)
    base_prob   *= school_mult

    budget_key   = min(snow_days_this_year, 5)
    base_prob   *= SNOW_DAY_BUDGET_FACTOR.get(budget_key, 0.65)

    probability = max(0, min(100, round(base_prob)))

    return {
        "date":         weather.get("date", ""),
        "probability":  probability,
        "label":        get_label(probability),
        "emoji":        get_emoji(probability),
        "snow_amount":  snow_amount,
        "temperature":  temp,
        "unit_snow":    "inches" if country == "US" else "cm",
        "unit_temp":    "°F" if country == "US" else "°C",
        "short_forecast": weather.get("short_forecast", ""),
        "breakdown": {
            "snow_score":       round(snow_score),
            "temp_score":       round(temp_score),
            "wind_score":       round(wind_score),
            "ice_bonus":        ice_score,
            "school_type":      school_type,
            "school_multiplier": school_mult,
        }
    }


# ═════════════════════════════════════════════════════════════════════════════
# MANUAL MODE — User entered storm data
# ═════════════════════════════════════════════════════════════════════════════
def calculate_manual_snow_day(
    storm_type: str,          # none/flurries/snow_showers/wintry_mix/snow/freezing_rain/heavy_snow
    storm_chance: int,        # 0-100 %
    start_period: str,        # am_day_before/pm_day_before/am_day/pm_day
    end_period: str,          # pm_day_before/am_day/pm_day/am_day_after
    temp_f: float,            # temperature at 7am in °F
    day_of_week: str,         # monday/tuesday/.../sunday
    school_type: str,
    snow_days_this_year: int,
    leniency: str,            # easy/okay/harsh
    mountainous: bool,
    special_event: bool,
    hype: int,                # 0-3
    country: str,
) -> dict:
    """
    Manual storm data se snow day probability calculate karo.
    Smart weighted formula — better than competitor's simple lookup.
    """

    # 1. Storm type base score
    storm_key  = storm_type.lower().replace(" ", "_").replace("/", "_")
    base_score = STORM_TYPE_SCORES.get(storm_key, 0)

    # 2. Storm timing — overnight storms close more schools
    timing_score = _timing_score(start_period, end_period)

    # 3. Temperature at 7am
    temp_score = _temp_score_us(temp_f)

    # 4. Storm chance factor (0-100%)
    chance_factor = storm_chance / 100

    # 5. Day of week bonus
    day_bonus = DAY_BONUS.get(day_of_week.lower(), 0)

    # 6. Combine base scores
    raw_score = (base_score + timing_score + temp_score + day_bonus) * chance_factor

    # 7. School type multiplier
    school_mult = SCHOOL_TYPE_MULTIPLIERS.get(school_type, 1.0)
    raw_score  *= school_mult

    # 8. Snow day budget
    budget_key  = min(snow_days_this_year, 5)
    raw_score  *= SNOW_DAY_BUDGET_FACTOR.get(budget_key, 0.65)

    # 9. Leniency multiplier
    leniency_mult = LENIENCY_MULTIPLIERS.get(leniency.lower(), 1.0)
    raw_score    *= leniency_mult

    # 10. Mountainous area bonus (+12%)
    if mountainous:
        raw_score *= 1.12

    # 11. Special event penalty (-10%) — schools avoid closing on important days
    if special_event:
        raw_score *= 0.90

    # 12. Hype factor — slight social pressure modifier (0-3 scale, max +6%)
    hype_bonus  = min(hype, 3) * 2
    raw_score  += hype_bonus

    probability = max(0, min(100, round(raw_score)))

    # Convert temp for display
    temp_c = round((temp_f - 32) * 5 / 9, 1)

    return {
        "date":        "",
        "probability": probability,
        "label":       get_label(probability),
        "emoji":       get_emoji(probability),
        "snow_amount": 0,
        "temperature": temp_f,
        "unit_snow":   "inches" if country == "US" else "cm",
        "unit_temp":   "°F",
        "short_forecast": storm_type.replace("_", " ").title(),
        "mode":        "manual",
        "breakdown": {
            "storm_type":     storm_type,
            "storm_score":    round(base_score),
            "timing_score":   round(timing_score),
            "temp_score":     round(temp_score),
            "day_bonus":      day_bonus,
            "chance_factor":  storm_chance,
            "leniency":       leniency,
            "mountainous":    mountainous,
            "special_event":  special_event,
            "hype":           hype,
            "school_type":    school_type,
        }
    }


def _timing_score(start_period: str, end_period: str) -> float:
    """
    Storm timing score — overnight storms are most impactful.
    Best case: starts PM day before, ends AM the day = roads untreated overnight
    Worst case: starts/ends AM the day = crews have time to respond
    """
    timing_map = {
        # (start, end) → score
        ("pm_day_before", "am_day"):     30,  # Perfect overnight — highest impact
        ("pm_day_before", "pm_day"):     25,  # Overnight + morning
        ("pm_day_before", "am_day_after"): 20, # Long storm, started night before
        ("am_day_before", "am_day"):     22,  # Full day before + overnight
        ("am_day_before", "pm_day"):     18,
        ("am_day",        "pm_day"):     10,  # Morning storm — crews respond
        ("am_day",        "am_day_after"): 15,
        ("pm_day",        "am_day_after"): 8,  # Afternoon/evening — next day clear
    }
    key = (start_period.lower(), end_period.lower())
    return timing_map.get(key, 10)


# ═════════════════════════════════════════════════════════════════════════════
# SHARED SCORING FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════
def _snow_score_us(inches: float) -> float:
    if inches == 0:   return 0
    if inches < 1:    return 10
    if inches < 2:    return 25
    if inches < 4:    return 45
    if inches < 6:    return 65
    if inches < 8:    return 80
    if inches < 12:   return 90
    return 95

def _snow_score_ca(cm: float) -> float:
    if cm == 0:       return 0
    if cm < 2:        return 10
    if cm < 5:        return 25
    if cm < 10:       return 45
    if cm < 15:       return 65
    if cm < 20:       return 80
    if cm < 30:       return 90
    return 95

def _temp_score_us(temp_f: float) -> float:
    if temp_f > 35:   return 0
    if temp_f > 32:   return 5
    if temp_f > 28:   return 10
    if temp_f > 20:   return 15
    if temp_f > 10:   return 20
    return 25

def _temp_score_ca(temp_c: float) -> float:
    if temp_c > 2:    return 0
    if temp_c > 0:    return 5
    if temp_c > -5:   return 10
    if temp_c > -10:  return 15
    if temp_c > -20:  return 20
    return 25

def _wind_score(wind_str) -> float:
    try:
        speed = float(str(wind_str).split()[0])
        if "km" in str(wind_str):
            speed *= 0.621
        if speed < 15:  return 0
        if speed < 25:  return 5
        if speed < 35:  return 10
        if speed < 45:  return 15
        return 20
    except:
        return 0

def get_label(probability: int) -> str:
    if probability >= 90: return "Almost Certain Snow Day! ❄️"
    if probability >= 75: return "Very Likely Snow Day"
    if probability >= 60: return "Likely Snow Day"
    if probability >= 40: return "Possible Snow Day"
    if probability >= 20: return "Unlikely Snow Day"
    return "No Snow Day Expected"

def get_emoji(probability: int) -> str:
    if probability >= 75: return "🌨️"
    if probability >= 50: return "❄️"
    if probability >= 25: return "🌥️"
    return "☀️"

def empty_result() -> dict:
    return {
        "date": "", "probability": 0,
        "label": "No data available", "emoji": "❓",
        "snow_amount": 0, "temperature": 0,
        "unit_snow": "inches", "unit_temp": "°F",
        "short_forecast": "", "breakdown": {}
    }
