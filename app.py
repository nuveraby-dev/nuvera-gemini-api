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
        
        # ШАГ 1: Получаем список всех моделей, доступных вашему ключу
        # Это исключит ошибку 404, так как мы будем использовать только то, что есть в списке
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # ШАГ 2: Ищем лучшую модель из доступных
        # Приоритет: 1.5-flash -> 1.5-flash-latest -> любая первая в списке
        target_model = 'models/gemini-1.5-flash'
        
        if target_model not in available_models:
            if 'models/gemini-1.5-flash-latest' in available_models:
                target_model = 'models/gemini-1.5-flash-latest'
            elif available_models:
                target_model = available_models[0]
            else:
                return jsonify({"response": "У вашего ключа нет доступных моделей ИИ."}), 200

        # Инициализируем выбранную модель
        model = genai.GenerativeModel(target_model)
        
        data = request.get_json()
        user_msg = data.get('message', '')

        # Сжимаем прайс для экономии лимитов
        raw_price = get_price_json_string()
        compact_price = re.sub(r'\s+', ' ', raw_price)

        prompt = (
            f"Ты технолог Nuvera. Прайс: {compact_price}. "
            f"Ответь кратко и вежливо. Без знаков * и #. "
            f"Вопрос: {user_msg}"
        )

        response = model.generate_content(prompt)
        
        # Очистка ответа от лишних символов
        clean_text = response.text.replace('*', '').replace('#', '').strip()
        
        return jsonify({
            "response": clean_text, 
            "status": "ok",
            "active_model": target_model  # добавил для отладки, увидим какая модель сработала
        })

    except Exception as e:
        error_str = str(e)
        if "429" in error_str:
            return jsonify({"response": "Много запросов. Подождите 60 сек."}), 200
        return jsonify({"response": f"Ошибка: {error_str}"}), 200

@app.route('/')
def index():
    return "API Nuvera (Smart Mode) Active", 200
