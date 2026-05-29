import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.data.destinations import DESTINATIONS
from app.services.weather_service import get_weather
from app.services.news_service import get_news
from app.services.advisory_service import get_advisory


load_dotenv()
##debug
print("OpenWeather key loaded:", os.getenv("OPENWEATHER_API_KEY") is not None)
print("News key loaded:", os.getenv("NEWS_API_KEY") is not None)

app = FastAPI()

allowed_origins = [
    "http://localhost:5173",
    "https://travelbuddiez.vercel.app/",
]

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "TravelBuddiez backend is running"}


@app.get("/destinations/{country_code}")
def get_destination(country_code: str):
    country_code = country_code.upper()

    destination = DESTINATIONS.get(country_code)

    if destination is None:
        raise HTTPException(status_code=404, detail="Destination not found")

    weather = get_weather(destination["city"])
    news = get_news(destination["country"])
    advisory = get_advisory(country_code)

    return {
        "countryCode": destination["countryCode"],
        "country": destination["country"],
        "travelScore": destination["travelScore"],
        "riskLevel": destination["riskLevel"],
        "condition": destination["condition"],
        "weather": weather,
        "news": news,
        "advisory": advisory,
    }