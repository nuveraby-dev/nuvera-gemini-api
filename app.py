# app.py (Финальный рабочий код для AI-помощника сайта на Vercel)

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai.errors import APIError
from google.genai.types import Content, Part, GenerateContentConfig
import logging

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)

# --- Настройка Flask ---
app = Flask(__name__)
# Разрешаем запросы со всех внешних доменов
CORS(app)

# --- Инициализация Gemini API ---
client = None
MODEL_NAME = "gemini-2.5-flash"
# Ключ будет автоматически считан из переменной окружения Vercel
try:
    # Клиент автоматически ищет GEMINI_API_KEY в переменных окружения
    # Убедитесь, что на Vercel ключ называется GEMINI_API_KEY
    client = genai.Client()
    logging.info("Gemini client initialized successfully.")
except Exception as e:
    logging.error(f"!!! CRITICAL ERROR: Gemini client failed to initialize: {e}")
    # Если инициализация не удалась, клиент останется None

# --- Маршрут для ТЕСТИРОВАНИЯ ---
@app.route('/', methods=['GET'])
def home():
    if client:
        return "Nuvera AI API is running and Gemini client is ready!", 200
    else:
        return "Nuvera AI API is running, but Gemini client failed to initialize. Check API Key.", 503

# --- Маршрут для ТЕКСТОВОГО ЧАТА ---
@app.route('/api/ai_chat', methods=['POST'])
def ai_chat():
    if not client:
        return jsonify({
            "response": "Ошибка API: Gemini client не инициализирован. Проверьте ваш API-ключ на Vercel.",
            "manager_alert": True
        }), 503

    try:
        data = request.get_json()
        user_message = data.get('message', '')
        # История чата в формате Tilda/JS
        history_data = data.get('history', [])

        # 1. Форматирование истории чата для Gemini
        history = []
        for item in history_data:
            # Проверяем, что необходимые поля существуют
            if 'role' in item and item.get('parts') and item['parts'][0].get('text'):
                history.append(Content(
                    role=item['role'],
                    parts=[Part.from_text(item['parts'][0]['text'])]
                ))

        # 2. Системная инструкция
        # Вы можете добавить сюда вашу JSON-таблицу с ценами, как планировали
        system_instruction = (
            "Ты – AI-консультант компании Nuvera, специализирующейся на широкоформатной печати и производстве рекламных конструкций. "
            "Твоя задача — помочь клиенту с расчетом стоимости печати, выбором материала и проверкой требований к макетам. "
            "Отвечай вежливо, кратко и только по существу, связанному с печатью."
        )

        # 3. Создание чата (для сохранения контекста)
        chat = client.chats.create(
            model=MODEL_NAME,
            history=history,
            config=GenerateContentConfig(
                system_instruction=system_instruction
            )
        )

        # 4. Отправка нового сообщения и получение ответа
        ai_response_result = chat.send_message(user_message)
        ai_response = ai_response_result.text

        return jsonify({"response": ai_response, "manager_alert": False})

    except APIError as api_e:
        logging.error(f"Ошибка Gemini API (во время запроса): {api_e}")
        return jsonify({
            "response": "Произошла ошибка API (Gemini). Проверьте ключ API или лимиты запросов.",
            "manager_alert": True
        }), 500

    except Exception as e:
        logging.error(f"Общая внутренняя ошибка в ai_chat: {e}")
        return jsonify({
            "response": "Произошла внутренняя ошибка сервера. Пожалуйста, обратитесь к менеджеру.",
            "manager_alert": True
        }), 500
