import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from groq import Groq

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = os.getenv("ADMIN_ID")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

client = Groq(api_key=GROQ_API_KEY)

# Admin ga xabar yo'naltirish
async def notify_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_msg: str):
    if not ADMIN_ID:
        return
    
    user = update.effective_user
    admin_text = (
        f"🆕 Yangi xabar:\n\n"
        f"👤 Ism: {user.full_name}\n"
        f"🔖 Username: @{user.username or 'yoq'}\n"
        f"🆔 ID: {user.id}\n"
        f"⏰ Vaqt: {update.message.date.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"💬 Savol: {user_msg}"
    )
    
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    except Exception as e:
        logger.warning(f"Admin ga xabar yuborishda xatolik: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Salom! Hojaka AI yordamchiman. Savolingizni yozing 👇")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    
    # Admin ga xabar yo'naltirish
    await notify_admin(update, context, user_msg)
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Siz faqat o'zbek tilida javob bering. Hech qachon boshqa tilda javob bermang."},
                {"role": "user", "content": user_msg}
            ],
            model="llama-3.1-8b-instant",
        )
        answer = chat_completion.choices[0].message.content
        
        # Uzun javobni bo'lib yuborish
        if len(answer) > 4096:
            for i in range(0, len(answer), 4096):
                await update.message.reply_text(answer[i:i+4096])
        else:
            await update.message.reply_text(answer)
            
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

def main():
    if not TELEGRAM_TOKEN or not GROQ_API_KEY:
        logger.error("XATOLIK: .env faylida kalitlar yo'q!")
        return
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🤖 Bot ishga tushdi (Admin paneli bilan)...")
    application.run_polling()

if __name__ == "__main__":
    main()