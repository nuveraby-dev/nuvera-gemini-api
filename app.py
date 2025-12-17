import requests
import re
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
# Разрешаем CORS для всех путей
CORS(app)

TELEGRAM_TOKEN = "8514796589:AAEJqdm3DsCtki-gneHQTLEEIUZKqyiz_tg"
ADMIN_ID = "1055949397"

# Память для хранения ответов менеджера
answers_storage = {}

def _build_cors_response(data, status=200):
    response = make_response(jsonify(data), status)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@app.route('/api/ai_chat', methods=['POST', 'OPTIONS'])
def from_site():
    if request.method == 'OPTIONS':
        return _build_cors_response({}, 200)
    
    try:
        data = request.get_json()
        msg = data.get('message', '')
        uid = data.get('user_id', 'anon')

        # Отправка сообщения в Telegram
        text = f"📩 **Сообщение с сайта!**\nID: `[{uid}]` \n\n💬: {msg}"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        
        requests.post(url, json={"chat_id": ADMIN_ID, "text": text, "parse_mode": "HTML"}, timeout=5)
        
        return _build_cors_response({"status": "ok"})
    except Exception as e:
        return _build_cors_response({"status": "error", "message": str(e)}, 500)

@app.route('/api/get_answer', methods=['GET', 'OPTIONS'])
def get_answer():
    if request.method == 'OPTIONS':
        return _build_cors_response({}, 200)
        
    uid = request.args.get('user_id')
    answer = answers_storage.get(uid)
    if answer:
        del answers_storage[uid]
        return _build_cors_response({"answer": answer})
    return _build_cors_response({"answer": None})

@app.route('/api/tg_webhook', methods=['POST'])
def tg_webhook():
    data = request.get_json()
    # Логика обработки ответа (Reply) из Telegram
    if data and "message" in data and "reply_to_message" in data["message"]:
        reply_text = data["message"].get("text")
        original_text = data["message"]["reply_to_message"].get("text", "")
        # Ищем ID пользователя в формате [u12345]
        match = re.search(r"\[(\w+)\]", original_text)
        if match and reply_text:
            user_id = match.group(1)
            answers_storage[user_id] = reply_text
            
    return jsonify({"status": "ok"})

@app.route('/')
def index():
    return "Nuvera Bridge Online", 200
