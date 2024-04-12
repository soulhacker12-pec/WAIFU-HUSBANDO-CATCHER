from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler
from shivu import user_collection, application  # Adjust this import based on your actual database setup

async def locate(update: Update, context: CallbackContext, waifu_no: int) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        if update.message:
            await update.message.reply_text('You Have Not Guessed any Characters Yet..')
        else:
            await update.callback_query.edit_message_text('You Have Not Guessed any Characters Yet..')
        return

    # Search for the character with the provided waifu_no in the user's collection
    character_found = next((c for c in user['characters'] if c['waifu_no'] == waifu_no), None)

    if character_found:
        character_name = character_found['name']
        character_img_url = character_found['img_url']

        # Caption template
        caption = f"Character found!\n\nName: {character_name}\nWaifu Number: {waifu_no}"

        # Send photo of the character and caption
        await update.message.reply_photo(
            photo=character_img_url,
            caption=caption
        )
    else:
        await update.message.reply_text("Character not found in your collection.")

async def locate_command_handler(update: Update, context: CallbackContext):
    # Extract the waifu number from the command
    waifu_no = int(context.args[0]) if context.args else None

    if waifu_no is None:
        await update.message.reply_text("Please provide a waifu number.")
        return

    # Call the locate function with the provided waifu number
    await locate(update, context, waifu_no)

# Add the command handler for /locate
application.add_handler(CommandHandler("locate", locate_command_handler, block=False))
