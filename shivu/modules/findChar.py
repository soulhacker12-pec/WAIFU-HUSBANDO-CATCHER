from pymongo import TEXT
from telegram import Update, InlineQueryResultPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import InlineQueryHandler, CallbackContext, CommandHandler 
from cachetools import TTLCache
import asyncio
import time
import uuid  # Import UUID to generate unique access keywords

from shivu import user_collection, collection, application, db

# Define a lock for concurrency control
lock = asyncio.Lock()
# collection
db.characters.create_index([('id', TEXT), ('anime', TEXT)], default_language='english')
db.characters.create_index([('img_url', TEXT)])

# TTL caches
all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)
found_ids_cache = TTLCache(maxsize=1000, ttl=120)

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

            # Generate a unique access keyword for this search
            access_keyword = str(uuid.uuid4())

            # Cache found IDs with the unique access keyword
            found_ids_cache[access_keyword] = found_ids

            # Create inline button to access cached IDs
            inline_button = InlineKeyboardButton(
                "Access IDs", switch_inline_query_current_chat=f'access {access_keyword}'
            )
            reply_markup = InlineKeyboardMarkup([[inline_button]])

            # Add inline button to found text
            found_text = f"IDs of found characters: {ids_text}"
            await update.message.reply_text(found_text, parse_mode='HTML', reply_markup=reply_markup)
        else:
            await update.message.reply_text('No characters found.')

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')


async def inline_query_handler(update: Update, context: CallbackContext) -> None:
    async with lock:
        query = update.inline_query.query
        offset = int(update.inline_query.offset) if update.inline_query.offset else 0

        if query.startswith('access'):
            access_keyword = query.split()[1]
            if access_keyword in found_ids_cache:
                found_ids = found_ids_cache[access_keyword]
                found_characters = await collection.find({"id": {"$in": found_ids}}).to_list(None)
            else:
                found_characters = []
        else:
            found_characters = []

        results = []
        for character in found_characters:
            global_count = await user_collection.count_documents({'characters.id': character['id']})
            anime_characters = await collection.count_documents({'anime': character['anime']})

            caption = f"<b>Look At This Character !!</b>\n\n🌸:<b> {character['name']}</b>\n🏖️: <b>{character['anime']}</b>\n<b>{character['rarity']}</b>\n🆔️: <b>{character['id']}</b>\n\n<b>Globally Guessed {global_count} Times...</b>"

            results.append(
                InlineQueryResultPhoto(
                    thumbnail_url=character['img_url'],
                    id=f"{character['id']}_{time.time()}",
                    photo_url=character['img_url'],
                    caption=caption,
                    parse_mode='HTML',
                    photo_width=300,  # Adjust the width as needed
                    photo_height=300  # Adjust the height as needed
                )
            )

        await update.inline_query.answer(results, cache_time=1)

FIND_HANDLER = CommandHandler('find', find_command, block=False)
application.add_handler(FIND_HANDLER)

application.add_handler(InlineQueryHandler(inline_query_handler, block=False))
