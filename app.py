import requests
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Ваши данные
TELEGRAM_TOKEN = "8514796589:AAEJqdm3DsCtki-gneHQTLEEIUZKqyiz_tg"
ADMIN_ID = "1055949397"

# Временное хранилище для ответов (в памяти сервера)
answers_storage = {}

@app.route('/api/ai_chat', methods=['POST', 'OPTIONS'])
def from_site():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        user_msg = data.get('message', '')
        user_id = data.get('user_id', 'anon') # Получаем ID из Tilda

        if not user_msg:
            return jsonify({"status": "error"}), 400

        # Отправляем сообщение вам в Telegram
        # Формат ID: [u12345] важен для парсинга ответа
        text = f"📩 **Новый вопрос с сайта!**\nID: `[{user_id}]` \n\n💬: {user_msg}\n\n<i>Ответьте на это сообщение (REPLY), чтобы клиент получил ответ.</i>"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": ADMIN_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload)

        return jsonify({
            "status": "ok", 
            "response": "Сообщение доставлено менеджеру. Ожидайте ответ прямо здесь."
        })
    except Exception as e:
        return jsonify({"status": "error", "response": str(e)}), 200

@app.route('/api/get_answer', methods=['GET'])
def get_answer():
    user_id = request.args.get('user_id')
    answer = answers_storage.get(user_id)
    if answer:
        # Удаляем ответ из памяти после того, как клиент его забрал
        del answers_storage[user_id]
        return jsonify({"answer": answer})
    return jsonify({"answer": None})

@app.route('/api/tg_webhook', methods=['POST'])
def tg_webhook():
    data = request.get_json()
    
    # Логика: если вы ответили на сообщение бота (REPLY)
    if "message" in data and "reply_to_message" in data["message"]:
        reply_text = data["message"].get("text")
        original_text = data["message"]["reply_to_message"].get("text", "")
        
        # Ищем ID пользователя в квадратных скобках [ ]
        match = re.search(r"\[(\w+)\]", original_text)
        if match and reply_text:
            user_id = match.group(1)
            answers_storage[user_id] = reply_text
            
    return jsonify({"status": "ok"})

@app.route('/')
def index():
    return "Nuvera Chat Engine Active", 200
