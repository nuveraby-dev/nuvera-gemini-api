import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

TELEGRAM_TOKEN = "8514796589:AAEJqdm3DsCtki-gneHQTLEEIUZKqyiz_tg"
ADMIN_ID = "1055949397"

# Временное хранилище ответов (в памяти сервера)
# Формат: { user_id: "текст ответа" }
answers_storage = {}

@app.route('/api/ai_chat', methods=['POST'])
def from_site():
    data = request.get_json()
    user_msg = data.get('message', '')
    user_id = data.get('user_id', 'anon') # Уникальный ID сессии клиента

    if not user_msg:
        return jsonify({"status": "error"}), 400

    # Отправляем сообщение вам в Telegram
    # Добавляем в текст ID пользователя, чтобы вы могли ответить реплаем (ответом)
    text = f"📩 **Новый вопрос!**\nID: `{user_id}`\n\n💬: {user_msg}\n\n<i>Чтобы ответить, просто напишите ответ в боте.</i>"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)

    return jsonify({"status": "ok", "response": "Сообщение доставлено менеджеру. Ожидайте ответ прямо здесь."})

# Эндпоинт для получения ответов (Tilda будет сюда стучаться)
@app.route('/api/get_answer', methods=['GET'])
def get_answer():
    user_id = request.args.get('user_id')
    answer = answers_storage.get(user_id)
    if answer:
        del answers_storage[user_id] # Удаляем после прочтения
        return jsonify({"answer": answer})
    return jsonify({"answer": None})

# Эндпоинт для Telegram Webhook (сюда придут ваши ответы из TG)
@app.route('/api/tg_webhook', methods=['POST'])
def tg_webhook():
    data = request.get_json()
    
    # Проверяем, что это сообщение-ответ (Reply)
    if "message" in data and "reply_to_message" in data["message"]:
        reply_text = data["message"]["text"]
        original_text = data["message"]["reply_to_message"]["text"]
        
        # Вытаскиваем ID пользователя из оригинального сообщения с помощью регулярки или поиска
        import re
        match = re.search(r"ID: (\w+)", original_text)
        if match:
            user_id = match.group(1)
            answers_storage[user_id] = reply_text # Кладем ответ в хранилище
            
    return jsonify({"status": "ok"})

@app.route('/')
def index():
    return "Nuvera Chat Engine Active", 200
