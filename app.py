from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
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
        
        # Получаем список всех доступных моделей для вашего ключа
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Приоритетный список моделей (от самых стабильных к экспериментальным)
        priority_models = ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-latest', 'models/gemini-pro']
        
        selected_model = None
        for target in priority_models:
            if target in all_models:
                selected_model = target
                break
        
        # Если ничего из списка не подошло, берем первую доступную
        if not selected_model:
            selected_model = all_models[0] if all_models else None

        if not selected_model:
            return jsonify({"response": "Нет доступных моделей ИИ."}), 200

        model = genai.GenerativeModel(selected_model)
        data = request.get_json()
        user_msg = data.get('message', '')

        # Сокращаем промпт, чтобы экономить лимиты (квоты)
        prompt = f"Ты технолог Nuvera. Прайс: {get_price_json_string()}. Ответь кратко на вопрос: {user_msg}"

        response = model.generate_content(prompt)
        
        return jsonify({
            "response": response.text, 
            "status": "ok",
            "model": selected_model
        })

    except Exception as e:
        # Если ошибка 429 (лимит), уведомляем пользователя понятно
        error_msg = str(e)
        if "429" in error_msg:
            return jsonify({"response": "Превышен лимит запросов. Пожалуйста, подождите 1 минуту."}), 200
        return jsonify({"response": f"Ошибка: {error_msg}"}), 200

@app.route('/')
def index():
    return "API Nuvera Smart System Active"
