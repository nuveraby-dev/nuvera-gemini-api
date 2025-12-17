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
        return jsonify({"response": "Ошибка: API-ключ не найден в Vercel."}), 200

    try:
        genai.configure(api_key=api_key)
        
        # Автоматический подбор рабочей модели
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Приоритет выбора: сначала flash, если нет - любая доступная
        model_name = 'models/gemini-1.5-flash' # пробуем стандарт
        if model_name not in available_models:
            # Если стандарта нет в списке, берем первую рабочую модель из списка Google
            model_name = available_models[0] if available_models else None

        if not model_name:
            return jsonify({"response": "У вашего ключа нет доступных моделей ИИ."}), 200

        model = genai.GenerativeModel(model_name)
        
        data = request.get_json()
        user_msg = data.get('message', '')

        prompt = (
            f"Ты технолог Nuvera. Прайс: {get_price_json_string()}\n"
            f"Ответь кратко на вопрос: {user_msg}"
        )

        response = model.generate_content(prompt)
        return jsonify({
            "response": response.text, 
            "status": "ok",
            "used_model": model_name # для диагностики
        })

    except Exception as e:
        return jsonify({"response": f"Критическая ошибка: {str(e)}"}), 200

@app.route('/')
def index():
    return "API Nuvera Ready (Smart Select Mode)"
