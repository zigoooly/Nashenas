import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from database import init_db, get_nickname, set_nickname

BOT_TOKEN = "8574592475:AAFfarKG2o8OzBtykXr4bzFPolHVgQEBbKc"
ADMIN_ID = 6474515118
GROUP_ID = -1003614589024
PORT = int(os.environ.get("PORT", 8080))

init_db()

WAIT_NICK = set()
WAIT_NEW_NICK = set()

def keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ تغییر لقب", callback_data="change_nick")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    nick = get_nickname(uid)

    if nick:
        await update.message.reply_text(
            f"🕶 لقب فعلی تو: *{nick}*",
            parse_mode="Markdown",
            reply_markup=keyboard()
        )
    else:
        WAIT_NICK.add(uid)
        await update.message.reply_text(
            "سلام 👋\n\n"
            "✍️ یه لقب ناشناس برای خودت بفرست",
            parse_mode="Markdown"
        )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if uid in WAIT_NICK:
        WAIT_NICK.remove(uid)
        set_nickname(uid, text)
        await update.message.reply_text(
            f"✅ لقبت ثبت شد: *{text}*",
            parse_mode="Markdown",
            reply_markup=keyboard()
        )
        return

    if uid in WAIT_NEW_NICK:
        WAIT_NEW_NICK.remove(uid)
        set_nickname(uid, text)
        await update.message.reply_text(
            f"✏️ لقبت تغییر کرد: *{text}*",
            parse_mode="Markdown",
            reply_markup=keyboard()
        )
        return

    nick = get_nickname(uid)
    if not nick:
        WAIT_NICK.add(uid)
        await update.message.reply_text("اول یه لقب بفرست ✍️")
        return

    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=uid,
        message_id=update.message.message_id
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🕶 لقب: {nick}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تأیید", callback_data=f"ok|{uid}|{text}"),
                InlineKeyboardButton("❌ رد", callback_data=f"no|{uid}")
            ]
        ])
    )

    await update.message.reply_text("⏳ ارسال شد برای بررسی")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data.split("|")

    if data[0] == "change_nick":
        WAIT_NEW_NICK.add(q.from_user.id)
        await q.message.reply_text("✍️ لقب جدید رو بفرست")
        return

    uid = int(data[1])

    if data[0] == "ok":
        text = data[2]
        nick = get_nickname(uid)

        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"🕶 {nick} گفت:\n{text}"
        )
        await context.bot.send_message(uid, "✅ پیامت منتشر شد")
        await q.edit_message_text("✅ ارسال شد")

    else:
        await context.bot.send_message(uid, "❌ پیامت رد شد")
        await q.edit_message_text("❌ رد شد")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(CallbackQueryHandler(buttons))

    # 🔥 وبهوک واقعی
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url="https://nashenas-71cn.onrender.com/webhook",
        url_path="webhook"
    )

if __name__ == "__main__":
    main()
