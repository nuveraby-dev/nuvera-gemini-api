from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai
from data_config import get_price_json_string

app = Flask(__name__)
CORS(app)

try:
    API_KEY = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    print(f"Critial Init Error: {e}")

@app.route('/api/ai_chat', methods=['POST'])
def ai_chat_endpoint():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        history = data.get('history', [])

        # Формируем компактный контекст
        prompt = f"Ты технолог Nuvera. Прайс: {get_price_json_string()}. Отвечай кратко. Вопрос: {user_message}"

        # Используем 1.5-flash (она быстрее и стабильнее для Vercel)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )

        return jsonify({"response": response.text, "status": "ok"})

    except Exception as e:
        # Вместо 500 ошибки возвращаем 200 с текстом ошибки, чтобы сайт не «ломался»
        return jsonify({"response": "Сервер перегружен. Попробуйте через 30 секунд.", "error": str(e)}), 200

@app.route('/')
def index():
    return "API Nuvera is running"
