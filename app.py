from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
from data_config import get_price_json_string

app = Flask(__name__)

# Настройка CORS: разрешаем всё, чтобы убрать ошибку в консоли
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/api/ai_chat', methods=['POST', 'OPTIONS'])
def ai_chat_endpoint():
    # Обработка preflight запроса (те самые ошибки на скриншоте)
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"response": "Ошибка: Ключ API не найден."}), 200

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        data = request.get_json()
        user_msg = data.get('message', '')

        prompt = (
            f"Ты технолог Nuvera. Твой прайс: {get_price_json_string()}\n"
            f"Отвечай кратко. Вопрос: {user_msg}"
        )

        response = model.generate_content(prompt)
        
        return jsonify({
            "response": response.text, 
            "status": "ok"
        })

    except Exception as e:
        return jsonify({"response": f"Ошибка Gemini: {str(e)}"}), 200

@app.route('/')
def index():
    return "API Nuvera Active"
