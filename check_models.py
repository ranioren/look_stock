import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

with open("models.txt", "w") as f:
    if not api_key:
        f.write("No API key found")
    else:
        genai.configure(api_key=api_key)
        try:
            f.write("Listing available models:\n")
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    f.write(f"{m.name}\n")
        except Exception as e:
            f.write(f"Error listing models: {e}")
