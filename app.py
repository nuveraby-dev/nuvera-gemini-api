from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
import re
from data_config import get_price_data

app = Flask(__name__)
# Разрешаем запросы с любых доменов (для Tilda)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/api/ai_chat', methods=['POST', 'OPTIONS'])
def ai_chat_endpoint():
    # Обработка предварительного запроса браузера
    if request.method == 'OPTIONS':
        return '', 200

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"response": "Ошибка: API ключ не настроен в Vercel."}), 200

    try:
        # Настройка Google AI
        genai.configure(api_key=api_key)
        
        # Получаем сообщение от пользователя
        data = request.get_json()
        user_msg = data.get('message', '')
        user_msg_lower = user_msg.lower()

        # Загружаем разбитый на блоки прайс
        price_dict = get_price_data()
        
        # Логика подбора контекста (Умный фильтр)
        # Это экономит 80% лимитов, отправляя только нужный блок
        if any(x in user_msg_lower for x in ["фото", "паспорт", "10х15", "селфи"]):
            context = price_dict["фото"]
        elif any(x in user_msg_lower for x in ["чертеж", "а1", "а0", "а2", "проект", "фальц", "склад"]):
            context = price_dict["чертежи"]
        elif any(x in user_msg_lower for x in ["визитк", "карточк"]):
            context = price_dict["визитки"]
        elif any(x in user_msg_lower for x in ["офсет", "1000", "тираж", "флаер", "листовк"]):
            context = price_dict["офсет"]
        elif any(x in user_msg_lower for x in ["бумаг", "картон", "наклейк", "стикер", "sra3"]):
            context = price_dict["бумага"]
        elif any(x in user_msg_lower for x in ["ламин", "переплет", "резка", "копия", "скан"]):
            context = price_dict["обработка_и_правила"]
        else:
            # Если тема не ясна или общая (печать документов)
            context = price_dict["печать"]

        # Инициализация модели (используем стабильную версию)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Системная инструкция (максимально сжатая)
        prompt = (
            f"Ты ИИ-технолог типографии Nuvera. Прайс: {context}. "
            f"Правила: отвечай супер-кратко (1-2 предложения), вежливо, без символов * и #. "
            f"Если в этой части прайса нет ответа, скажи 'Уточните у менеджера'. "
            f"Вопрос: {user_msg}"
        )

        # Генерация ответа
        response = model.generate_content(prompt)
        
        # Дополнительная чистка текста на стороне сервера
        clean_text = response.text.replace('*', '').replace('#', '').strip()
        
        return jsonify({
            "response": clean_text,
            "status": "ok"
        })

    except Exception as e:
        error_msg = str(e)
        # Красивый перехват лимитов
        if "429" in error_msg:
            return jsonify({"response": "Много запросов. Пожалуйста, подождите 1 минуту."}), 200
        return jsonify({"response": f"Системная ошибка: {error_msg}"}), 200

@app.route('/')
def index():
    return "Nuvera AI API (Smart Filtering) is Online", 200
