from flask import Blueprint, request, jsonify
import google.generativeai as genai
import os

ai_bp = Blueprint('ai_bp', __name__)

# Configure API Key (Lazy loading to avoid error if env not set immediately)
def get_model():
    api_key = "AIzaSyCbEqsNnHi3GvYvJZpzXu4j3OnXdX15AK8"
    print(f"🔑 DEBUG: Checking API Key...")
    if not api_key:
        print("❌ DEBUG: API Key is None")
        return None
    
    if "SIZNING" in api_key:
        print("⚠️ DEBUG: API Key appears to be the default placeholder!")
    else:
        print(f"✅ DEBUG: API Key found (Length: {len(api_key)})")
    
    genai.configure(api_key=api_key)
    
    SYSTEM_PROMPT = """
    You are Niners AI.

    Rules:
    - You only help with LANGUAGE LEARNING.
    - Languages supported: Uzbek, Russian, English.
    - You must introduce yourself as "Niners AI" if asked.
    - You NEVER do homework fully for the student.
    - You can give hints, explanations, examples, or corrections.
    - If user asks to "do homework", politely refuse and explain instead.
    - Do not judge the user.
    - Do not say things like "you are lazy" or "you are bad".
    - Keep answers clear and educational.
    - If the user speaks Uzbek, answer in Uzbek. If Russian, in Russian.
    """
    
    return genai.GenerativeModel(
        model_name="gemini-flash-latest",
        system_instruction=SYSTEM_PROMPT
    )

@ai_bp.route("/chat", methods=["POST"])
def ai_chat():
    model = get_model()
    if not model:
        return jsonify({"error": "Server: AI API Key not configured"}), 500

    data = request.json
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    try:
        response = model.generate_content(user_message)
        return jsonify({
            "assistant": "Niners AI",
            "response": response.text
        })
    except Exception as e:
        print(f"❌ AI CHAT ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"AI Error: {str(e)}"}), 500

@ai_bp.route("/info", methods=["GET"])
def ai_info():
    return jsonify({
        "name": "Niners AI",
        "description": "Language learning assistant (UZ / RU / EN)",
        "status": "active" if os.getenv("GEMINI_API_KEY") else "inactive"
    })
