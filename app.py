from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai
from google.genai.types import Part
from data_config import get_price_json_string

app = Flask(__name__)
CORS(app)

# Инициализация клиента
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

SYSTEM_PROMPT = """Ты — ведущий технолог-полиграфист типографии «Быстрая Печать». 
Опирайся на прайс-лист. Цены в BYN. Не удваивай стоимость ламинации. 
Резка: 20 листов А3 = 4 реза."""

@app.route('/api/ai_chat', methods=['POST'])
def ai_chat_endpoint():
    try:
        data = request.get_json()
        message = data.get('message')
        history = data.get('history', [])

        # ОШИБКА БЫЛА ЗДЕСЬ: В Part.from_text должен быть ТОЛЬКО текст
        user_parts = [Part.from_text(text=message)] 
        
        # Системный контекст (тоже исправлено)
        system_parts = [
            Part.from_text(text=SYSTEM_PROMPT),
            Part.from_text(text=f"ПРАЙС: {get_price_json_string()}")
        ]

        # Собираем контент для отправки
        contents = [
            {"role": "user", "parts": system_parts}
        ] + history + [
            {"role": "user", "parts": user_parts}
        ]

        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=contents
        )

        return jsonify({"response": response.text, "status": "ok"}), 200

    except Exception as e:
        # Это выведет точную причину в логи Vercel, если что-то пойдет не так
        print(f"Error: {str(e)}")
        return jsonify({"response": f"Ошибка: {str(e)}", "manager_alert": True}), 500

if __name__ == '__main__':
    app.run(debug=True)
