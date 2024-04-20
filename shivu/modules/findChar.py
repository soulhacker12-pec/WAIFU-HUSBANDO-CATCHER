from pymongo import TEXT
from telegram import Update, InlineQueryResultPhoto
from telegram.ext import InlineQueryHandler, CallbackContext, CommandHandler 
from cachetools import TTLCache
import asyncio
import time
from html import escape

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


async def inline_query_handler(update: Update, context: CallbackContext) -> None:
    async with lock:
        query = update.inline_query.query
        offset = int(update.inline_query.offset) if update.inline_query.offset else 0

        # Load 3 results per row
        results_per_row = 4
        results_per_page = 8

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
        characters = all_characters[offset:offset+results_per_page]

        next_offset = offset + len(characters)

        results = []
        for character in characters:
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

        await update.inline_query.answer(results, next_offset=str(next_offset), cache_time=5)

FIND_HANDLER = CommandHandler('find', find_command, block=False)
application.add_handler(FIND_HANDLER)

application.add_handler(InlineQueryHandler(inline_query_handler, block=False))
