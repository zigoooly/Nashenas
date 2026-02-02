from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
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

ASK_NICK = {}
CHANGE_NICK = {}

WELCOME = (
    "سلام 👋\n\n"
    "🤖 این ربات برای ارسال *پیام ناشناس* به گروهه.\n\n"
    "🧩 لطفاً یه لقب ناشناس برای خودت انتخاب کن.\n"
    "🔒 این لقب بالای پیام‌هات نمایش داده میشه."
)

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ تغییر لقب", callback_data="change_nick")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    nick = get_nickname(uid)

    if nick:
        await update.message.reply_text(
            f"خوش اومدی 🌱\n\n"
            f"🕶 لقب فعلی تو: *{nick}*\n\n"
            "هر پیامی بفرستی بعد از تأیید منتشر میشه.",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
    else:
        ASK_NICK[uid] = True
        await update.message.reply_text(WELCOME, parse_mode="Markdown")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    # ثبت لقب اولیه
    if ASK_NICK.pop(uid, False):
        set_nickname(uid, text)
        await update.message.reply_text(
            f"✅ لقبت ثبت شد:\n*{text}*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return

    # تغییر لقب
    if CHANGE_NICK.pop(uid, False):
        set_nickname(uid, text)
        await update.message.reply_text(
            f"✏️ لقبت با موفقیت تغییر کرد:\n*{text}*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return

    # پیام ناشناس
    nickname = get_nickname(uid)
    if not nickname:
        ASK_NICK[uid] = True
        await update.message.reply_text("اول باید یه لقب انتخاب کنی ✍️")
        return

    # فوروارد به ادمین (پروفایل معلوم)
    forwarded = await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=uid,
        message_id=update.message.message_id
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید", callback_data=f"ok|{uid}|{text}"),
            InlineKeyboardButton("❌ رد", callback_data=f"no|{uid}")
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
        CHANGE_NICK[q.from_user.id] = True
        await q.message.reply_text("✍️ لقب جدیدتو بفرست")
        return

    action = data[0]
    uid = int(data[1])

    if action == "ok":
        text = data[2]
        nick = get_nickname(uid)

        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"🕶 {nick} گفت:\n{text}"
        )

        await context.bot.send_message(
            chat_id=uid,
            text="✅ پیامت تأیید و منتشر شد"
        )

        await q.edit_message_text("✅ ارسال شد")

    elif action == "no":
        await context.bot.send_message(
            chat_id=uid,
            text="❌ پیامت رد شد"
        )
        await q.edit_message_text("❌ رد شد")

def build_app():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(CallbackQueryHandler(buttons))

    return app
