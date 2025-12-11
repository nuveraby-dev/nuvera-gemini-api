from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json

# Импорты для Gemini
from google import genai
from google.genai.types import Part

# Импорт конфигурации
from data_config import get_price_json_string

# -----------------------------------------------------------------
# 1. КОНФИГУРАЦИЯ И ИНИЦИАЛИЗАЦИЯ
# -----------------------------------------------------------------

app = Flask(__name__)
CORS(app) # Разрешаем CORS

# Получение API ключа из переменных окружения Vercel
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    # Используйте raise только для локальной отладки или в начале развертывания
    print("FATAL ERROR: GEMINI_API_KEY environment variable not set.")
    # На Vercel этот print уйдет в логи, но не прервет работу, 
    # однако вызовы client.models.generate_content будут падать, 
    # если не будет инициализации клиента.

# Инициализация клиента Gemini
try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    # Клиент не будет инициализирован, если ключа нет, но мы продолжим, 
    # чтобы обработчик мог вернуть 500 с сообщением
    print(f"Ошибка инициализации клиента Gemini: {e}")
    client = None

# -----------------------------------------------------------------
# 2. СИСТЕМНЫЙ ПРОМПТ
# -----------------------------------------------------------------

# !!! Вставьте сюда ваш полный системный промпт из предыдущих обсуждений !!!
SYSTEM_PROMPT = (
    "Ты — ведущий технолог-полиграфист и автоматизированная система консультаций типографии «Быстрая Печать». "
    "Твой тон: профессиональный, деловой и вежливый. Общение должно быть строго по факту запроса, "
    "но с использованием нейтральных, доброжелательных конструкций. "
    "Опирайся на полиграфическую теорию и прикрепленные данные."
    # ... Ваш полный промпт с правилами резки, ламинации и т.д. ...
)

# Дополнительные данные, прикрепленные к промпту
PRICE_LIST_STRING = get_price_json_string()

# -----------------------------------------------------------------
# 3. МАРШРУТИЗАЦИЯ И ОБРАБОТКА ЗАПРОСОВ
# -----------------------------------------------------------------

@app.route('/api/ai_chat', methods=['POST'])
def process_chat_request():
    if client is None:
         return jsonify({
            "manager_alert": True,
            "response": "Ошибка конфигурации сервера: API ключ не найден."
        }), 500

    try:
        # Получение данных из тела запроса
        data = request.get_json()
        message = data.get('message')
        history = data.get('history', [])
        
        if not message:
            return jsonify({"response": "Пустой запрос.", "status": "error"}), 400
        
        # 1. Сборка нового сообщения пользователя (user_content)
        user_content = {
            "role": "user",
            "parts": [Part.from_text(message)] # ИСПРАВЛЕНО: Один аргумент
        }
        
        # 2. Добавление системного промпта и прайс-листа в начало истории
        # Это гарантирует, что промпт и прайс-лист всегда присутствуют
        system_content = {
            "role": "user",
            "parts": [
                Part.from_text(SYSTEM_PROMPT),
                Part.from_text(f"ПРИКРЕПЛЕННЫЙ ПРАЙС-ЛИСТ:\n{PRICE_LIST_STRING}")
            ]
        }
        
        contents_for_api = [system_content] + history + [user_content]

        # 3. Вызов API
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents_for_api
        )
        
        # 4. Сборка ответа для клиента
        ai_response = response.text
        return jsonify({"response": ai_response, "status": "ok"}), 200

    except Exception as e:
        # Улучшенная обработка ошибок для предотвращения 500-й ошибки
        print(f"Общая внутренняя ошибка в ai_chat: {e}")
        return jsonify({
            "manager_alert": True,
            "response": f"Произошла внутренняя ошибка сервера. Код: {e}"
        }), 500 

# -----------------------------------------------------------------
# 4. ОБРАБОТЧИК ДЛЯ VERCEL (только для Vercel)
# -----------------------------------------------------------------

# Этот код нужен для того, чтобы Vercel мог найти WSGI приложение
# В вашем случае, если вы используете vercel.json, Vercel будет искать 
# WSGI приложение 'app' в 'app.py'
if __name__ == '__main__':
    app.run(debug=True)
