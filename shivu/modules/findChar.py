from pymongo import TEXT, DESCENDING
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

        # Perform case-insensitive partial match search and sort by text score
        cursor = collection.aggregate([
            {
                '$match': {
                    'name': {'$regex': search_query, '$options': 'i'}
                }
            },
            {
                '$project': {
                    'name': 1,
                    'id': 1,
                    'score': {'$meta': 'textScore'}
                }
            },
            {
                '$sort': {'score': {'$meta': 'textScore'}}
            }
        ])

        found_characters = await cursor.to_list(None)

        if found_characters:
            ids = ', '.join(str(char['id']) for char in found_characters)
            await update.message.reply_text(f"IDs of found characters: {ids}")
        else:
            await update.message.reply_text('No characters found.')

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

FIND_HANDLER = CommandHandler('find', find, block=False)
application.add_handler(FIND_HANDLER)
