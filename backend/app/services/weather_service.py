import os
import requests


def get_weather(city: str) -> str:
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if api_key is None:
        return "Weather API key is missing."

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        return "Weather information is currently unavailable."

    data = response.json()

    description = data["weather"][0]["description"]
    temperature = data["main"]["temp"]

    return f"{description.capitalize()}, around {temperature}°C."