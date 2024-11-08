import openai
import os
import io
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import tiktoken

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables directly
openai.api_key = os.getenv("OPENAI_API_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

if telegram_token is None:
    logging.error("Error: TELEGRAM_BOT_TOKEN environment variable is not set")
    exit(1)
if openai.api_key is None:
    logging.error("Error: OPENAI_API_KEY environment variable is not set")
    exit(1)

# Define a function to handle text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_message = update.message.text
        logging.debug(f"Received text message: {user_message}")

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

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=trimmed_conversation
        )
        bot_reply = response['choices'][0]['message']['content'].strip()

        # Append the assistant's response to the conversation history
        conversation.append({"role": "assistant", "content": bot_reply})

        # Update the stored conversation
        context.user_data['conversation'] = conversation

        await update.message.reply_text(bot_reply)
    except Exception as e:
        logging.exception("Error in handle_message")
        await update.message.reply_text("Sorry, I'm having trouble processing your request.")

# Define a function to handle voice messages
async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logging.debug("Received a voice message")

        # Get the voice message
        voice = update.message.voice
        file_id = voice.file_id
        logging.debug(f"Voice message file_id: {file_id}")

        # Get the file object
        file = await context.bot.get_file(file_id)

        # Download the file into a BytesIO object
        audio_buffer = io.BytesIO()
        await file.download_to_memory(out=audio_buffer)
        logging.debug("Voice message downloaded into buffer")

        # Reset the buffer's file pointer to the beginning
        audio_buffer.seek(0)

        # Transcribe the audio using OpenAI's Whisper API
        transcript = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_buffer,
            filename="audio.ogg",  # Provide a filename with the correct extension
            response_format="text"
        )
        logging.debug(f"Transcription result: {transcript}")

        # Use the transcript as the user's message
        user_message = transcript

        # Retrieve the conversation history for this user
        if 'conversation' not in context.user_data:
            context.user_data['conversation'] = []
        conversation = context.user_data['conversation']

        # Append the user's new message to the conversation history
        conversation.append({"role": "user", "content": user_message})

        # Token limit management (same as in handle_message)
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

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=trimmed_conversation
        )
        bot_reply = response['choices'][0]['message']['content'].strip()

        # Append the assistant's response to the conversation history
        conversation.append({"role": "assistant", "content": bot_reply})

        # Update the stored conversation
        context.user_data['conversation'] = conversation

        await update.message.reply_text(bot_reply)
    except Exception as e:
        logging.exception("Error in handle_voice_message")
        await update.message.reply_text("Sorry, an error occurred while processing your voice message.")

# Define a function to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! I am your AI-powered bot. How can I assist you today?')

# Define a function to reset the conversation
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['conversation'] = []
    await update.message.reply_text("Conversation history has been reset. How can I assist you now?")

def main():
    logging.info("Starting application")

    # Create the Application
    application = Application.builder().token(telegram_token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))  # Moved before text handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start webhook instead of polling
    port = int(os.environ.get("PORT", "8443"))  # Default port 8443 if PORT is not set
    logging.info(f"PORT: {port}")
    render_external_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_external_url is None:
        logging.error("Error: RENDER_EXTERNAL_URL environment variable is not set")
        exit(1)
    webhook_url = f"{render_external_url}/{telegram_token}"
    logging.info(f"Webhook URL: {webhook_url}")
    try:
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=telegram_token,
            webhook_url=webhook_url
        )
    except Exception as e:
        logging.exception("Error starting the webhook")
        exit(1)

if __name__ == '__main__':
    main()
