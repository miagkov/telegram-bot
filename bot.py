import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8014448300:AAEDklIi04Kz0HzTx7CQQ_XJqfAiA6tw8CU"       # <-- сюда токен
LEADS_CHAT_ID = -1003086157203      # <-- сюда чат/канал для заявок (бот должен быть там и иметь право писать)

# валидатор телефона (очень мягкий)
PHONE_RE = re.compile(r"^\+?\d[\d\s\-()]{6,}$")

ST_NAME   = "ASK_NAME"
ST_CITY   = "ASK_CITY"
ST_PHONE  = "ASK_PHONE"
ST_DOCS   = "ASK_DOCS"
ST_DONE   = "DONE"

WELCOME_TEXT = (
    "Здравствуйте, спасибо что откликнулись на нашу вакансию!\n"
    "Ответьте на пару вопросов, чтобы наш менеджер мог связаться с Вами.\n\n"
    "Напишите Ваше *имя*:"
)

async def send_lead(context: ContextTypes.DEFAULT_TYPE, data: dict):
    text = (
        "📩 *Новая заявка*\n"
        f"• Имя: {data.get('name','-')}\n"
        f"• Город: {data.get('city','-')}\n"
        f"• Телефон: {data.get('phone','-')}\n"
        f"• Документы: {data.get('docs','-')}"
    )
    await context.bot.send_message(LEADS_CHAT_ID, text, parse_mode="Markdown")

# /start — на случай если пользователь нажал Старт
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["state"] = ST_NAME
    await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")

# /id — узнать chat_id (полезно для групп/каналов)
async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"chat_id: {update.effective_chat.id}")

# /reset — начать заново
async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["state"] = ST_NAME
    await update.message.reply_text("Начнём заново.\n\n" + WELCOME_TEXT, parse_mode="Markdown")

# Главный обработчик ЛИЧНЫХ сообщений (без команд)
async def on_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    state = context.user_data.get("state")

    # Если это первое сообщение — запускаем диалог сами
    if not state:
        context.user_data.clear()
        context.user_data["state"] = ST_NAME
        await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")
        return

    # Обработка состояний
    if state == ST_NAME:
        if len(text) < 2:
            await update.message.reply_text("Имя слишком короткое. Напишите, пожалуйста, имя полностью:")
            return
        context.user_data["name"] = text
        context.user_data["state"] = ST_CITY
        await update.message.reply_text("Из какого вы города?")
        return

    if state == ST_CITY:
        if len(text) < 2:
            await update.message.reply_text("Похоже на опечатку. Уточните, пожалуйста, город:")
            return
        context.user_data["city"] = text
        context.user_data["state"] = ST_PHONE
        await update.message.reply_text("Напишите Ваш номер телефона с кодом страны для связи Viber/WhatsApp/Telegram (например, +373...):")
        return

    if state == ST_PHONE:
        if not PHONE_RE.match(text):
            await update.message.reply_text("Похоже на неверный формат. Укажите телефон с кодом страны (например, +373...):")
            return
        context.user_data["phone"] = text
        context.user_data["state"] = ST_DOCS
        await update.message.reply_text("Какие у Вас есть документы для работы в ЕС?")
        return

    if state == ST_DOCS:
        context.user_data["docs"] = text
        context.user_data["state"] = ST_DONE

        # благодарность пользователю
        await update.message.reply_text(
            "Спасибо за Ваши ответы, ожидайте, наш менеджер свяжется с Вами в ближайшее время!"
        )

        # отправка заявки в рабочий чат/канал
        await send_lead(context, context.user_data.copy())
        return

    # Если уже завершено — позволяем начать заново простым сообщением
    if state == ST_DONE:
        context.user_data.clear()
        context.user_data["state"] = ST_NAME
        await update.message.reply_text("Начнём новую анкету.\n\n" + WELCOME_TEXT, parse_mode="Markdown")
        return

def main():
    app = Application.builder().token(TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("reset", cmd_reset))

    # ЛИЧНЫЕ сообщения — ведём диалог
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, on_private_message))

    # (по желанию можно добавить приветствие в группе для NEW_CHAT_MEMBERS)
    app.run_polling()

if __name__ == "__main__":
    main()
