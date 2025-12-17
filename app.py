import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Разрешаем запросы с Tilda
CORS(app, resources={r"/*": {"origins": "*"}})

# Твои данные бота
TELEGRAM_TOKEN = "8514796589:AAEJqdm3DsCtki-gneHQTLEEIUZKqyiz_tg"
TELEGRAM_CHAT_ID = "1055949397"

@app.route('/api/ai_chat', methods=['POST', 'OPTIONS'])
def telegram_bridge():
    # Обработка предварительного запроса браузера (CORS)
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json()
        user_msg = data.get('message', '')

        if not user_msg:
            return jsonify({"status": "error", "response": "Пустое сообщение"}), 400

        # Формируем текст сообщения для Telegram
        full_text = f"📩 **Новое сообщение с сайта Nuvera!**\n\n💬 Текст: {user_msg}"
        
        # Отправка через Telegram Bot API
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": full_text,
            "parse_mode": "Markdown"
        }
        
        tg_response = requests.post(url, json=payload)
        
        if tg_response.status_code == 200:
            return jsonify({
                "response": "Ваше сообщение отправлено менеджеру! Мы ответим вам в ближайшее время.",
                "status": "ok"
            })
        else:
            return jsonify({
                "response": "Ошибка при отправке в Telegram. Проверьте токен бота.",
                "status": "error"
            }), 200

    except Exception as e:
        return jsonify({
            "response": f"Системная ошибка: {str(e)}",
            "status": "error"
        }), 200

@app.route('/')
def index():
    return "Nuvera TG Bridge is Active", 200
