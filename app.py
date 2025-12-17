from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
import re
from data_config import get_price_json_string

app = Flask(__name__)
# Полный доступ для Tilda
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/api/ai_chat', methods=['POST', 'OPTIONS'])
def ai_chat_endpoint():
    if request.method == 'OPTIONS':
        return '', 200

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"response": "Ошибка: Добавьте GEMINI_API_KEY в Vercel"}), 200

    try:
        # Настройка модели
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        data = request.get_json()
        user_msg = data.get('message', '')

        # Получаем и максимально сжимаем прайс (удаляем лишние пробелы)
        compact_price = re.sub(r'\s+', ' ', get_price_json_string())

        # Системный промпт: строгие правила для ИИ
        prompt = (
            f"Ты — эксперт-технолог типографии Nuvera. Твой прайс в JSON: {compact_price}. "
            f"Правила: 1. Отвечай очень кратко и вежливо. "
            f"2. Используй только данные из прайса. "
            f"3. Если услуги нет в списке, вежливо отправь к менеджеру. "
            f"4. НЕ используй символы * или # в ответе. "
            f"Вопрос клиента: {user_msg}"
        )

        # Генерация ответа
        response = model.generate_content(prompt)
        clean_response = response.text.replace('*', '').replace('#', '').strip()
        
        return jsonify({
            "response": clean_response, 
            "status": "ok"
        })

    except Exception as e:
        error_msg = str(e)
        # Обработка лимита 429
        if "429" in error_msg:
            return jsonify({"response": "Превышен лимит запросов. Подождите 60 сек."}), 200
        return jsonify({"response": f"Системная ошибка: {error_msg}"}), 200

@app.route('/')
def index():
    return "Nuvera AI API: Online", 200
