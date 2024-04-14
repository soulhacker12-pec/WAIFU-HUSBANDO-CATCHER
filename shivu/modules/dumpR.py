from telegram import Update
from itertools import groupby
import math
from html import escape 
import random

from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from shivu import collection, user_collection, application
import redis

# Redis connection setup
r = redis.Redis(
    host='redis-13192.c282.east-us-mz.azure.cloud.redislabs.com',
    port=13192,
    password='wKgGC52NC9NRhic36fDIvWh76dngPvP9'
)


async def refresh(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    # Load harem data from the dump (replace this with your dump loading logic)
    harem_data = load_harem_data(user_id)
    if not harem_data:
        await update.message.reply_text('Harem data not found. Please upload the harem data first.')
        return

    characters = harem_data.get('characters', [])
    sorted_characters = sorted(characters, key=lambda x: (x['anime'], x['id']))

    # Define a mapping dictionary for harem modes to rarity values
    harem_mode_mapping = {
        "common": "⚪ Common",
        "rare": "🟣 Rare",
        "legendary": "🟡 Legendary",
        "medium": "🟢 Medium",
        "exclusive": "💮 Exclusive",
        "special_edition": "🫧 Special Edition",
        "limited_edition": "🔮 Limited Edition",
        "celestial": "🎐 Celestial",
        "christmas": "🎄 Christmas",
        "valentine": "💘 Valentine",
        "x_valentine": "💋 [𝙓] 𝙑𝙚𝙧𝙨𝙚",
        "18+": "🔞 NSFW"
    }

    harem_messages = {}  # Dictionary to store harem messages for each rarity

    for hmode, rarity_value in harem_mode_mapping.items():
        hmode_characters = [char for char in sorted_characters if char['rarity'] == rarity_value]

        unique_characters = list({character['id']: character for character in hmode_characters}.values())

        total_pages = math.ceil(len(unique_characters) / 10)

        harem_message = f"<b>{escape(update.effective_user.first_name)}'s {rarity_value} Harem - Page 1/{total_pages}</b>\n"

        current_characters = unique_characters[:10]  # Display first 10 characters

        current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

        for anime, characters in current_grouped_characters.items():
            harem_message += f'\n\n<b>⌬ {anime} 〔{len(characters)}/{await collection.count_documents({"anime": anime})}〕</b>\n'

            for character in characters:
                count = len([char for char in hmode_characters if char['id'] == character['id']])
                # Format the ID with leading zeros if it's less than four digits
                formatted_id = f"{int(character['id']):04d}"
                harem_message += f'\n➥ <b>˹{formatted_id}˼</b> | ◈ ⌠{character["rarity"][0]}⌡ | {character["name"]} ×{count}'

        harem_messages[hmode] = harem_message

    # Store harem messages for the user in Redis or any storage mechanism
    store_harem_messages(user_id, harem_messages)

    await update.message.reply_text('Harem messages prepared for all rarities.')


async def rharem(update: Update, context: CallbackContext, rarity_number: int) -> None:
    user_id = update.effective_user.id
    # Load harem messages for the user (replace this with your actual loading logic)
    harem_messages = load_harem_messages(user_id)
    if not harem_messages:
        await update.message.reply_text('Harem messages not found. Please refresh the harem data first.')
        return

    rarity_key = f"rarity_{rarity_number}"
    harem_message = harem_messages.get(rarity_key)
    if not harem_message:
        await update.message.reply_text('Harem message not found for the specified rarity.')
        return

    # Pagination logic
    total_pages = math.ceil(len(harem_message) / 10)  # Calculate total pages
    page = 1  # Start from page 1

    harem_message_page = harem_message[:10]  # Display first 10 characters

    keyboard = [[InlineKeyboardButton("Next ➡️", callback_data=f"rharem_next:{user_id}:{rarity_number}:2")]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    message = await update.message.reply_text(harem_message_page, parse_mode='HTML', reply_markup=reply_markup)
    # Save message id and page info for pagination
    context.user_data['rharem_message_id'] = message.message_id
    context.user_data['rharem_rarity'] = rarity_number
    context.user_data['rharem_current_page'] = page


async def rharem_next(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    rarity_number = context.user_data.get('rharem_rarity')
    current_page = context.user_data.get('rharem_current_page')

    harem_messages = load_harem_messages(user_id)
    if not harem_messages:
        await update.message.reply_text('Harem messages not found. Please refresh the harem data first.')
        return

    rarity_key = f"rarity_{rarity_number}"
    harem_message = harem_messages.get(rarity_key)
    if not harem_message:
        await update.message.reply_text('Harem message not found for the specified rarity.')
        return

    total_pages = math.ceil(len(harem_message) / 10)  # Calculate total pages
    page = current_page + 1  # Increment page

    start_idx = (page - 1) * 10
    end_idx = start_idx + 10
    harem_message_page = harem_message[start_idx:end_idx]

    keyboard = []
    if page > 1:
        keyboard.append([InlineKeyboardButton("⬅️ Prev", callback_data=f"rharem_prev:{user_id}:{rarity_number}:{page-1}")])
    if page < total_pages:
        keyboard.append([InlineKeyboardButton("Next ➡️", callback_data=f"rharem_next:{user_id}:{rarity_number}:{page+1}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(harem_message_page, parse_mode='HTML', reply_markup=reply_markup)


# Add command handlers
application.add_handler(CommandHandler("refresh", refresh))
application.add_handler(CommandHandler("rharem", rharem))

# Add callback query handler for "rharem_next" pattern
application.add_handler(CallbackQueryHandler(rharem_next, pattern=r'^rharem_next'))
