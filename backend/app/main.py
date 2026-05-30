import os
import time
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.data.destinations import DESTINATIONS
from app.services.weather_service import get_weather
from app.services.news_service import get_news
from app.services.advisory_service import get_advisory
from app.data.travelscore import calculate_travelscore


load_dotenv()

##debug
print("OpenWeather key loaded:", os.getenv("OPENWEATHER_API_KEY") is not None)
print("News key loaded:", os.getenv("WORLD_NEWS_API_KEY") is not None)

app = FastAPI()

allowed_origins = [
    "http://localhost:5173",
    "https://travelbuddiez.vercel.app",
]
allowed_origins = [
    "http://localhost:5173",
    "https://travelbuddiez.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEST_COUNTRY_CODES = [
    #"SGP",
    "IDN",
    #"JPN",
]

@app.get("/")
def root():
    return {"message": "TravelBuddiez backend is running"}

@app.get("/destinations")
def get_all_destinations():
    all_destinations = []

    for country_code in TEST_COUNTRY_CODES:

        destination = DESTINATIONS.get(country_code)
        if destination is None:
            continue

        weather = get_weather(destination["city"])
        news = get_news(destination["newsCode"], destination["country"])
        advisory = get_advisory(country_code)
        score_data = calculate_travelscore(weather, news, advisory)

        all_destinations.append({
            "countryCode": destination["countryCode"],
            "country": destination["country"],
            "city": destination["city"],
            "travelScore": score_data["travelScore"],
            "riskLevel": score_data["riskLevel"],
            "condition": score_data["condition"],
        })

    return all_destinations

@app.get("/destinations/{country_code}")
def get_destination(country_code: str):
    country_code = country_code.upper()

    if country_code not in TEST_COUNTRY_CODES:
        raise HTTPException(status_code=404, detail="Destination not available in test mode")

    destination = DESTINATIONS.get(country_code)

    if destination is None:
        raise HTTPException(status_code=404, detail="Destination not found")

    weather = get_weather(destination["city"])
    news = get_news(destination["newsCode"], destination["country"])
    advisory = get_advisory(country_code)

    score_data = calculate_travelscore(weather, news, advisory)

    #debug
    print("Country:", destination["country"])
    print("News code:", destination.get("newsCode"))
    print("News articles returned:", len(news))


    return {
        "countryCode": destination["countryCode"],
        "country": destination["country"],
        "city": destination["city"],
        "travelScore": score_data["travelScore"],
        "riskLevel": score_data["riskLevel"],
        "condition": score_data["condition"],
        "weather": weather,
        "news": news,
        "advisory": advisory,
    }

