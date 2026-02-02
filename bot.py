from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from database import init_db, get_nickname, set_nickname

BOT_TOKEN = "8574592475:AAFfarKG2o8OzBtykXr4bzFPolHVgQEBbKc"
ADMIN_ID = 6474515118
GROUP_ID = -1003614589024

init_db()

WAITING_FOR_NICK = set()
WAITING_FOR_NEW_NICK = set()

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ تغییر لقب", callback_data="change_nick")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    nick = get_nickname(uid)

    if nick:
        await update.message.reply_text(
            f"👋 خوش اومدی\n\n"
            f"🕶 لقب فعلی تو: *{nick}*\n\n"
            "هر پیامی بفرستی بعد از تأیید ادمین توی گروه منتشر میشه.",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
    else:
        WAITING_FOR_NICK.add(uid)
        await update.message.reply_text(
            "سلام 👋\n\n"
            "🤖 این ربات برای ارسال پیام *ناشناس* به گروهه.\n\n"
            "✍️ لطفاً یه لقب ناشناس برای خودت بفرست.\n"
            "🔒 این لقب دائمیه ولی می‌تونی تغییرش بدی.",
            parse_mode="Markdown"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    # ثبت لقب اولیه
    if uid in WAITING_FOR_NICK:
        WAITING_FOR_NICK.remove(uid)
        set_nickname(uid, text)
        await update.message.reply_text(
            f"✅ لقبت ثبت شد:\n*{text}*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return

    # تغییر لقب
    if uid in WAITING_FOR_NEW_NICK:
        WAITING_FOR_NEW_NICK.remove(uid)
        set_nickname(uid, text)
        await update.message.reply_text(
            f"✏️ لقبت تغییر کرد:\n*{text}*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return

    nickname = get_nickname(uid)
    if not nickname:
        WAITING_FOR_NICK.add(uid)
        await update.message.reply_text("اول باید یه لقب انتخاب کنی ✍️")
        return

    # فوروارد پیام به ادمین (پروفایل معلوم)
    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=uid,
        message_id=update.message.message_id
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید", callback_data=f"approve|{uid}|{text}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject|{uid}")
        ]
    ])

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🕶 لقب: {nickname}",
        reply_markup=keyboard
    )

    await update.message.reply_text("⏳ پیامت برای بررسی ارسال شد")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data.split("|")

    if data[0] == "change_nick":
        WAITING_FOR_NEW_NICK.add(q.from_user.id)
        await q.message.reply_text("✍️ لقب جدیدتو بفرست")
        return

    action = data[0]
    uid = int(data[1])

    if action == "approve":
        text = data[2]
        nick = get_nickname(uid)

        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"🕶 {nick} گفت:\n{text}"
        )

        await context.bot.send_message(
            chat_id=uid,
            text="✅ پیامت تأیید شد و توی گروه منتشر شد"
        )

        await q.edit_message_text("✅ پیام ارسال شد")

    elif action == "reject":
        await context.bot.send_message(
            chat_id=uid,
            text="❌ پیامت رد شد"
        )
        await q.edit_message_text("❌ پیام رد شد")

# اپلیکیشن سراسری (برای webhook)
application = Application.builder().token(BOT_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
application.add_handler(CallbackQueryHandler(buttons))
