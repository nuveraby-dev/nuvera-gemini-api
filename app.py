# app.py (Изменения только в секции инициализации клиента)

# ... (импорты)
# ... (настройка Flask и CORS(app) остается)

# --- Настройки Gemini ---
MODEL_NAME = "gemini-2.5-flash"

# --- Инициализация Gemini API ---
client = None
try:
    # 1. Читаем ваш ключ из переменной CLIENT_KEY__
    my_api_key = os.environ.get("CLIENT_KEY__") 
    
    # 2. Если ключ найден, передаем его явно при инициализации
    if my_api_key:
        client = genai.Client(api_key=my_api_key)
        logging.info("Gemini client initialized successfully using CLIENT_KEY__.")
    else:
        # 3. Если ключ не найден, логируем ошибку
        raise ValueError("Environment variable CLIENT_KEY__ not found.")

except Exception as e:
    logging.error(f"!!! CRITICAL ERROR: Gemini client failed to initialize: {e}")

# ... (Остальной код app.py) ...
