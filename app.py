import requests
import re
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
# Включаем базовый CORS
CORS(app)

TELEGRAM_TOKEN = "8514796589:AAEJqdm3DsCtki-gneHQTLEEIUZKqyiz_tg"
ADMIN_ID = "1055949397"

# Временное хранилище ответов
answers_storage = {}

# Универсальная функция для отправки ответа с правильными заголовками
def send_res(data, status=200):
    res = make_response(jsonify(data), status)
    res.headers["Access-Control-Allow-Origin"] = "*"
    res.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    res.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return res

@app.before_request
def handle_preflight():
    # Если браузер просто проверяет права (OPTIONS), сразу говорим "ОК"
    if request.method == "OPTIONS":
        return send_res({}, 200)

@app.route('/api/ai_chat', methods=['POST'])
def from_site():
    try:
        data = request.get_json()
        if not data:
            return send_res({"error": "no_data"}, 400)
            
        msg = data.get('message', '')
        uid = data.get('user_id', 'anon')

        # Отправка в Телеграм
        text = f"📩 **Новое сообщение!**\nID: `[{uid}]` \n\n💬: {msg}"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        
        requests.post(url, json={"chat_id": ADMIN_ID, "text": text, "parse_mode": "HTML"}, timeout=7)
        
        return send_res({"status": "ok"})
    except Exception as e:
        return send_res({"error": str(e)}, 500)

@app.route('/api/get_answer', methods=['GET'])
def get_answer():
    uid = request.args.get('user_id')
    answer = answers_storage.get(uid)
    if answer:
        del answers_storage[uid]
        return send_res({"answer": answer})
    return send_res({"answer": None})

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

@app.route('/')
def index():
    return "Nuvera Bridge Online", 200
