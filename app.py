from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
from data_config import get_price_json_string

app = Flask(__name__)
# Разрешаем CORS для всех доменов и методов
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/api/ai_chat', methods=['POST', 'OPTIONS'])
def ai_chat_endpoint():
    # Исправляем CORS preflight (ошибка на твоих скриншотах)
    if request.method == 'OPTIONS':
        return '', 200

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"response": "Ошибка: Ключ API не найден в Vercel."}), 200

    try:
        genai.configure(api_key=api_key)
        
        # Убираем префиксы, оставляем только чистое имя модели
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        data = request.get_json()
        user_msg = data.get('message', '')

        prompt = (
            f"Ты технолог типографии Nuvera. Твой прайс: {get_price_json_string()}\n"
            f"Отвечай кратко и вежливо. Вопрос клиента: {user_msg}"
        )

        response = model.generate_content(prompt)
        
        return jsonify({
            "response": response.text, 
            "status": "ok"
        })

    except Exception as e:
        # Если будет ошибка 404 или 429, мы увидим точное описание
        return jsonify({"response": f"Ошибка Gemini: {str(e)}"}), 200

@app.route('/')
def index():
    return "API Nuvera Active (Region: CLE1)"
