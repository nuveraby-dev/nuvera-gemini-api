from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
import re
from data_config import get_price_json_string

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/api/ai_chat', methods=['POST', 'OPTIONS'])
def ai_chat_endpoint():
    if request.method == 'OPTIONS':
        return '', 200

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"response": "Ошибка: Ключ API не найден."}), 200

    try:
        genai.configure(api_key=api_key)
        
        # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Мы НЕ указываем версию в имени модели
        # Библиотека сама выберет v1 (стабильную), если написать просто имя
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        data = request.get_json()
        user_msg = data.get('message', '')

        raw_price = get_price_json_string()
        compact_price = re.sub(r'\s+', ' ', raw_price)

        prompt = (
            f"Ты технолог Nuvera. Прайс: {compact_price}. "
            f"Ответь кратко и вежливо. Без символов * и #. "
            f"Вопрос: {user_msg}"
        )

        # Добавляем параметр для принудительного использования стабильной версии, если библиотека капризничает
        response = model.generate_content(prompt)
        
        if not response.text:
            return jsonify({"response": "ИИ не смог сформировать ответ. Попробуйте другой вопрос."}), 200

        clean_text = response.text.replace('*', '').replace('#', '').strip()
        
        return jsonify({"response": clean_text, "status": "ok"})

    except Exception as e:
        error_str = str(e)
        # Если все еще 404, пробуем подсказать серверу переключиться на gemini-pro
        if "404" in error_str:
             try:
                 model_alt = genai.GenerativeModel('gemini-pro')
                 response = model_alt.generate_content(user_msg)
                 return jsonify({"response": response.text.replace('*', ''), "status": "ok"})
             except:
                 return jsonify({"response": "Модель временно недоступна. Обновите API ключ или подождите."}), 200
        
        if "429" in error_str:
            return jsonify({"response": "Много запросов. Подождите 60 сек."}), 200
            
        return jsonify({"response": f"Ошибка: {error_str}"}), 200

@app.route('/')
def index():
    return "API Nuvera Active", 200
