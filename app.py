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
        return jsonify({"response": "Ошибка: API-ключ не найден в настройках Vercel."}), 200

    try:
        genai.configure(api_key=api_key)
        
        # Пробуем версию -latest, она часто подхватывается там, где обычная выдает 404
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        data = request.get_json()
        user_msg = data.get('message', '')

        prompt = (
            f"Ты технолог Nuvera. Прайс: {get_price_json_string()}\n"
            f"Ответь кратко на вопрос: {user_msg}"
        )

        response = model.generate_content(prompt)
        return jsonify({"response": response.text, "status": "ok"})

    except Exception as e:
        # Если снова 404, этот блок выведет список моделей, которые ВАМ доступны
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            return jsonify({
                "response": f"Ошибка: {str(e)}",
                "available_models": available_models[:5] # Покажем первые 5 доступных
            }), 200
        except:
            return jsonify({"response": f"Критическая ошибка: {str(e)}"}), 200

@app.route('/')
def index():
    return "API Nuvera Ready"
