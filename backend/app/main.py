import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.routes.root import router as root_router
from app.routes.destination_routes import router as destinations_router

from app.routes.auth_routes import router as auth_router

# Travel planning routes for flight and hotel search.
from app.routes.travel_routes import router as travel_router

# ai chatbot route
from app.routes.ai_assistant import router as assistant_router

load_dotenv()

##debug
#print("OpenWeather key loaded:", os.getenv("OPENWEATHER_API_KEY") is not None)
#print("News key loaded:", os.getenv("WORLD_NEWS_API_KEY") is not None)
print("Database URL loaded:", os.getenv("DATABASE_URL") is not None)

app = FastAPI()

allowed_origins = [
    "http://localhost:5173",
    "https://travelbuddiez.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root_router)
app.include_router(destinations_router)
app.include_router(auth_router)
app.include_router(travel_router)
app.include_router(assistant_router)