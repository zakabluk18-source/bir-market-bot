# bot.py
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from threading import Thread
import asyncio

# === ТОКЕН И АДМИН ===
TOKEN = os.getenv("TOKEN", "8475405331:AAH-kBpTIX6P-f3o3OwUAecniiUYQtZTt1E")
ADMIN_ID = int(os.getenv("ADMIN_ID", "50420118"))

# === КЛАВИАТУРА "ГЛАВНОЕ МЕНЮ" ===
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# === КОМАНДА /start ===
async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("Федеральные компании", callback_data="federal")],
        [InlineKeyboardButton("Импортное пиво", callback_data="import")],
        [InlineKeyboardButton("Крафт-пиво", callback_data="craft")],
        [InlineKeyboardButton("Контакты", callback_data="contacts")]
    ]
    await update.message.reply_text("Выберите категорию:", reply_markup=InlineKeyboardMarkup(keyboard))

# === ОБРАБОТЧИК КНОПОК ===
async def button(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "federal":
        keyboard = [
            [InlineKeyboardButton("🍺 Балтика", callback_data="baltika")],
            [InlineKeyboardButton("🌍 ABInBev", callback_data="ab_inbev")],
            [InlineKeyboardButton("🏭 ОПХ", callback_data="oph")],
            [InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]
        ]
        await query.edit_message_text("Выберите компанию:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "baltika":
        with open("prays/baltika.pdf", "rb") as pdf:
            await query.message.reply_document(pdf, caption="Прайс-лист: Балтика")
        await query.message.reply_text("Главное меню:", reply_markup=main_menu_keyboard())

    elif query.data == "ab_inbev":
        with open("prays/ab_inbev.pdf", "rb") as pdf:
            await query.message.reply_document(pdf, caption="Прайс-лист: ABInBev")
        await query.message.reply_text("Главное меню:", reply_markup=main_menu_keyboard())

    elif query.data == "oph":
        with open("prays/oph.pdf", "rb") as pdf:
            await query.message.reply_document(pdf, caption="Прайс-лист: ОПХ")
        await query.message.reply_text("Главное меню:", reply_markup=main_menu_keyboard())

    elif query.data == "import":
        with open("prays/import.pdf", "rb") as pdf:
            await query.message.reply_document(pdf, caption="Прайс-лист: Импортное пиво")
        await query.message.reply_text("Главное меню:", reply_markup=main_menu_keyboard())

    elif query.data == "craft":
        with open("prays/craft.pdf", "rb") as pdf:
            await query.message.reply_document(pdf, caption="Прайс-лист: Крафт-пиво")
        await query.message.reply_text("Главное меню:", reply_markup=main_menu_keyboard())

    elif query.data == "contacts":
        await query.edit_message_text(
            "Свяжитесь с нами:\n📞 +7 (999) 123-45-67\n📧 zakabluk18@yandex.ru",
            reply_markup=main_menu_keyboard()
        )

    elif query.data == "main_menu":
        keyboard = [
            [InlineKeyboardButton("Федеральные компании", callback_data="federal")],
            [InlineKeyboardButton("Импортное пиво", callback_data="import")],
            [InlineKeyboardButton("Крафт-пиво", callback_data="craft")],
            [InlineKeyboardButton("Контакты", callback_data="contacts")]
        ]
        await query.edit_message_text("Выберите категорию:", reply_markup=InlineKeyboardMarkup(keyboard))


# === ЗАПУСК БОТА И ВЕБ-СЕРВЕР ДЛЯ RENDER ===
if __name__ == "__main__":
    # Создаём приложение
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # === ЗАПУСК БОТА В ОТДЕЛЬНОМ ПОТОКЕ ===
    def run_bot():
        asyncio.set_event_loop(asyncio.new_event_loop())
        application.run_polling(allowed_updates=[], stop_signals=None)

    bot_thread = Thread(target=run_bot)
    bot_thread.start()

    # === ВЕБ-СЕРВЕР ДЛЯ RENDER (здоровье сервиса) ===
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Bot is alive and running on Render!")

    port = int(os.environ.get("PORT", 8000))

    def run_server():
        server = HTTPServer(("", port), HealthCheckHandler)
        print(f"✅ Веб-сервер запущен на порту {port}")
        server.serve_forever()

    server_thread = Thread(target=run_server)
    server_thread.start()
