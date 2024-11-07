import openai
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Remove load_dotenv() as environment variables are set via Render Dashboard

# Load environment variables directly
openai.api_key = os.getenv("OPENAI_API_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

if telegram_token is None:
    print("Error: TELEGRAM_BOT_TOKEN environment variable is not set")
    exit(1)
if openai.api_key is None:
    print("Error: OPENAI_API_KEY environment variable is not set")
    exit(1)

# Define a function to handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        bot_reply = response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error in OpenAI API call: {e}")
        bot_reply = "Sorry, I'm having trouble processing your request."
    await update.message.reply_text(bot_reply)

# Define a function to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! I am your AI-powered bot. How can I assist you today?')

def main():
    print("Starting application")
    # Create the Application
    application = Application.builder().token(telegram_token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start webhook instead of polling
    port = int(os.environ.get("PORT"))
    print(f"PORT: {port}")
    render_external_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_external_url is None:
        print("Error: RENDER_EXTERNAL_URL environment variable is not set")
        exit(1)
    webhook_url = f"{render_external_url}/{telegram_token}"
    print(f"Webhook URL: {webhook_url}")
    try:
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=telegram_token,
            webhook_url=webhook_url
        )
    except Exception as e:
        print(f"Error starting the webhook: {e}")
        exit(1)

if __name__ == '__main__':
    main()
