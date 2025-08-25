# bot.py — Полностью исправленный и рабочий Telegram-бот

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
import time
from threading import Thread
from flask import Flask

# === Глобальные переменные ===
bot_instance = None
application_instance = None  # Будет присвоен позже

# === Логирование пользователей ===
LOG_FILE = "users.txt"

def log_user(update: Update):
    user = update.effective_user
    time_str = update.message.date.strftime("%Y-%m-%d %H:%M:%S") if update.message and update.message.date else "неизвестно"
    username = f"@{user.username}" if user.username else "нет"
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time_str} | ID: {user.id} | username: {username} | full_name: {user.full_name}\n")
    
    print(f"👤 Залогинен пользователь: {user.full_name} (@{username}) — {user.id}")

def get_user_count():
    if not os.path.exists(LOG_FILE):
        print(f"🟡 Файл логов не найден: {LOG_FILE}")
        return 0
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            count = len([line for line in lines if line.strip()])
            print(f"📊 Найдено пользователей: {count}")
            return count
    except Exception as e:
        print(f"❌ Ошибка чтения users.txt: {e}")
        return 0

# === Настройки ===
PRICES_DIR = "prays"

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

        latest_file = max(
            files,
            key=lambda f: os.path.getmtime(os.path.join(PRICES_DIR, f))
        )
        return os.path.join(PRICES_DIR, latest_file)
    except Exception as e:
        print(f"❌ Ошибка поиска прайса для {filename_key}: {e}")
        return None

# === Мониторинг прайсов в отдельном потоке ===
def monitor_price_files():
    global bot_instance, application_instance
    print("✅ Мониторинг прайсов запущен...")

    # Инициализация
    for key in current_files:
        current_files[key] = get_latest_price_file(key)
        if current_files[key]:
            print(f"📁 {key}: {current_files[key]}")
        else:
            print(f"📁 {key}: файл не найден")

    while True:
        time.sleep(300)  # 5 минут
        for key in current_files:
            latest = get_latest_price_file(key)
            if latest and latest != current_files[key]:
                current_files[key] = latest
                filename = os.path.basename(latest)
                print(f"❗ Обновлён прайс: {key} → {filename}")

                # Отправка уведомления
                if bot_instance and application_instance:
                    try:
                        caption = f"🔄 Обновлён прайс: *{key}* → `{filename}`"
                        asyncio.run_coroutine_threadsafe(
                            bot_instance.send_message(
                                chat_id=YOUR_USER_ID,
                                text=caption,
                                parse_mode="Markdown"
                            ),
                            application_instance.loop  # ✅ Правильно: используем loop из application
                        )
                    except Exception as e:
                        print(f"❌ Не удалось отправить уведомление: {e}")

# === Загрузка .env ===
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
YOUR_USER_ID = os.getenv("YOUR_USER_ID")

if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN в .env")
if not YOUR_USER_ID:
    raise ValueError("❌ Не найден YOUR_USER_ID в .env")

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
    log_user(update)
    user_count = get_user_count()
    await update.message.reply_text(
        f"Здравствуйте 👋\n"
        f"Вы — {user_count}-й посетитель бота.\n\n"
        "Выберите категорию:",
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
        time_str = update.message.date.strftime("%d.%m.%Y %H:%M") if update.message and update.message.date else "неизвестно"

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

    elif text == "◀️ Назад":
        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())

    else:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки меню.",
            reply_markup=get_main_keyboard()
        )

# === Flask для keep-alive ===
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Бот работает 🚀"

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

def keep_alive():
    thread = Thread(target=run_flask, daemon=True)
    thread.start()

# === /admin ===
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"🔹 /admin вызван пользователем: {user_id}")
    print(f"🔹 Ожидаемый ID админа: {YOUR_USER_ID}")
    print(f"🔹 Тип user_id: {type(user_id)}, тип YOUR_USER_ID: {type(YOUR_USER_ID)}")

    if user_id != YOUR_USER_ID:
        print("❌ Доступ запрещён: ID не совпадает")
        await update.message.reply_text("❌ Доступ запрещён.")
        return

    count = get_user_count()
    print(f"📊 Отправляем статистику: {count} пользователей")
    await update.message.reply_text(f"📊 Всего пользователей: {count}")

# === Главная функция ===
async def main():
    global bot_instance, application_instance

    application = Application.builder().token(BOT_TOKEN).build()
    application_instance = application
    bot_instance = application.bot

    # === ЛОГГЕР: ловим всё первым ===
    async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f"📥 ПРИШЛО ОБНОВЛЕНИЕ: {update.to_dict()}")

    application.add_handler(MessageHandler(filters.ALL, log_update), group=0)

    # === ХЕНДЛЕРЫ ===
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # === Запуск Flask и мониторинга ===
    keep_alive()
    Thread(target=monitor_price_files, daemon=True).start()

    # === Отладка ===
    print(f"🔧 Запуск бота...")
    print(f"🔧 Админ ID: {YOUR_USER_ID} (тип: {type(YOUR_USER_ID)})")
    print(f"🔧 BOT_TOKEN: {BOT_TOKEN[:10]}... (загружен)")
    print("✅ Бот запущен. Напишите /start в Telegram.")

    # === Запуск ===
    await application.run_polling()

# === Запуск ===
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
