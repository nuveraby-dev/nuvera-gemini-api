# app.py (Финальный Production-код с безопасным чтением JSON)

# ... (импорты и инициализация остаются без изменений)
# ...

# --- Маршрут для ТЕКСТОВОГО ЧАТА ---
@app.route('/api/ai_chat', methods=['POST'])
def ai_chat():
    if not client:
        return jsonify({
            "response": "Ошибка API: Gemini client не инициализирован. Проверьте ваш API-ключ на Vercel.",
            "manager_alert": True
        }), 503

    try:
        # --- КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: БЕЗОПАСНОЕ ЧТЕНИЕ JSON ---
        # Получаем JSON-данные. Silent=True предотвращает сбой функции, 
        # возвращая None, если данные невалидны или отсутствуют.
        data = request.get_json(silent=True) 

        if not data:
            logging.error("В ai_chat получен пустой или невалидный JSON-запрос.")
            return jsonify({
                "response": "Ошибка запроса: Получены невалидные данные от клиента.",
                "manager_alert": False
            }), 400

        user_message = data.get('message', '')
        history_data = data.get('history', [])
        # --- КОНЕЦ КРИТИЧЕСКОГО ИЗМЕНЕНИЯ ---

        if not user_message:
            return jsonify({"response": "Пожалуйста, отправьте текстовое сообщение.", "manager_alert": False}), 400

        # --- 1. ФОРМАТИРОВАНИЕ ИСТОРИИ ЧАТА (Оставляем ИСПРАВЛЕННЫЙ код) ---
        history = []
        for item in history_data:
            if 'role' in item and item.get('parts') and item['parts'][0].get('text'):
                history.append(Content(
                    role=item['role'],
                    parts=[Part.from_text(item['parts'][0]['text'])] 
                ))
        
        # ... (Остальная логика чата остается без изменений) ...

        system_instruction = (
            "Ты — ведущий технолог-полиграфист и автоматизированная система консультаций студии nuvera. "
            "Твой тон: деловой, профессиональный. "
            "Твоя задача — помочь клиенту с расчетом стоимости печати, выбором материала и проверкой требований к макетам. "
            "ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА: Отвечай вежливо, кратко и только по существу, связанному с печатью."
        )

        chat = client.chats.create(
            model=MODEL_NAME,
            history=history,
            config=GenerateContentConfig(
                system_instruction=system_instruction
            )
        )

        ai_response_result = chat.send_message(user_message)
        ai_response = ai_response_result.text

        return jsonify({"response": ai_response, "manager_alert": False})

    except APIError as api_e:
        logging.error(f"Ошибка Gemini API (во время запроса): {api_e}")
        return jsonify({
            "response": "Произошла ошибка API (Gemini). Попробуйте позже.",
            "manager_alert": True
        }), 500

    except Exception as e:
        logging.error(f"Общая внутренняя ошибка в ai_chat: {e}")
        return jsonify({
            "response": "Произошла внутренняя ошибка сервера. Пожалуйста, обратитесь к менеджеру.",
            "manager_alert": True
        }), 500
