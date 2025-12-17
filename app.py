from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
from data_config import get_price_json_string

app = Flask(__name__)
# Разрешаем запросы с любого источника (чтобы Tilda и тесты не блокировались)
CORS(app)

@app.route('/api/ai_chat', methods=['POST'])
def ai_chat_endpoint():
    # 1. Проверяем ключ
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"response": "Ошибка: Не найден GEMINI_API_KEY в настройках Vercel."}), 200

    try:
        # 2. Настраиваем библиотеку (стабильный метод)
        genai.configure(api_key=api_key)
        
        # 3. Выбираем модель (здесь имя 'gemini-1.5-flash' работает всегда)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 4. Получаем сообщение
        data = request.get_json()
        user_msg = data.get('message', '')
        
        if not user_msg:
             return jsonify({"response": "Вы прислали пустое сообщение."}), 200

        # 5. Собираем промпт (Прайс + Вопрос)
        full_prompt = (
            f"Ты — технолог типографии Nuvera. Твоя задача — консультировать по ценам.\n"
            f"Вот актуальный прайс-лист: {get_price_json_string()}\n"
            f"Отвечай вежливо, кратко и только на основе этого прайса. Валюта: BYN.\n"
            f"Вопрос клиента: {user_msg}"
        )

        # 6. Отправляем запрос
        response = model.generate_content(full_prompt)
        
        return jsonify({
            "response": response.text, 
            "status": "ok"
        })

    except Exception as e:
        # Если вдруг ошибка — выводим её текст, чтобы сразу понять причину
        return jsonify({"response": f"Ошибка сервера: {str(e)}"}), 200

@app.route('/')
def index():
    return "API Nuvera (Region: CLE1) is Running", 200
