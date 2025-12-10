# app.py (Финальный Production-код для nuvera-gemini-api.vercel.app)

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

# !!! FIX CORS: Простая инициализация для надежной обработки OPTIONS
CORS(app) 

# --- Настройки Gemini ---
MODEL_NAME = "gemini-2.5-flash"

# --- Инициализация Gemini API ---
client = None
try:
    # Ожидается, что ключ GEMINI_API_KEY установлен в переменных окружения Vercel
    client = genai.Client()
    logging.info("Gemini client initialized successfully.")
except Exception as e:
    # Если ключ не найден/недействителен, функция не падает, а мы логируем ошибку
    logging.error(f"!!! CRITICAL ERROR: Gemini client failed to initialize: {e}")

# --- Маршрут для ПРОВЕРКИ СТАТУСА ---
@app.route('/', methods=['GET'])
def home():
    """
    Возвращает статус работоспособности API и клиента Gemini.
    """
    if client:
        return "Nuvera AI API is running and Gemini client is ready!", 200
    else:
        # Статус 503 означает ошибку сервиса (например, нерабочий ключ API)
        return "Nuvera AI API is running, but Gemini client failed to initialize (Check GEMINI_API_KEY on Vercel).", 503

# --- Маршрут для ТЕКСТОВОГО ЧАТА ---
@app.route('/api/ai_chat', methods=['POST'])
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

        # --- 1. Форматирование истории чата для Gemini ---
        history = []
        for item in history_data:
            if 'role' in item and item.get('parts') and item['parts'][0].get('text'):
                history.append(Content(
                    role=item['role'],
                    parts=[Part.from_text(item['parts'][0]['text'])]
                ))
        
        # --- 2. Системная инструкция (Промпт) ---
        system_instruction = (
            "Ты — ведущий технолог-полиграфист и автоматизированная система консультаций студии nuvera. "
            "Твой тон: деловой, профессиональный. "
            "Твоя задача — помочь клиенту с расчетом стоимости печати, выбором материала и проверкой требований к макетам. "
            "ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА: Отвечай вежливо, кратко и только по существу, связанному с печатью."
        )

        # --- 3. Создание чата (для сохранения контекста) ---
        chat = client.chats.create(
            model=MODEL_NAME,
            history=history,
            config=GenerateContentConfig(
                system_instruction=system_instruction
            )
        )

        # --- 4. Отправка нового сообщения ---
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
