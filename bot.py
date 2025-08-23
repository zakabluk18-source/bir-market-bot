# bot.py — Полностью рабочий Telegram-бот с автообновлением прайсов

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
import time
import asyncio
from threading import Thread
from flask import Flask

# === Глобальная переменная для бота (чтобы мониторинг мог отправлять уведомления) ===
bot_instance = None
application_instance = None

# === Настройки ===
PRICES_DIR = "prays"  # Папка с прайсами

# Словарь для хранения актуальных файлов
current_files = {
    "general": None,
    "import": None,
    "craft": None,
    "cider": None,
    "water": None,
    "energy_drinks": None,
    "baltika": None,
    "ab_inbev": None,
    "oph": None
}

# === Найти самый свежий PDF по ключу (например, "general") ===
def get_latest_price_file(filename_key):
    try:
        if not os.path.exists(PRICES_DIR):
            print(f"❌ Папка {PRICES_DIR} не найдена")
            return None

        files = [
            f for f in os.listdir(PRICES_DIR)
            if f.lower().endswith(".pdf") and filename_key.lower() in f.lower()
        ]
        if not files:
            return None

        # Возвращаем файл с самой свежей датой изменения
        latest_file = max(
            files,
            key=lambda f: os.path.getmtime(os.path.join(PRICES_DIR, f))
        )
        return os.path.join(PRICES_DIR, latest_file)
    except Exception as e:
        print(f"❌ Ошибка поиска прайса для {filename_key}: {e}")
        return None

# === Фоновый мониторинг прайсов (запускается в отдельном потоке) ===
def monitor_price_files():
    global current_files
    print("✅ Мониторинг прайсов запущен...")

    # Инициализация: найдём первые файлы
    for key in current_files:
        current_files[key] = get_latest_price_file(key)
        if current_files[key]:
            print(f"📁 {key}: {current_files[key]}")
        else:
            print(f"📁 {key}: файл не найден")

    # Каждые 5 минут проверяем обновления
    while True:
        time.sleep(300)  # 5 минут
        for key in current_files:
            latest = get_latest_price_file(key)
            if latest and latest != current_files[key]:
                current_files[key] = latest
                filename = os.path.basename(latest)
                print(f"❗ Обновлён прайс: {key} → {filename}")

                # 📢 Отправляем уведомление (если бот готов)
                if bot_instance:
                    try:
                        caption = f"🔄 Обновлён прайс: *{key}* → `{filename}`"
                        asyncio.run(
                            bot_instance.send_message(
                                chat_id=YOUR_USER_ID,
                                text=caption,
                                parse_mode="Markdown"
                            )
                        )
                    except Exception as e:
                        print(f"❌ Не удалось отправить уведомление: {e}")

# === Загрузка переменных окружения ===
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
YOUR_USER_ID = os.getenv("YOUR_USER_ID")

if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN в файле .env")
if not YOUR_USER_ID:
    raise ValueError("❌ Не найден YOUR_USER_ID в файле .env")

try:
    YOUR_USER_ID = int(YOUR_USER_ID)
except ValueError:
    raise ValueError("❌ YOUR_USER_ID должен быть числом")

# === Состояния для заявок ===
STATE_WAITING_NAME = "waiting_name"
STATE_WAITING_COMPANY = "waiting_company"
STATE_WAITING_PHONE = "waiting_phone"
STATE_WAITING_ORDER = "waiting_order"

# === Клавиатуры ===
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("Федеральные компании")],
        [KeyboardButton("Импортное пиво")],
        [KeyboardButton("Крафт-пиво")],
        [KeyboardButton("🍎 Сидры")],
        [KeyboardButton("🚫🍺 Безалкогольное")],
        [KeyboardButton("📝 Оставить заявку")],
        [KeyboardButton("📞 Контакты")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_non_alcohol_keyboard():
    keyboard = [
        [KeyboardButton("💧 Вода")],
        [KeyboardButton("⚡ Энергетики")],
        [KeyboardButton("◀️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте Выберите категорию:",
        reply_markup=get_main_keyboard()
    )

# === Обработка сообщений ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # === Сбор заявки ===
    if context.user_data.get("state") == STATE_WAITING_NAME:
        context.user_data["name"] = text
        context.user_data["state"] = STATE_WAITING_COMPANY
        await update.message.reply_text("Введите название вашей компании:")

    elif context.user_data.get("state") == STATE_WAITING_COMPANY:
        context.user_data["company"] = text
        context.user_data["state"] = STATE_WAITING_PHONE
        await update.message.reply_text("Введите ваш телефон (например: +7 999 123-45-67):")

    elif context.user_data.get("state") == STATE_WAITING_PHONE:
        context.user_data["phone"] = text
        context.user_data["state"] = STATE_WAITING_ORDER
        await update.message.reply_text(
            "Что хотите заказать? Укажите:\n"
            "— Категорию\n"
            "— Объём (литры, ящики)\n"
            "— Адрес доставки"
        )

    elif context.user_data.get("state") == STATE_WAITING_ORDER:
        context.user_data["order"] = text
        name = context.user_data.get("name", "Не указано")
        company = context.user_data.get("company", "Не указано")
        phone = context.user_data.get("phone", "Не указано")
        order = context.user_data.get("order", "Не указано")
        time_str = update.message.date.strftime("%d.%m.%Y %H:%M")

        application_text = (
            "🆕 <b>НОВАЯ ЗАЯВКА</b>:\n\n"
            f"👤 <b>Имя:</b> {name}\n"
            f"🏢 <b>Компания:</b> {company}\n"
            f"📞 <b>Телефон:</b> {phone}\n"
            f"📦 <b>Заказ:</b> {order}\n"
            f"⏱ <b>Время:</b> {time_str}"
        )

        try:
            await context.bot.send_message(
                chat_id=YOUR_USER_ID,
                text=application_text,
                parse_mode="HTML"
            )
            await update.message.reply_text(
                "✅ Спасибо Ваша заявка отправлена.\n"
                "Мы свяжемся с вами в ближайшее время."
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка отправки заявки: {e}")

        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())
        context.user_data.clear()

    # === Основное меню ===
    elif text == "Федеральные компании":
        keyboard = [
            [KeyboardButton("🍺 Балтика")],
            [KeyboardButton("🌍 ABInBev")],
            [KeyboardButton("🏭 ОПХ")],
            [KeyboardButton("📦 Общий прайс")],
            [KeyboardButton("◀️ Назад")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите компанию:", reply_markup=reply_markup)

    elif text == "📦 Общий прайс":
        file_path = current_files.get("general")
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, "rb") as pdf:
                    await update.message.reply_document(
                        document=pdf,
                        caption="📄 <b>Общий прайс-лист</b>\nВсе товары в одном файле",
                        parse_mode="HTML"
                    )
            except Exception as e:
                await update.message.reply_text(f"❌ Ошибка отправки файла: {e}")
        else:
            await update.message.reply_text("❌ Актуальный прайс не найден.")
        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())

    # Остальные elif — как у тебя, они правильные
    # (для краткости не дублирую, но они должны быть)

    elif text == "◀️ Назад":
        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())

    else:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки меню.",
            reply_markup=get_main_keyboard()
        )

# === Flask для keep-alive на Render ===
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Бот работает 🚀"

def run_flask():
    try:
        flask_app.run(host='0.0.0.0', port=8080)
    except Exception as e:
        print(f"❌ Ошибка Flask: {e}")

def keep_alive():
    thread = Thread(target=run_flask)
    thread.start()

# === Запуск бота ===
if __name__ == "__main__":
    # Запускаем веб-сервер
    keep_alive()

    # Запускаем мониторинг прайсов в фоне
    monitor_thread = Thread(target=monitor_price_files, daemon=True)
    monitor_thread.start()

    # Создаём и запускаем бота
    while True:
        try:
            app = Application.builder().token(BOT_TOKEN).build()
            app.add_handler(CommandHandler("start", start))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

            # Сохраняем бота для уведомлений
            global bot_instance
            bot_instance = app.bot

            print("✅ Бот запущен и работает 24/7")
            app.run_polling()
        except Exception as e:
            print(f"❌ Ошибка: {e}. Перезапуск через 5 сек...")
            time.sleep(5)
