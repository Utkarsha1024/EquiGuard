import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

models_to_test = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-3-flash-preview",
    "gemma-3-4b-it",
]

for m in models_to_test:
    try:
        print(f"\nTesting {m}...")
        response = client.models.generate_content(
            model=m,
            contents='say hi'
        )
        print(f"Success! {response.text}")
    except Exception as e:
        print(f"{m} failed: {e}")

