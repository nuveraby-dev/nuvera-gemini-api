import asyncio
import logging
import os
import pathlib
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, ReplyKeyboardRemove
from google import genai
from dotenv import load_dotenv

# Подключаем наш новый файл с данными
from data_config import get_price_json_string

# --- ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')
AI_API_KEY = os.getenv('GEMINI_KEY')
# Убедимся, что ADMIN_ID корректно считывается
try:
    ADMIN_ID = int(os.getenv('ADMIN_ID'))
except (TypeError, ValueError):
    logging.error("ADMIN_ID не найден или некорректен в .env!")
    ADMIN_ID = 0 # Используем 0, чтобы избежать сбоя, но логируем ошибку

# --- НАСТРОЙКИ GEMINI ---
GEMINI_MODEL = "gemini-2.5-flash" 
os.environ['GEMINI_API_TIMEOUT_SECONDS'] = '120'

# Глобальные переменные
tech_requirements_gemini_file = None
gemini_client = None
DOWNLOAD_DIR = 'downloads'

# --- ИНИЦИАЛИЗАЦИЯ ---
logging.basicConfig(level=logging.INFO)

# Проверка, что ключи загружены перед инициализацией
if not API_TOKEN:
    logging.error("CRITICAL ERROR: BOT_TOKEN не найден в .env file.")
    exit()
if not AI_API_KEY:
    logging.error("CRITICAL ERROR: GEMINI_KEY не найден в .env file.")
    # Бот может работать без ИИ, но лучше предупредить
    pass

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Инициализация Gemini Client и загрузка требований
async def on_startup():
    global gemini_client, tech_requirements_gemini_file
    pathlib.Path(DOWNLOAD_DIR).mkdir(exist_ok=True)
    
    # Проверка, есть ли ключи для инициализации ИИ
    if not AI_API_KEY:
         logging.warning("Инициализация Gemini пропущена, так как GEMINI_KEY не найден.")
         return

    try:
        logging.info("Connecting to Gemini...")
        gemini_client = genai.Client(api_key=AI_API_KEY)
        
        # Загружаем только requirements, так как прайс теперь в JSON
        logging.info("Uploading requirements.pdf to Gemini...")
        if os.path.exists("requirements.pdf"):
            tech_requirements_gemini_file = gemini_client.files.upload(file="requirements.pdf")
            logging.info("Requirements uploaded successfully.")
        else:
            logging.warning("Файл requirements.pdf не найден! Анализ макетов будет работать хуже.")
            
    except Exception as e:
        logging.error(f"CRITICAL GEMINI ERROR: {e}")
        gemini_client = None # Сброс клиента, чтобы не пытаться использовать его в ошибке

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ АНАЛИЗА GEMINI VISION ---
async def analyze_design_file(gemini_client, file_path, tech_requirements_file):
    uploaded_file = None
    try:
        uploaded_file = gemini_client.files.upload(file=file_path)
        
        contents = [
            "Проанализируй макет согласно тех. требованиям. Проверь вылеты, CMYK/RGB, разрешение. Ответь кратко маркированным списком. В конце: 'Макет готов к печати' или 'Макет требует доработки'.",
            uploaded_file
        ]
        
        if tech_requirements_file:
            contents.append(tech_requirements_file)
            
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
        )
        return response.text
    except Exception as e:
        logging.error(f"Gemini Vision Analysis Error: {e}")
        return "❌ Ошибка при анализе макета с помощью ИИ."
    finally:
        if uploaded_file:
            try:
                gemini_client.files.delete(name=uploaded_file.name)
            except Exception as delete_e:
                logging.warning(f"Failed to delete uploaded Gemini file: {delete_e}")

async def process_design_file_and_send_to_manager(bot, gemini_client, tech_file, file_id, file_name, message):
    ai_report = "⚠️ ИИ недоступен."
    temp_file_name = f"{DOWNLOAD_DIR}/{file_id}_{file_name}"
    
    # Сначала пытаемся скачать, если ИИ доступен
    if gemini_client:
        file_info = await bot.get_file(file_id)
        
        try:
            await message.answer("✅ Файл принят. Начинаю автоматический анализ...")
            await bot.download_file(file_info.file_path, temp_file_name)
            ai_report = await analyze_design_file(gemini_client, temp_file_name, tech_file)
        except Exception as e:
            logging.error(f"AI/Download Error: {e}")
            ai_report = "❌ Ошибка анализа."
    
    username = f"@{message.from_user.username}" if message.from_user.username else "Без ника"
    manager_message = (f"🔥 <b>НОВЫЙ ЗАКАЗ</b>\nОт клиента: {username}\nФайл: {file_name}\n\n--- <b>ОТЧЕТ ИИ-ТЕХНОЛОГА</b> ---\n{ai_report}\n---------------------------------\n<b>Оригинальный макет прикреплен ниже.</b>")
    
    try:
        # 💡 ИСПРАВЛЕННАЯ ЛОГИКА ОТПРАВКИ МЕНЕДЖЕРУ
        if os.path.exists(temp_file_name):
            # Отправляем локально скачанный файл (и удаляем его)
            await bot.send_document(chat_id=ADMIN_ID, document=FSInputFile(temp_file_name), caption=manager_message, parse_mode="HTML")
            os.remove(temp_file_name)
        else:
            # Отправляем файл по его Telegram file_id (если ИИ был недоступен или сбойнул до скачивания)
            await bot.send_document(chat_id=ADMIN_ID, document=file_id, caption=manager_message, parse_mode="HTML")
            
        await message.answer(f"✅ <b>Отчет по макету готов.</b>\nВаш заказ и макет отправлены менеджеру.", parse_mode="HTML")
    except Exception as e:
        logging.error(f"Sending to manager error: {e}")
        await message.answer("❌ Ошибка отправки заказа.")

# --- СТЕЙТЫ ---
class UserState(StatesGroup):
    default = State()
    ai_consultation = State()
    manager_chat = State()
    awaiting_design = State() 


# --- КЛАВИАТУРА ---
def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📄 Прайс-лист")
    builder.button(text="🖨 Сделать заказ")
    builder.button(text="📍 Контакты")
    builder.button(text="❓ Требования")
    builder.button(text="🧠 ИИ-консультант")
    builder.button(text="👨‍💼 Менеджер")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# --- ХЭНДЛЕРЫ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.set_state(UserState.default)
    await message.answer("Привет! Я бот типографии Nuvera.", reply_markup=get_main_keyboard())

@dp.message(F.text == "📄 Прайс-лист", UserState.default)
async def show_prices(message: types.Message):
    if os.path.exists("price_list.pdf"):
        await message.answer_document(FSInputFile("price_list.pdf"), caption="Актуальный прайс.")
    else:
        await message.answer("Прайс-лист уточняйте у менеджера.")

@dp.message(F.text == "📍 Контакты", UserState.default)
async def show_contacts(message: types.Message):
    await message.answer("<b>Адрес:</b> Юрово-Завальная, 15", parse_mode="HTML")

@dp.message(F.text == "❓ Требования", UserState.default)
async def show_requirements(message: types.Message):
    if os.path.exists("requirements.pdf"):
        await message.answer_document(FSInputFile("requirements.pdf"), caption="Требования к макетам.")
    else:
        await message.answer("Требования: CMYK, 300dpi, вылеты 2мм.")


# --- РЕЖИМ СДЕЛАТЬ ЗАКАЗ ---

@dp.message(F.text == "🖨 Сделать заказ", UserState.default)
async def start_order(message: types.Message, state: FSMContext): 
    await state.set_state(UserState.awaiting_design) 
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Отмена заказа")
    await message.answer(
        "Прикрепите файл макета (PDF, JPG, PNG). "
        "Для отмены нажмите '❌ Отмена заказа'.",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@dp.message(F.document, UserState.awaiting_design)
async def handle_document(message: types.Message, state: FSMContext):
    await process_design_file_and_send_to_manager(bot, gemini_client, tech_requirements_gemini_file, message.document.file_id, message.document.file_name, message)
    await state.set_state(UserState.default) 
    await message.answer("✅ Заказ оформлен. Вы вернулись в главное меню.", reply_markup=get_main_keyboard())


@dp.message(F.photo, UserState.awaiting_design)
async def handle_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_name = f"photo_{photo.file_id}.jpg" 
    await process_design_file_and_send_to_manager(bot, gemini_client, tech_requirements_gemini_file, photo.file_id, file_name, message)
    await state.set_state(UserState.default) 
    await message.answer("✅ Заказ оформлен. Вы вернулись в главное меню.", reply_markup=get_main_keyboard())


@dp.message(F.text == "❌ Отмена заказа", UserState.awaiting_design)
async def cancel_order(message: types.Message, state: FSMContext):
    await state.set_state(UserState.default)
    await message.answer("Заказ отменен. Вы вернулись в главное меню.", reply_markup=get_main_keyboard())


# FALLBACK-ХЭНДЛЕР ДЛЯ РЕЖИМА ОЖИДАНИЯ МАКЕТА
@dp.message(UserState.awaiting_design)
async def handle_wrong_input(message: types.Message):
    if message.text in ["/start", "/stop_ai", "/stop_manager"]: return
    await message.answer("Пожалуйста, прикрепите файл макета. Для отмены нажмите '❌ Отмена заказа'.")


# --- МЕНЕДЖЕР ---
@dp.message(F.text == "👨‍💼 Менеджер", UserState.default)
async def start_manager_chat(message: types.Message, state: FSMContext):
    await state.set_state(UserState.manager_chat)
    await message.answer("Напишите ваш вопрос менеджеру.", reply_markup=ReplyKeyboardRemove())

@dp.message(Command("stop_manager"), UserState.manager_chat)
async def cmd_manager_stop(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserState.default)
    await message.answer("Вы вернулись в меню.", reply_markup=get_main_keyboard())

@dp.message(UserState.manager_chat, F.text)
async def handle_manager_message(message: types.Message):
    username = f"@{message.from_user.username}" if message.from_user.username else "Без ника"
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=f"📩 <b>Сообщение менеджеру</b> от {username}:\n{message.text}", parse_mode="HTML")
        await message.answer("✅ Отправлено.")
    except:
        await message.answer("Ошибка отправки.")

# --- ИИ (GEMINI) ---
@dp.message(F.text == "🧠 ИИ-консультант", UserState.default)
async def start_ai_mode_button(message: types.Message, state: FSMContext):
    if not gemini_client:
        await message.answer("❌ ИИ временно недоступен (ошибка соединения). Попробуйте позже.")
        return

    price_list_json_string = get_price_json_string()

    # Добавление инструкции, как использовать команду /stop_ai
    system_prompt = (
        "Ты — ведущий технолог-полиграфист и автоматизированная система консультаций студии nuvera. "
        "Твой тон: деловой, профессиональный. Используй только данные из предоставленных файлов и JSON. "
        "Цены указаны в белорусских рублях (BYN) с НДС. "
        "ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА РАСЧЕТА:\n"
        "1. Расчет стоимости печати производи на основе таблицы в JSON (Черно-белая и Цветная печать).\n"
        "2. Цена печати всегда рассчитывается по формату листа SRA3 (320x450 мм).\n"
        "3. В SRA3 вмещается: А4=2 шт, А5=4 шт, А6=8 шт.\n"
        "4. К цене печати всегда прибавляй стоимость послепечатной работы: Резка листа РЕЗ (0,36 BYN).\n"
        "5. Если вопрос сложный, тираж свыше 500 листов или требуется индивидуальный расчет, используй фразу [СМЕНЕДЖЕРОМ]."
        f"\n\n--- АКТУАЛЬНЫЙ ПРАЙС-ЛИСТ (JSON) ---\n{price_list_json_string}\n\n--- КОНЕЦ ПРАЙС-ЛИСТА ---"
    )
    
    try:
        chat_session = gemini_client.chats.create(
            model=GEMINI_MODEL,
            config=genai.types.GenerateContentConfig(system_instruction=system_prompt)
        )
        
        initial_history = ["Инициализация чата. Прайс загружен в промпт."]
        if tech_requirements_gemini_file:
            initial_history.append(tech_requirements_gemini_file)
            initial_history.append("Технические требования также приложены.")

        chat_session.send_message(initial_history)
        
        await state.update_data(ai_chat_session=chat_session)
        await state.set_state(UserState.ai_consultation)
        
        # Добавляем инструкцию, как выйти
        await message.answer("🧠 ИИ-консультант слушает. Задавайте вопросы.\nДля выхода используйте команду /stop_ai.", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        error_text = f"⚠️ <b>НЕ УДАЛОСЬ ЗАПУСТИТЬ ИИ:</b>\n{str(e)}"
        await message.answer(error_text, parse_mode="HTML")
        logging.error(f"AI START ERROR: {e}")

@dp.message(Command("stop_ai"), UserState.ai_consultation)
async def cmd_ai_stop(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserState.default)
    await message.answer("ИИ отключен. Вы вернулись в главное меню.", reply_markup=get_main_keyboard())

@dp.message(UserState.ai_consultation, F.text)
async def handle_ai_message_gemini(message: types.Message, state: FSMContext):
    if message.text in ["/stop_ai", "/start"]: 
        # Если пользователь ввел команду /stop_ai, она будет обработана выше
        return

    data = await state.get_data()
    chat_session = data.get('ai_chat_session')
    
    if not chat_session:
        await message.answer("Ошибка сессии. Перезапустите ИИ.")
        await state.set_state(UserState.default)
        return

    msg = await message.answer("💡 Думаю...")
    
    try:
        response = chat_session.send_message(message.text)
        text = response.text.replace("[СМЕНЕДЖЕРОМ]", "").strip()
        if "[СМЕНЕДЖЕРОМ]" in response.text:
            text += "\n\n⚠️ <b>Рекомендую обратиться к менеджеру.</b>"
            
        await bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=text, parse_mode="HTML")
    except Exception as e:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="Ошибка соединения с ИИ. Попробуйте снова или используйте /stop_ai.")
        logging.error(f"GEMINI CHAT ERROR: {e}")

# FALLBACK
@dp.message() 
async def handle_unrecognized_input(message: types.Message):
    # Пропускаем сообщения, которые могут быть кнопками
    if message.text in ["📄 Прайс-лист", "🖨 Сделать заказ", "📍 Контакты", "❓ Требования", "🧠 ИИ-консультант", "👨‍💼 Менеджер"]: return
    await message.answer("❌ <b>Неизвестная команда.</b> Выберите действие в меню.", parse_mode="HTML", reply_markup=get_main_keyboard())

# --- ГЛАВНЫЙ ЗАПУСК ---
async def main():
    await on_startup() 
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt: pass
    except Exception as e: 
        logging.error(f"Fatal error in main: {e}")