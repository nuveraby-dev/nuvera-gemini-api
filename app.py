from google import genai
from google.genai.types import Part # Убедитесь, что этот импорт присутствует

# ... (ваш код инициализации клиента и других переменных) ...

# -------------------------------------------------------------
# ЭТА ЛОГИКА ДОЛЖНА БЫТЬ ВАШИМ ОБРАБОТЧИКОМ POST-ЗАПРОСА
# -------------------------------------------------------------

def process_chat_request(request):
    # Получение данных из тела запроса (message и history)
    data = request.get_json()
    message = data.get('message')
    history = data.get('history', [])
    
    # 1. Сборка нового сообщения пользователя (user_content)
    # Здесь была ваша ошибка: лишний аргумент в Part.from_text()
    user_content = {
        "role": "user",
        # ИСПРАВЛЕНО: Теперь передается только один аргумент (message)
        "parts": [Part.from_text(message)] 
    }
    
    # 2. Обновление истории: добавляем новое сообщение
    # (Необходимо убедиться, что вся history передается в формате, который 
    # ожидает generate_content - это может быть список Content объектов или словарей)
    contents_for_api = history + [user_content] 

    # 3. Вызов API
    try:
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
            "response": "Произошла внутренняя ошибка сервера. Пожалуйста, обратитесь к менеджеру."
        }), 500 # Возвращаем 500, но с контролируемым сообщением
