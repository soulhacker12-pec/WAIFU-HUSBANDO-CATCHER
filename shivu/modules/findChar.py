import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import MongoClient, DESCENDING
import asyncio

from telegram import Update, InlineQueryResultPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import InlineQueryHandler, CallbackContext, CommandHandler, Updater


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

# Inline query handler
async def inlinequery(update: Update, context: CallbackContext) -> None:
    async with lock:
        query = update.inline_query.query
        offset = int(update.inline_query.offset) if update.inline_query.offset else 0

        # Load characters from cache or database
        if query:
            regex = {'$regex': query, '$options': 'i'}
            all_characters = list(await collection.find({"$or": [{"name": regex}, {"anime": regex}]}).to_list(length=None))
        else:
            if 'all_characters' in all_characters_cache:
                all_characters = all_characters_cache['all_characters']
            else:
                all_characters = list(await collection.find({}).to_list(length=None))
                all_characters_cache['all_characters'] = all_characters

        # Slice the characters based on the current offset and results per page
        characters = all_characters[offset:offset+8]

        results = []
        for character in characters:
            global_count = await user_collection.count_documents({'characters.id': character['id']})

            caption = f"<b>Look At This Character !!</b>\n\n🌸: <b>{character['name']}</b>\n🏖️: <b>{character['anime']}</b>\n<b>{character['rarity']}</b>\n🆔️: <b>{character['id']}</b>\n\n<b>Globally Guessed {global_count} Times...</b>"

            # Create inline button to access IDs
            inline_button = InlineKeyboardButton("Access IDs", callback_data=f"access_ids_{character['id']}")
            reply_markup = InlineKeyboardMarkup([[inline_button]])

            results.append(
                InlineQueryResultPhoto(
                    thumbnail_url=character['img_url'],
                    id=f"{character['id']}_{time.time()}",
                    photo_url=character['img_url'],
                    caption=caption,
                    parse_mode='HTML',
                    photo_width=300,
                    photo_height=300,
                    reply_markup=reply_markup  # Include inline button in result
                )
            )

        await update.inline_query.answer(results, cache_time=5)

# Callback handler for accessing IDs
def access_ids_callback(update: Update, context: CallbackContext) -> None:
    chat_id = update.callback_query.message.chat_id
    if chat_id in found_ids_cache:
        found_ids = found_ids_cache[chat_id]
        ids_text = ', '.join(f'<code>{char_id}</code>' for char_id in found_ids)
        found_text = f"IDs of found characters: {ids_text}"
        update.callback_query.message.reply_text(found_text, parse_mode='HTML')
    else:
        update.callback_query.message.reply_text("No cached IDs found.")

# Add handlers to dispatcher
application.add_handler(CommandHandler('find', find_command))
application.add_handler(InlineQueryHandler(inlinequery))
application.add_handler(CallbackQueryHandler(access_ids_callback, pattern='^access_ids'))
