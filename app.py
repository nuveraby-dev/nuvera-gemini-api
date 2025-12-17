from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai

app = Flask(__name__)
CORS(app)

@app.route('/api/ai_chat', methods=['POST'])
def ai_chat_endpoint():
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # ПРОВЕРКА НАЛИЧИЯ КЛЮЧА
    if not api_key:
        return jsonify({"response": "Ошибка конфигурации: Ключ API не найден на сервере Vercel."}), 200

    try:
        client = genai.Client(api_key=api_key)
        data = request.get_json()
        user_msg = data.get('message', 'Привет')

        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=user_msg
        )
        return jsonify({"response": response.text, "status": "ok"})
        
    except Exception as e:
        return jsonify({"response": f"Ошибка Gemini: {str(e)}"}), 200

@app.route('/')
def index():
    return "API Nuvera Active"

