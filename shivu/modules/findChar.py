from pymongo import TEXT
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, collection

async def find(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Incorrect format. Please use: /find name')
            return

        search_query = args[0].replace('-', ' ').title()

        # Perform case-insensitive partial match search using text index
        cursor = collection.find({'$text': {'$search': search_query}})

        found_characters = await cursor.to_list(None)

        if found_characters:
            # Format the IDs with prefix 'id' and a number
            formatted_ids = [f'id{char["id"]}' for char in found_characters]
            ids_text = ', '.join(formatted_ids)
            await update.message.reply_text(f"IDs of found characters: {ids_text}")
        else:
            await update.message.reply_text('No characters found.')

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

FIND_HANDLER = CommandHandler('find', find, block=False)
application.add_handler(FIND_HANDLER)

# Create a text index on the 'name' field
collection.create_index([('name', TEXT)], default_language='english')
