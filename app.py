import requests
import re
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Твои данные
TOKEN = "8514796589:AAEJqdm3DsCtki-gneHQTLEEIUZKqyiz_tg"
ADMIN_ID = "1055949397"
# Память для хранения ответов (очищается при перезагрузке сервера)
storage = {}

@app.route('/api/ai_chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        res = make_response("", 200)
        res.headers["Access-Control-Allow-Origin"] = "*"
        res.headers["Access-Control-Allow-Headers"] = "*"
        res.headers["Access-Control-Allow-Methods"] = "*"
        return res
    
    try:
        data = request.get_json()
        msg = data.get('message', '')
        uid = data.get('user_id', 'anon')
        
        # Отправляем сообщение тебе в Telegram
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      json={"chat_id": ADMIN_ID, "text": f"ID: [{uid}]\n{msg}"})
        
        r = jsonify({"status": "ok"})
        r.headers["Access-Control-Allow-Origin"] = "*"
        return r
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_answer', methods=['GET'])
def get_answer():
    uid = request.args.get('user_id')
    ans = storage.get(uid)
    if ans:
        del storage[uid]
    res = jsonify({"answer": ans})
    res.headers["Access-Control-Allow-Origin"] = "*"
    return res

@app.route('/api/tg_webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    # Проверяем, является ли сообщение ответом (Reply)
    if data and "message" in data and "reply_to_message" in data["message"]:
        txt = data["message"].get("text")
        orig = data["message"]["reply_to_message"].get("text", "")
        # Ищем ID в формате [u12345]
        match = re.search(r"\[(\w+)\]", orig)
        if match and txt:
            storage[match.group(1)] = txt
    return jsonify({"status": "ok"})

@app.route('/')
def home():
    return "Bridge is alive", 200
