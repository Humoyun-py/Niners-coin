import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ API Key not found in .env")
else:
    print(f"✅ Found API Key: {api_key[:5]}...")
    try:
        genai.configure(api_key=api_key)
        print("Listing available models...")
        with open('backend/available_models.txt', 'w') as f:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    f.write(f"{m.name}\n")
                    print(f"Model: {m.name}")
        print("Done listing models.")
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        with open('backend/available_models.txt', 'w') as f:
            f.write(f"Error: {e}")
