from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai
from data_config import get_price_json_string

app = Flask(__name__)
# Разрешаем CORS только для вашего домена для безопасности
CORS(app, resources={r"/api/*": {"origins": "https://nuvera-print.by"}})

# Инициализация клиента
try:
    API_KEY = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    print(f"Startup Error: {e}")

@app.route('/api/ai_chat', methods=['POST'])
def ai_chat_endpoint():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"response": "Пустой запрос"}), 400

        user_msg = data.get('message')
        
        # Максимально простой промпт для Gemini 1.5 Flash
        context = f"Ты технолог Nuvera. Прайс: {get_price_json_string()}. Отвечай кратко."
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=f"{context}\nВопрос пользователя: {user_msg}"
        )

        return jsonify({"response": response.text, "status": "ok"})

    except Exception as e:
        # Логируем ошибку в консоль Vercel
        print(f"Runtime Error: {str(e)}")
        # Возвращаем 200 статус, чтобы браузер не выдавал 500 ошибку
        return jsonify({"response": "Сервер временно отдыхает. Попробуйте через минуту."}), 200

@app.route('/', methods=['GET'])
def index():
    return "API Nuvera Active", 200
