import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import MongoClient, DESCENDING
import asyncio
from telegram import Update, InlineQueryResultPhoto
from telegram.ext import InlineQueryHandler, CallbackContext, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Define a lock for concurrency control
lock = asyncio.Lock()
from shivu import user_collection, collection, application, db

# Collection indexes
collection.create_index([('id', DESCENDING)])
collection.create_index([('anime', DESCENDING)])
collection.create_index([('img_url', DESCENDING)])
user_collection.create_index([('characters.id', DESCENDING)])
user_collection.create_index([('characters.name', DESCENDING)])
user_collection.create_index([('characters.img_url', DESCENDING)])

# TTL caches
all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)
found_ids_cache = TTLCache(maxsize=10000, ttl=3600)  # Define found_ids_cache

# /find command handler
async def find_command(update: Update, context: CallbackContext) -> None:
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
            # Extract the IDs from found characters and wrap each in <code> tags
            found_ids = [char["id"] for char in found_characters]
            ids_text = ', '.join(f'<code>{char_id}</code>' for char_id in found_ids)

            # Cache found IDs
            found_ids_cache[update.message.chat_id] = found_ids

            # Create inline button to access cached IDs
            inline_button = InlineKeyboardButton("Access IDs", callback_data="access_ids")
            reply_markup = InlineKeyboardMarkup([[inline_button]])

            # Add inline button to found text
            found_text = f"IDs of found characters: {ids_text}"
            await update.message.reply_text(found_text, parse_mode='HTML', reply_markup=reply_markup)
        else:
            await update.message.reply_text('No characters found.')

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

application.add_handler(CommandHandler('find', find_command))
