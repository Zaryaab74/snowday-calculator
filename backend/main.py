from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from weather import get_weather_data
from calculator import calculate_snow_day, calculate_manual_snow_day
import uvicorn

app = FastAPI(
    title="Snow Day Calculator API",
    description="Snow day prediction for USA and Canada — Auto + Manual modes",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Auto Mode Request ────────────────────────────────────────────────────────
class PredictionRequest(BaseModel):
    zip_code:            str
    snow_days_this_year: int = 0
    school_type:         str = "public"


# ─── Manual Mode Request ──────────────────────────────────────────────────────
class ManualPredictionRequest(BaseModel):
    storm_type:          str   = "snow"
    storm_chance:        int   = 80
    start_period:        str   = "pm_day_before"
    end_period:          str   = "am_day"
    temp_f:              float = 28.0
    day_of_week:         str   = "monday"
    school_type:         str   = "public"
    snow_days_this_year: int   = 0
    leniency:            str   = "okay"
    mountainous:         bool  = False
    special_event:       bool  = False
    hype:                int   = 0
    country:             str   = "US"


class PredictionResponse(BaseModel):
    zip_code:          Optional[str] = None
    country:           str
    city:              Optional[str] = None
    region:            Optional[str] = None
    probability:       int
    prediction_label:  str
    tomorrow:          dict
    day_after:         dict
    weather_summary:   dict
    mode:              str = "auto"


@app.get("/")
def root():
    return {"message": "Snow Day Calculator API v2.0 — Auto + Manual modes"}


# ─── AUTO MODE ────────────────────────────────────────────────────────────────
@app.post("/predict")
async def predict_snow_day(request: PredictionRequest):
    zip_code = request.zip_code.strip().upper()
    country  = detect_country(zip_code)
    weather  = await get_weather_data(zip_code, country)

    if not weather:
        raise HTTPException(status_code=404, detail="Location not found. Check ZIP/Postal code.")

    tomorrow  = calculate_snow_day(weather["tomorrow"],  request.snow_days_this_year, request.school_type, country)
    day_after = calculate_snow_day(weather["day_after"], request.snow_days_this_year, request.school_type, country)

    return {
        "zip_code":         zip_code,
        "country":          country,
        "city":             weather["city"],
        "region":           weather["region"],
        "probability":      tomorrow["probability"],
        "prediction_label": tomorrow["label"],
        "tomorrow":         tomorrow,
        "day_after":        day_after,
        "weather_summary":  weather["tomorrow"],
        "mode":             "auto",
    }


# ─── MANUAL MODE ──────────────────────────────────────────────────────────────
@app.post("/predict/manual")
async def predict_manual(request: ManualPredictionRequest):
    """
    Manual storm data se snow day probability calculate karo.
    No ZIP code needed — user enters storm conditions directly.
    """
    result = calculate_manual_snow_day(
        storm_type          = request.storm_type,
        storm_chance        = request.storm_chance,
        start_period        = request.start_period,
        end_period          = request.end_period,
        temp_f              = request.temp_f,
        day_of_week         = request.day_of_week,
        school_type         = request.school_type,
        snow_days_this_year = request.snow_days_this_year,
        leniency            = request.leniency,
        mountainous         = request.mountainous,
        special_event       = request.special_event,
        hype                = request.hype,
        country             = request.country,
    )

    # Manual mode mein dono days same result (no date-specific forecast)
    return {
        "zip_code":         None,
        "country":          request.country,
        "city":             None,
        "region":           None,
        "probability":      result["probability"],
        "prediction_label": result["label"],
        "tomorrow":         result,
        "day_after":        result,
        "weather_summary":  {},
        "mode":             "manual",
    }


def detect_country(zip_code: str) -> str:
    cleaned = zip_code.replace(" ", "")
    if cleaned.isdigit() and len(cleaned) == 5:
        return "US"
    if len(cleaned) == 6 and cleaned[0].isalpha():
        return "CA"
    raise HTTPException(
        status_code=400,
        detail="Invalid ZIP/Postal code. Use US format (12345) or Canadian format (A1A1A1)"
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
