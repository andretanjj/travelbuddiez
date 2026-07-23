import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from the .env file.")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model=model_name,
        contents=(
            "You are a travel assistant. "
            "Reply with one sentence explaining why Japan is popular."
        ),
    )

    print("Gemini response:")
    print(response.text)

except Exception as error:
    print(f"Gemini request failed: {error}")