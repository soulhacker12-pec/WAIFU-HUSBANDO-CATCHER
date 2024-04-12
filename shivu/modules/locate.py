from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from shivu import user_collection, application  # Adjust this import based on your actual database setup

async def get_character_count(user_id: int, char_id: int) -> int:
    user = await user_collection.find_one({'id': user_id})
    if user:
        characters = user.get('characters', [])
        return sum(character['id'] == char_id for character in characters)
    return 0

async def harem(update: Update, context: CallbackContext, char_id: int, page=0) -> None:
    user_id = update.effective_user.id

    # Get the count of the specific character
    count = await get_character_count(user_id, char_id)

    # Now you can use the count as needed in your harem function
    # For example, you can include it in the caption or message
    caption = f"You have {count} of character with ID {char_id} in your collection."

    # Send the message with the count
    await update.message.reply_text(caption)

async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    _, char_id, user_id = data.split(':')
    char_id = int(char_id)
    user_id = int(user_id)

    # Get the count of the specific character
    count = await get_character_count(user_id, char_id)

    # Now you can use the count as needed in your harem callback function
    # For example, you can include it in the caption or message
    caption = f"You have {count} of character with ID {char_id} in your collection."

    # Edit the message with the count
    await query.edit_message_text(caption)

# Add the command handler for /harem
application.add_handler(CommandHandler("locate", harem, block=False))
# Add the callback handler for harem pagination and other interactions
application.add_handler(CallbackQueryHandler(harem_callback, pattern='^harem:', block=False))
