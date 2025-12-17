import requests
import re
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
# Включаем CORS максимально мягко
CORS(app)

TELEGRAM_TOKEN = "8514796589:AAEJqdm3DsCtki-gneHQTLEEIUZKqyiz_tg"
ADMIN_ID = "1055949397"

# Память для ответов
answers_storage = {}

@app.route('/api/ai_chat', methods=['POST', 'OPTIONS'])
def from_site():
    if request.method == 'OPTIONS':
        return _build_cors_response()
        
    try:
        data = request.get_json()
        user_msg = data.get('message', '')
        user_id = data.get('user_id', 'anon')

        # Отправляем в ТГ
        text = f"📩 **Новое сообщение!**\nID: `[{user_id}]` \n\n💬: {user_msg}"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        
        # Используем timeout, чтобы запрос не висел вечно
        requests.post(url, json={"chat_id": ADMIN_ID, "text": text, "parse_mode": "HTML"}, timeout=5)

        return _build_cors_response(jsonify({"status": "ok"}))
    except Exception as e:
        return _build_cors_response(jsonify({"status": "error", "error": str(e)}), 500)

@app.route('/api/get_answer', methods=['GET', 'OPTIONS'])
def get_answer():
    if request.method == 'OPTIONS':
        return _build_cors_response()
        
    user_id = request.args.get('user_id')
    answer = answers_storage.get(user_id)
    if answer:
        del answers_storage[user_id]
        return _build_cors_response(jsonify({"answer": answer}))
    return _build_cors_response(jsonify({"answer": None}))

@app.route('/api/tg_webhook', methods=['POST'])
def tg_webhook():
    data = request.get_json()
    if data and "message" in data and "reply_to_message" in data["message"]:
        reply_text = data["message"].get("text")
        original_text = data["message"]["reply_to_message"].get("text", "")
        match = re.search(r"\[(\w+)\]", original_text)
        if match and reply_text:
            user_id = match.group(1)
            answers_storage[user_id] = reply_text
    return jsonify({"status": "ok"})

def _build_cors_response(response=None, status=200):
    if response is None:
        response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
    return response, status

@app.route('/')
def index():
    return "Nuvera Bridge OK", 200
