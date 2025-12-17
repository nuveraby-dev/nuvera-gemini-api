import requests
import re
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
# Разрешаем CORS максимально широко
CORS(app, resources={r"/*": {"origins": "*"}})

TELEGRAM_TOKEN = "8514796589:AAEJqdm3DsCtki-gneHQTLEEIUZKqyiz_tg"
ADMIN_ID = "1055949397"

# Хранилище ответов
answers_storage = {}

def build_cors_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route('/api/ai_chat', methods=['POST', 'OPTIONS'])
def from_site():
    if request.method == 'OPTIONS':
        # Предварительный запрос от браузера Tilda
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        return response

    try:
        data = request.get_json()
        user_msg = data.get('message', '')
        user_id = data.get('user_id', 'anon')

        # Отправка в Телеграм
        text = f"📩 **Новый вопрос!**\nID: `[{user_id}]` \n\n💬: {user_msg}"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        
        requests.post(url, json={"chat_id": ADMIN_ID, "text": text, "parse_mode": "HTML"}, timeout=10)

        return build_cors_actual_response(jsonify({"status": "ok"}))
    except Exception as e:
        return build_cors_actual_response(jsonify({"error": str(e)}), 500)

@app.route('/api/get_answer', methods=['GET', 'OPTIONS'])
def get_answer():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "GET")
        return response

    user_id = request.args.get('user_id')
    answer = answers_storage.get(user_id)
    if answer:
        del answers_storage[user_id]
        return build_cors_actual_response(jsonify({"answer": answer}))
    return build_cors_actual_response(jsonify({"answer": None}))

@app.route('/api/tg_webhook', methods=['POST'])
def tg_webhook():
    data = request.get_json()
    # Если ты ответил на сообщение (Reply)
    if data and "message" in data and "reply_to_message" in data["message"]:
        reply_text = data["message"].get("text")
        original_text = data["message"]["reply_to_message"].get("text", "")
        
        # Ищем ID в квадратных скобках
        match = re.search(r"\[(\w+)\]", original_text)
        if match and reply_text:
            uid = match.group(1)
            answers_storage[uid] = reply_text
            
    return jsonify({"status": "ok"})

@app.route('/')
def index():
    return "Nuvera Bridge OK", 200
