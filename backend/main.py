from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from weather import get_weather_data
from calculator import calculate_snow_day
import uvicorn

app = FastAPI(
    title="Snow Day Calculator API",
    description="Snow day prediction for USA and Canada",
    version="1.0.0"
)

# CORS — React frontend ko allow karo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production mein apna domain daalna
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictionRequest(BaseModel):
    zip_code: str           # US ZIP or Canadian Postal Code
    snow_days_this_year: int = 0
    school_type: str = "public"  # public, urban_public, rural_public, private, boarding


class PredictionResponse(BaseModel):
    zip_code: str
    country: str
    city: str
    region: str
    probability: int        # 0-100
    prediction_label: str   # "Very Likely", "Likely", etc.
    tomorrow: dict
    day_after: dict
    weather_summary: dict


@app.get("/")
def root():
    return {"message": "Snow Day Calculator API is running!"}


@app.post("/predict", response_model=PredictionResponse)
async def predict_snow_day(request: PredictionRequest):
    """
    ZIP/Postal Code se snow day probability calculate karo
    """
    zip_code = request.zip_code.strip().upper()

    # Country detect karo
    country = detect_country(zip_code)

    # Weather data fetch karo
    weather = await get_weather_data(zip_code, country)
    if not weather:
        raise HTTPException(status_code=404, detail="Location not found. Check ZIP/Postal code.")

    # Snow day calculate karo
    tomorrow = calculate_snow_day(
        weather["tomorrow"],
        request.snow_days_this_year,
        request.school_type,
        country
    )
    day_after = calculate_snow_day(
        weather["day_after"],
        request.snow_days_this_year,
        request.school_type,
        country
    )

    return PredictionResponse(
        zip_code=zip_code,
        country=country,
        city=weather["city"],
        region=weather["region"],
        probability=tomorrow["probability"],
        prediction_label=tomorrow["label"],
        tomorrow=tomorrow,
        day_after=day_after,
        weather_summary=weather["tomorrow"]
    )


def detect_country(zip_code: str) -> str:
    """
    ZIP code format se country detect karo
    US: 5 digits (e.g. 10001)
    Canada: A1A 1A1 format
    """
    cleaned = zip_code.replace(" ", "")
    if cleaned.isdigit() and len(cleaned) == 5:
        return "US"
    # Canadian postal code: Letter-Digit-Letter-Digit-Letter-Digit
    if len(cleaned) == 6 and cleaned[0].isalpha():
        return "CA"
    raise HTTPException(
        status_code=400,
        detail="Invalid ZIP/Postal code. Use US format (12345) or Canadian format (A1A1A1)"
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
