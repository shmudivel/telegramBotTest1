import openai
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import tiktoken

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

    # Retrieve the conversation history for this user
    if 'conversation' not in context.user_data:
        context.user_data['conversation'] = []
    conversation = context.user_data['conversation']

    # Append the user's new message to the conversation history
    conversation.append({"role": "user", "content": user_message})

    # Token limit management
    MAX_TOKENS = 4096
    TOKEN_MARGIN = 500  # Leave space for the assistant's reply
    encoding = tiktoken.encoding_for_model('gpt-3.5-turbo')

    total_tokens = 0
    trimmed_conversation = []
    # Reverse the conversation to start from the latest messages
    for message in reversed(conversation):
        tokens = len(encoding.encode(message['content']))
        total_tokens += tokens
        if total_tokens > (MAX_TOKENS - TOKEN_MARGIN):
            break
        trimmed_conversation.insert(0, message)  # Re-insert at the beginning

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=trimmed_conversation
        )
        bot_reply = response['choices'][0]['message']['content'].strip()

        # Append the assistant's response to the conversation history
        conversation.append({"role": "assistant", "content": bot_reply})

        # Update the stored conversation
        context.user_data['conversation'] = conversation

    except Exception as e:
        print(f"Error in OpenAI API call: {e}")
        bot_reply = "Sorry, I'm having trouble processing your request."

    await update.message.reply_text(bot_reply)

# Define a function to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! I am your AI-powered bot. How can I assist you today?')

# Define a function to reset the conversation
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['conversation'] = []
    await update.message.reply_text("Conversation history has been reset. How can I assist you now?")

def main():
    print("Starting application")
    # Create the Application
    application = Application.builder().token(telegram_token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset))  # Added reset command handler
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
