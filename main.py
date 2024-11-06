import openai
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

# Define a function to handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_message}]
    )
    bot_reply = response['choices'][0]['message']['content'].strip()
    await update.message.reply_text(bot_reply)

# Define a function to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! I am your AI-powered bot. How can I assist you today?')

def main():
    # Set your Telegram bot token
    # telegram_token = '7987453052:AAEDLf8O4bbnsVA9fVlZSNwvH-m9s_-vkEo'
    
    # Create the Application
    application = Application.builder().token(telegram_token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()