# app.py (Минималистичная версия с декоратором CORS)

import os
from flask import Flask, request, jsonify
# Импортируем cross_origin для явного управления CORS
from flask_cors import cross_origin 
from google import genai
from google.genai.errors import APIError
from google.genai.types import Content, Part, GenerateContentConfig
import logging

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)

# --- Настройка Flask ---
app = Flask(__name__)

# --- Настройки Gemini ---
MODEL_NAME = "gemini-2.5-flash"

# --- Инициализация Gemini API ---
# Попробуем инициализировать клиент здесь, чтобы увидеть, когда функция падает
client = None
try:
    # Ожидает GEMINI_API_KEY
    client = genai.Client()
    logging.info("Gemini client initialized successfully.")
except Exception as e:
    logging.error(f"!!! CRITICAL ERROR: Gemini client failed to initialize: {e}")

# --- Маршрут для ПРОВЕРКИ СТАТУСА ---
@app.route('/', methods=['GET'])
def home():
    if client:
        return "Nuvera AI API is running and Gemini client is ready!", 200
    else:
        # Если API key не найден, вернем 503
        return "Nuvera AI API is running, but Gemini client failed to initialize (Key Error?).", 503

# --- Маршрут для ТЕКСТОВОГО ЧАТА ---
@app.route('/api/ai_chat', methods=['POST'])
# Явно добавляем декоратор CORS
@cross_origin() 
def ai_chat():
    """
    Принимает JSON-запрос с сообщением и историей чата, возвращает ответ Gemini.
    """
    if not client:
        return jsonify({
            "response": "Ошибка API: Gemini client не инициализирован. Проверьте ваш API-ключ на Vercel.",
            "manager_alert": True
        }), 503

    try:
        data = request.get_json()
        user_message = data.get('message', '')
        history_data = data.get('history', [])

        if not user_message:
            return jsonify({"response": "Пожалуйста, отправьте текстовое сообщение.", "manager_alert": False}), 400

        # ... (логика чата остается без изменений) ...
        history = []
        for item in history_data:
            if 'role' in item and item.get('parts') and item['parts'][0].get('text'):
                history.append(Content(
                    role=item['role'],
                    parts=[Part.from_text(item['parts'][0]['text'])]
                ))
        
        system_instruction = (
            "Ты — ведущий технолог-полиграфист и автоматизированная система консультаций студии nuvera. "
            # ... (остальная часть промпта) ...
            "Твой тон: деловой, профессиональный. Твоя задача — помочь клиенту с расчетом стоимости печати, выбором материала и проверкой требований к макетам. ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА: Отвечай вежливо, кратко и только по существу, связанному с печатью."
        )

        chat = client.chats.create(
            model=MODEL_NAME,
            history=history,
            config=GenerateContentConfig(
                system_instruction=system_instruction
            )
        )

        ai_response_result = chat.send_message(user_message)
        ai_response = ai_response_result.text

        return jsonify({"response": ai_response, "manager_alert": False})

    except APIError as api_e:
        logging.error(f"Ошибка Gemini API (во время запроса): {api_e}")
        return jsonify({
            "response": "Произошла ошибка API (Gemini). Пожалуйста, попробуйте позже.",
            "manager_alert": True
        }), 500

    except Exception as e:
        logging.error(f"Общая внутренняя ошибка в ai_chat: {e}")
        return jsonify({
            "response": "Произошла внутренняя ошибка сервера. Пожалуйста, обратитесь к менеджеру.",
            "manager_alert": True
        }), 500
