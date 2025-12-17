from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai
from google.genai.types import Part
from data_config import get_price_json_string

app = Flask(__name__)
CORS(app)

# Инициализация клиента Gemini
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# Системные инструкции
SYSTEM_PROMPT = """Ты — ведущий технолог типографии Nuvera. 
Твоя задача: консультировать клиентов по ценам и услугам на основе ПРАЙС-ЛИСТА.
Цены строго в BYN. Если клиент спрашивает на русском, отвечай на русском.
Будь кратким и профессиональным."""

@app.route('/api/ai_chat', methods=['POST'])
def ai_chat_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        user_message = data.get('message')
        history = data.get('history', [])

        # Подготовка контекста (Прайс + Инструкция)
        system_context = f"{SYSTEM_PROMPT}\n\nПРАЙС-ЛИСТ (JSON):\n{get_price_json_string()}"
        
        # Формируем структуру запроса
        contents = [
            {"role": "user", "parts": [Part.from_text(text=system_context)]}
        ]
        contents.extend(history)
        contents.append({"role": "user", "parts": [Part.from_text(text=user_message)]})

        # Вызов модели 1.5 Flash (у неё выше лимиты запросов)
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=contents
        )

        return jsonify({
            "response": response.text,
            "status": "ok"
        }), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            "response": "Извините, я временно перегружен. Попробуйте написать через 60 секунд.",
            "status": "error"
        }), 500

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "working", "model": "gemini-1.5-flash"}), 200
