from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai
from data_config import get_price_json_string

app = Flask(__name__)
CORS(app)

@app.route('/api/ai_chat', methods=['POST'])
def ai_chat_endpoint():
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        return jsonify({"response": "Ошибка конфигурации: Ключ API не найден."}), 200

    try:
        client = genai.Client(api_key=api_key)
        data = request.get_json()
        user_msg = data.get('message', 'Привет')

        # Добавляем ПРАЙС и системную роль в запрос
        full_context = f"Ты технолог Nuvera. Прайс: {get_price_json_string()}. Отвечай кратко."
        
        # ВАЖНОЕ ИЗМЕНЕНИЕ: используем полное имя 'models/gemini-1.5-flash'
        response = client.models.generate_content(
            model='models/gemini-1.5-flash',
            contents=f"{full_context}\n\nВопрос пользователя: {user_msg}"
        )
        
        return jsonify({"response": response.text, "status": "ok"})
        
    except Exception as e:
        # Теперь ошибка будет выводиться более детально
        return jsonify({"response": f"Ошибка Gemini: {str(e)}"}), 200

@app.route('/')
def index():
    return "API Nuvera Active"
