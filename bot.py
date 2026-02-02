import os
import psycopg2
from psycopg2.extras import DictCursor

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ChatType


# ================= CONFIG =================
BOT_TOKEN = "8574592475:AAFfarKG2o8OzBtykXr4bzFPolHVgQEBbKc"
ADMIN_ID = 6474515118
GROUP_ID = -1003614589024
DATABASE_URL = os.environ.get("DATABASE_URL")
PORT = int(os.environ.get("PORT", 10000))


# ================= DATABASE =================
def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    nickname TEXT NOT NULL
                );
            """)
        conn.commit()


def get_user(user_id):
    with get_db() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
            return cur.fetchone()


def set_nickname(user_id, nickname):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (user_id, nickname)
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET nickname=EXCLUDED.nickname
            """, (user_id, nickname))
        conn.commit()


# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != ChatType.PRIVATE:
        return

    user = get_user(update.effective_user.id)

    if user:
        await update.message.reply_text(
            f"👋 خوش اومدی!\n\n"
            f"لقب فعلی تو:\n"
            f"🔹 {user['nickname']}\n\n"
            f"هر پیامی بفرستی بعد از تأیید ادمین، ناشناس تو گروه منتشر می‌شه.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ تغییر لقب", callback_data="change_nick")]
            ])
        )
    else:
        context.user_data["awaiting_nick"] = True
        await update.message.reply_text(
            "👋 سلام!\n\n"
            "این ربات پیام‌هات رو **به‌صورت ناشناس** تو گروه منتشر می‌کنه.\n\n"
            "🕶 لطفاً یک **لقب ناشناس** برای خودت انتخاب کن.\n"
            "⚠️ این لقب پیش‌فرض دائمیه (ولی بعداً می‌تونی عوضش کنی)."
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != ChatType.PRIVATE:
        return

    user_id = update.effective_user.id
    text = update.message.text.strip()

    # انتخاب یا تغییر لقب
    if context.user_data.get("awaiting_nick"):
        set_nickname(user_id, text)
        context.user_data["awaiting_nick"] = False

        await update.message.reply_text(
            f"✅ لقبت ثبت شد:\n"
            f"🔹 {text}\n\n"
            f"از حالا هر پیامی بفرستی، بعد از تأیید ادمین تو گروه منتشر می‌شه."
        )
        return

    user = get_user(user_id)
    if not user:
        context.user_data["awaiting_nick"] = True
        await update.message.reply_text("اول باید یه لقب انتخاب کنی ✍️")
        return

    # ارسال پیام برای ادمین (فوروارد)
    forwarded = await update.message.forward(chat_id=ADMIN_ID)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید", callback_data=f"approve:{forwarded.message_id}:{user_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject:{forwarded.message_id}:{user_id}")
        ]
    ])

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text="📨 پیام جدید برای بررسی:",
        reply_to_message_id=forwarded.message_id,
        reply_markup=keyboard
    )


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # تغییر لقب
    if data == "change_nick":
        context.user_data["awaiting_nick"] = True
        await query.message.reply_text("✏️ لقب جدیدتو بفرست:")
        return

    # فقط ادمین
    if update.effective_user.id != ADMIN_ID:
        return

    action, msg_id, user_id = data.split(":")
    user_id = int(user_id)

    user = get_user(user_id)
    if not user:
        return

    # متن پیام اصلی
    forwarded_msg = query.message.reply_to_message
    text = forwarded_msg.text or forwarded_msg.caption or ""

    if action == "approve":
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"🕶 {user['nickname']} گفت:\n{text}"
        )
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ پیامت تأیید شد و تو گروه منتشر شد."
        )

    else:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ پیامت توسط ادمین رد شد."
        )

    await query.edit_message_reply_markup(reply_markup=None)


# ================= MAIN =================
def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"https://nashenas-71cn.onrender.com/webhook"
    )


if __name__ == "__main__":
    main()
