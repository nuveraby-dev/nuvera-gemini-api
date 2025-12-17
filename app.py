import requests
import re
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
# Максимально открываем доступ для всех доменов и методов
CORS(app, resources={r"/*": {"origins": "*"}})

TELEGRAM_TOKEN = "8514796589:AAEJqdm3DsCtki-gneHQTLEEIUZKqyiz_tg"
ADMIN_ID = "1055949397"

answers_storage = {}

# Вспомогательная функция для ответов с правильными заголовками
def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response

@app.route('/api/ai_chat', methods=['POST', 'OPTIONS'])
def from_site():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
        
    try:
        data = request.get_json()
        user_msg = data.get('message', '')
        user_id = data.get('user_id', 'anon')

        text = f"📩 **Новый вопрос!**\nID: `[{user_id}]` \n\n💬: {user_msg}"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": ADMIN_ID, "text": text, "parse_mode": "HTML"})

        return jsonify({"status": "ok", "response": "Сообщение отправлено."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 200

@app.route('/api/get_answer', methods=['GET', 'OPTIONS'])
def get_answer():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
        
    user_id = request.args.get('user_id')
    answer = answers_storage.get(user_id)
    if answer:
        del answers_storage[user_id]
        return jsonify({"answer": answer})
    return jsonify({"answer": None})

@app.route('/api/tg_webhook', methods=['POST'])
def tg_webhook():
    data = request.get_json()
    if "message" in data and "reply_to_message" in data["message"]:
        reply_text = data["message"].get("text")
        original_text = data["message"]["reply_to_message"].get("text", "")
        match = re.search(r"\[(\w+)\]", original_text)
        if match and reply_text:
            user_id = match.group(1)
            answers_storage[user_id] = reply_text
    return jsonify({"status": "ok"})

@app.route('/')
def index():
    return "Bridge Active", 200
