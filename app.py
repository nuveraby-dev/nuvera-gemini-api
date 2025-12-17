import requests
import re
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

TELEGRAM_TOKEN = "8514796589:AAEJqdm3DsCtki-gneHQTLEEIUZKqyiz_tg"
ADMIN_ID = "1055949397"
answers_storage = {}

def _cors_response(data, status=200):
    response = make_response(jsonify(data), status)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@app.route('/api/ai_chat', methods=['POST', 'OPTIONS'])
def from_site():
    if request.method == 'OPTIONS':
        return _cors_response({}, 200)
    try:
        data = request.get_json()
        msg = data.get('message', '')
        uid = data.get('user_id', 'anon')
        text = f"📩 **Сообщение с сайта!**\nID: `[{uid}]` \n\n💬: {msg}"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={"chat_id": ADMIN_ID, "text": text, "parse_mode": "HTML"}, timeout=5)
        return _cors_response({"status": "ok"})
    except Exception as e:
        return _cors_response({"status": "error", "error": str(e)}, 500)

@app.route('/api/get_answer', methods=['GET', 'OPTIONS'])
def get_answer():
    if request.method == 'OPTIONS':
        return _cors_response({}, 200)
    uid = request.args.get('user_id')
    ans = answers_storage.get(uid)
    if ans:
        del answers_storage[uid]
        return _cors_response({"answer": ans})
    return _cors_response({"answer": None})

@app.route('/api/tg_webhook', methods=['POST'])
def tg_webhook():
    data = request.get_json()
    if data and "message" in data and "reply_to_message" in data["message"]:
        reply = data["message"].get("text")
        original = data["message"]["reply_to_message"].get("text", "")
        match = re.search(r"\[(\w+)\]", original)
        if match and reply:
            answers_storage[match.group(1)] = reply
    return jsonify({"status": "ok"})

@app.route('/')
def index():
    return "OK", 200
