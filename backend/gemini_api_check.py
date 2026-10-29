import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Check your .env file."
    )

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=(
            "You are testing the AI Receptionist Agent. "
            "Reply with one short sentence confirming "
            "that you are ready to help users book appointments."
        ),
    )

    print("Gemini response:")
    print(response.text)

finally:
    client.close()