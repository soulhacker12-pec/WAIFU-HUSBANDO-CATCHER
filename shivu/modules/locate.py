from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from shivu import user_collection , application # Adjust this import based on your actual database setup

async def locate(update: Update, context: CallbackContext, char_id: int) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        if update.message:
            await update.message.reply_text('You Have Not Guessed any Characters Yet..')
        else:
            await update.callback_query.edit_message_text('You Have Not Guessed any Characters Yet..')
        return

    characters = user['characters']
    count = sum(character['id'] == char_id for character in characters)

    character_found = next((c for c in characters if c['id'] == char_id), None)

    if character_found:
        character_name = character_found['name']
        character_img_url = character_found['img_url']

        # Caption template
        caption = f"┏━┅┅┄┄⟞⟦🎐⟧⟝┄┄┉┉━┓\n\n┣ {character_name}'s ˹𝕮𝖔𝖚𝖓𝖙˼ ➾ {count}\n\n┗━┅┅┄┄⟞⟦🎐⟧⟝┄┄┉┉━┛"

        # Button to delete the message
        delete_button = InlineKeyboardButton("🚮", callback_data="delete_message")

        keyboard = [[delete_button]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send photo of the character and caption with the delete button
        await update.message.reply_photo(
            photo=character_img_url,
            caption=caption,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Character not found in your collection.")

async def callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    if data == "delete_message":
        await query.message.delete()
    
    # Await the answer method
    await query.answer()

async def locate_command_handler(update: Update, context: CallbackContext):
    # Extract the character ID from the command
    char_id = int(context.args[0]) if context.args else None

    if char_id is None:
        await update.message.reply_text("Please provide a character ID.")
        return

    # Call the locate function with the provided character ID
    await locate(update, context, char_id)

# Add the command handler for /locate
application.add_handler(CommandHandler("locate", locate_command_handler, block=False))
# Add the callback handler for deleting messages
application.add_handler(CallbackQueryHandler(callback_handler, pattern='delete_message', block=False))
