# bot.py — Полностью рабочий бот с заявками, прайсами и меню

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os

# Загружаем переменные из .env
load_dotenv()

# Получаем токен и ID
BOT_TOKEN = os.getenv("BOT_TOKEN")
YOUR_USER_ID = int(os.getenv("YOUR_USER_ID"))

if not BOT_TOKEN:
    raise ValueError("Не найден BOT_TOKEN в файле .env")
if not YOUR_USER_ID:
    raise ValueError("Не найден YOUR_USER_ID в файле .env")

# Состояния для сбора заявки
STATE_WAITING_NAME = "waiting_name"
STATE_WAITING_COMPANY = "waiting_company"
STATE_WAITING_PHONE = "waiting_phone"
STATE_WAITING_ORDER = "waiting_order"


# Главная клавиатура
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
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


# Клавиатура для безалкогольного
def get_non_alcohol_keyboard():
    keyboard = [
        [KeyboardButton("💧 Вода")],
        [KeyboardButton("⚡ Энергетики")],
        [KeyboardButton("◀️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте Выберите категорию:",
        reply_markup=get_main_keyboard()
    )


# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Если идёт сбор заявки — обрабатываем по шагам
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

        # Формируем заявку
        name = context.user_data.get("name", "Не указано")
        company = context.user_data.get("company", "Не указано")
        phone = context.user_data.get("phone", "Не указано")
        order = context.user_data.get("order", "Не указано")
        time = update.message.date.strftime("%d.%m.%Y %H:%M")

        application_text = (
            "🆕 <b>НОВАЯ ЗАЯВКА</b>:\n\n"
            f"👤 <b>Имя:</b> {name}\n"
            f"🏢 <b>Компания:</b> {company}\n"
            f"📞 <b>Телефон:</b> {phone}\n"
            f"📦 <b>Заказ:</b> {order}\n"
            f"⏱ <b>Время:</b> {time}"
        )

        # Отправляем тебе в личку
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

        # Возвращаем в главное меню
        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())
        context.user_data.clear()

    # Основное меню
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
        try:
            with open("prays/general.pdf", "rb") as pdf:
                await update.message.reply_document(pdf, caption="📄 <b>Общий прайс-лист</b>\nВсе товары в одном файле", parse_mode="HTML")
        except FileNotFoundError:
            await update.message.reply_text("❌ Файл prays/general.pdf не найден.")
        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())

    elif text == "Импортное пиво":
        try:
            with open("prays/import.pdf", "rb") as pdf:
                await update.message.reply_document(pdf, caption="📄 Прайс-лист: Импортное пиво")
        except FileNotFoundError:
            await update.message.reply_text("❌ Файл prays/import.pdf не найден.")
        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())

    elif text == "Крафт-пиво":
        try:
            with open("prays/craft.pdf", "rb") as pdf:
                await update.message.reply_document(pdf, caption="📄 Прайс-лист: Крафт-пиво")
        except FileNotFoundError:
            await update.message.reply_text("❌ Файл prays/craft.pdf не найден.")
        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())

    elif text == "🍎 Сидры":
        try:
            with open("prays/cider.pdf", "rb") as pdf:
                await update.message.reply_document(pdf, caption="📄 Прайс-лист: Сидры")
        except FileNotFoundError:
            await update.message.reply_text("❌ Файл prays/cider.pdf не найден.")
        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())

    elif text == "🚫🍺 Безалкогольное":
        await update.message.reply_text("Выберите подкатегорию:", reply_markup=get_non_alcohol_keyboard())

    elif text == "💧 Вода":
        try:
            with open("prays/water.pdf", "rb") as pdf:
                await update.message.reply_document(pdf, caption="📄 Прайс-лист: Вода")
        except FileNotFoundError:
            await update.message.reply_text("❌ Файл prays/water.pdf не найден.")
        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())

    elif text == "⚡ Энергетики":
        try:
            with open("prays/energy_drinks.pdf", "rb") as pdf:
                await update.message.reply_document(pdf, caption="📄 Прайс-лист: Энергетики")
        except FileNotFoundError:
            await update.message.reply_text("❌ Файл prays/energy_drinks.pdf не найден.")
        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())

    elif text == "📝 Оставить заявку":
        context.user_data["state"] = STATE_WAITING_NAME
        await update.message.reply_text("Введите ваше имя:")

    elif text == "Контакты":
        await update.message.reply_text(
            "Свяжитесь с нами:\n"
            "📞 +7 (999) 123-45-67\n"
            "📧 zakabluk18@yandex.ru",
            reply_markup=get_main_keyboard()
        )

    elif text == "🍺 Балтика":
        try:
            with open("prays/baltika.pdf", "rb") as pdf:
                await update.message.reply_document(pdf, caption="📄 Прайс-лист: Балтика")
        except FileNotFoundError:
            await update.message.reply_text("❌ Файл prays/baltika.pdf не найден.")
        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())

    elif text == "🌍 ABInBev":
        try:
            with open("prays/ab_inbev.pdf", "rb") as pdf:
                await update.message.reply_document(pdf, caption="📄 Прайс-лист: ABInBev")
        except FileNotFoundError:
            await update.message.reply_text("❌ Файл prays/ab_inbev.pdf не найден.")
        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())

    elif text == "🏭 ОПХ":
        try:
            with open("prays/oph.pdf", "rb") as pdf:
                await update.message.reply_document(pdf, caption="📄 Прайс-лист: ОПХ")
        except FileNotFoundError:
            await update.message.reply_text("❌ Файл prays/oph.pdf не найден.")
        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())

    elif text == "◀️ Назад":
        await update.message.reply_text("Выберите категорию:", reply_markup=get_main_keyboard())

    else:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки меню.",
            reply_markup=get_main_keyboard()
        )


# Запуск бота
if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен. Напишите /start в Telegram.")
    from flask import Flask # pyright: ignore[reportMissingImports]
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Бот работает 🚀"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Запускаем веб-сервер ДО бота
keep_alive()

# Запускаем бота
if __name__ == "__main__":
    application = Application.builder().token(BOT_TOKEN).build()
    # ... твои хендлеры ...
    application.run_polling()
    app.run_polling()
