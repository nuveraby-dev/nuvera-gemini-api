from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai
from google.genai.types import Part
from data_config import get_price_json_string

app = Flask(__name__)
CORS(app)

# Инициализация клиента Gemini через переменную окружения
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# Ваш системный промпт
SYSTEM_PROMPT = """Ты — ведущий технолог-полиграфист типографии «Быстрая Печать». 
Опирайся на прайс-лист. Цены строго в BYN. 
Правила: не удваивай ламинацию, резка считается по проходам (20л А3 = 4 реза)."""

@app.route('/api/ai_chat', methods=['POST'])
def ai_chat_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        user_message = data.get('message')
        history = data.get('history', [])

        # ИСПРАВЛЕНИЕ: Part.from_text() принимает ТОЛЬКО ОДИН аргумент (текст)
        # Мы явно указываем именованный аргумент 'text' для надежности
        user_part = Part.from_text(text=user_message)
        
        system_part = Part.from_text(text=f"{SYSTEM_PROMPT}\n\nПРАЙС-ЛИСТ:\n{get_price_json_string()}")

        # Собираем контент для модели
        # Первым сообщением всегда идет системный контекст от имени user
        contents = [
            {"role": "user", "parts": [system_part]}
        ]
        
        # Добавляем историю (убедитесь, что она в формате [{'role':..., 'parts':...}])
        contents.extend(history)
        
        # Добавляем текущее сообщение пользователя
        contents.append({"role": "user", "parts": [user_part]})

        # Вызов модели
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=contents
        )

        return jsonify({
            "response": response.text,
            "status": "ok"
        }), 200

    except Exception as e:
        print(f"Ошибка в ai_chat: {str(e)}")
        return jsonify({
            "response": f"Произошла ошибка: {str(e)}",
            "manager_alert": True
        }), 500

# Корневой маршрут, чтобы не было ошибки 404 при простом открытии ссылки
@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Nuvera Gemini API is running"}), 200

if __name__ == '__main__':
    app.run(debug=True)
