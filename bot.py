from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

TOKEN = os.getenv("TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# === МЕНЮ ===
def get_main_menu():
    keyboard = [
        ["🍺 Прайсы"],
        ["📞 Связаться с менеджером"],
        ["ℹ️ Помощь"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_category_menu():
    keyboard = [
        ["🍺 Пиво"],
        ["🍎 Сидр"],
        ["🥤 Безалкогольные"],
        ["⚡ Энергетики"],
        ["🔙 Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_beer_menu():
    keyboard = [
        ["Крупные бренды"],
        ["Локальные пивоварни"],
        ["Сезонное пиво"],
        ["🔙 Назад в Прайсы"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cider_menu():
    keyboard = [
        ["Российский сидр"],
        ["Импортный сидр"],
        ["🔙 Назад в Прайсы"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_soft_menu():
    keyboard = [
        ["Лимонады"],
        ["Вода"],
        ["🔙 Назад в Прайсы"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_energy_menu():
    keyboard = [
        ["Крупные бренды"],
        ["Локальные/новинки"],
        ["🔙 Назад в Прайсы"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в *Бирмаркет НСК* 🍻\n\n"
        "Выберите действие в меню:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# === ОБРАБОТКА КНОПОК ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    print(f"Нажато: {text}")

    if text == "🍺 Прайсы":
        await update.message.reply_text("Выберите категорию:", reply_markup=get_category_menu())

    elif text == "📞 Связаться с менеджером":
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔔 Новый запрос на связь!\nОт: {update.effective_user.full_name}\nЮзернейм: @{update.effective_user.username}"
            )
        except Exception as e:
            print(f"Ошибка отправки менеджеру: {e}")

        await update.message.reply_text(
            "Свяжитесь с менеджером:\n\n"
            "📱 @your_manager\n"
            "📞 +7 (913) XXX-XX-XX\n\n"
            "Мы уже знаем — ответим за 15 минут ⏳"
        )

    elif text == "ℹ️ Помощь":
        await update.message.reply_text(
            "ℹ️ *Помощь*\n\n"
            "Бот помогает:\n"
            "• Скачать прайсы\n"
            "• Связаться с менеджером\n\n"
            "Если что-то не работает — пишите @your_manager",
            parse_mode="Markdown"
        )

    elif text == "🔙 Назад":
        await update.message.reply_text("Главное меню:", reply_markup=get_main_menu())

    elif text == "🔙 Назад в Прайсы":
        await update.message.reply_text("Выберите категорию:", reply_markup=get_category_menu())

    # === Пиво ===
    elif text == "🍺 Пиво":
        await update.message.reply_text("Выберите тип:", reply_markup=get_beer_menu())

    elif text == "Крупные бренды":
        await update.message.reply_document(document=open("files/beer_large.pdf", "rb"))
    elif text == "Локальные пивоварни":
        await update.message.reply_document(document=open("files/beer_local.pdf", "rb"))
    elif text == "Сезонное пиво":
        await update.message.reply_document(document=open("files/beer_seasonal.pdf", "rb"))

    # === Сидр ===
    elif text == "🍎 Сидр":
        await update.message.reply_text("Выберите тип:", reply_markup=get_cider_menu())

    elif text == "Российский сидр":
        await update.message.reply_document(document=open("files/cider_russia.pdf", "rb"))
    elif text == "Импортный сидр":
        await update.message.reply_document(document=open("files/cider_import.pdf", "rb"))

    # === Безалкогольные ===
    elif text == "🥤 Безалкогольные":
        await update.message.reply_text("Выберите:", reply_markup=get_soft_menu())

    elif text == "Лимонады":
        await update.message.reply_document(document=open("files/soft_lemonade.pdf", "rb"))
    elif text == "Вода":
        await update.message.reply_document(document=open("files/soft_water.pdf", "rb"))

    # === Энергетики ===
    elif text == "⚡ Энергетики":
        await update.message.reply_text("Выберите:", reply_markup=get_energy_menu())

    elif text == "Крупные бренды":
        await update.message.reply_document(document=open("files/energy_large.pdf", "rb"))
    elif text == "Локальные/новинки":
        await update.message.reply_document(document=open("files/energy_new.pdf", "rb"))

# === ЗАПУСК ===
if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен. Нажмите /start в Telegram.")
    application.run_polling()
