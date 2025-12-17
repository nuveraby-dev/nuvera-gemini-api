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
        return jsonify({"response": "Ошибка: Ключ API не найден в настройках Vercel."}), 200

    try:
        genai.configure(api_key=api_key)
        
        # 1. Пробуем получить список моделей
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        except:
            available_models = []

        # 2. Определяем приоритеты
        priority = ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-latest', 'models/gemini-pro']
        
        target_model = None
        # Ищем совпадение в списке
        for p in priority:
            if p in available_models:
                target_model = p
                break
        
        # 3. Если список пуст, пробуем принудительно самую стабильную версию
        if not target_model:
            target_model = 'gemini-1.5-flash' 

        model = genai.GenerativeModel(target_model)
        
        data = request.get_json()
        user_msg = data.get('message', '')

        compact_price = re.sub(r'\s+', ' ', get_price_json_string())

        prompt = (
            f"Ты технолог Nuvera. Прайс: {compact_price}. "
            f"Ответь кратко и вежливо. Не используй * или #. "
            f"Вопрос: {user_msg}"
        )

        response = model.generate_content(prompt)
        
        # Если ответ пустой
        if not response.text:
             raise Exception("Empty response")

        clean_text = response.text.replace('*', '').replace('#', '').strip()
        
        return jsonify({
            "response": clean_text, 
            "status": "ok",
            "model": target_model
        })

    except Exception as e:
        error_str = str(e)
        if "429" in error_str:
            return jsonify({"response": "Много запросов. Подождите 60 секунд."}), 200
        if "403" in error_str:
            return jsonify({"response": "Ошибка доступа. Проверьте регион в Vercel (нужен USA)."}), 200
        
        # Если ничего не помогло, выводим саму ошибку для диагностики
        return jsonify({"response": f"Ошибка связи с ИИ: {error_str}. Попробуйте позже."}), 200

@app.route('/')
def index():
    return "API Nuvera (Smart Selection) Active", 200
