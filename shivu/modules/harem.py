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

async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id
    user = None  # Initialize user variable

   
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

    # Retrieve the harem mode from Redis
    hmode_key = f"{user_id}hmode"
    hmode = r.hget(hmode_key, "rarity").decode("utf-8") if r.exists(hmode_key) else None
    if hmode:
        # Map harem mode to rarity value
        rarity_value = harem_mode_mapping.get(hmode, "Unknown Rarity")

        user = await user_collection.find_one({'id': user_id})
        if not user:
            if update.message:
                await update.message.reply_text('You Have Not Guessed any Characters Yet..')
            else:
                await update.callback_query.edit_message_text('You Have Not Guessed any Characters Yet..')
            return

        characters = sorted(user['characters'], key=lambda x: (x['anime'], x['id']))

        character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}

        # Filter characters based on rarity
        hmode_characters = [char for char in characters if char['rarity'] == rarity_value]

        unique_characters = list({character['id']: character for character in hmode_characters}.values())

        total_pages = math.ceil(len(unique_characters) / 10)

        if page < 0 or page >= total_pages:
            page = 0

        harem_message = f"<b>{escape(update.effective_user.first_name)}'s {rarity_value} Harem - Page {page+1}/{total_pages}</b>\n"

        current_characters = unique_characters[page*10:(page+1)*10]

        current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])} 

        for anime, characters in current_grouped_characters.items():
            harem_message += f'\n\n<b>⌬ {anime} 〔{len(characters)}/{await collection.count_documents({"anime": anime})}〕</b>\n'

            for character in characters:
                count = character_counts[character['id']]
                # Format the ID with leading zeros if it's less than four digits
                formatted_id = f"{int(character['id']):04d}"
                harem_message += f'\n➥ <b>{formatted_id}</b> | {character["rarity"][0]} | {character["name"]} ×{count}'

        total_count = len(user['characters'])
        keyboard = [[InlineKeyboardButton(f"⟭⟬ ᴄᴏɴᴄᴜʙɪɴᴇs ⌠{total_count}⌡", switch_inline_query_current_chat=f"collection.{user_id}")]]

        if total_pages > 1:
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}"))
            if page < total_pages - 1:
                nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}"))
            keyboard.append(nav_buttons)

        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query and update.callback_query.message:
            try:
                await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
            except Exception as e:
                await update.callback_query.answer(f"Error updating message: {e}")
    else:
        if update.message:
            await update.message.reply_text('Please set your harem mode first using /hmode command.')
        else:
            await update.callback_query.edit_message_text('Please set your harem mode first using /hmode command.')

    if 'favorites' in user and user['favorites']:
        fav_character_id = user['favorites'][0]
        fav_character = next((c for c in user['characters'] if c['id'] == fav_character_id), None)

        if fav_character and 'img_url' in fav_character:
            if update.message:
                await update.message.reply_photo(photo=fav_character['img_url'], parse_mode='HTML', caption=harem_message, reply_markup=reply_markup)
            else:
                if update.callback_query.message and update.callback_query.message.caption != harem_message:
                    await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            if update.message:
                await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                if update.callback_query.message and update.callback_query.message.text != harem_message:
                    await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        if user['characters']:
            random_character = random.choice(user['characters'])

            if 'img_url' in random_character:
                if update.message:
                    await update.message.reply_photo(photo=random_character['img_url'], parse_mode='HTML', caption=harem_message, reply_markup=reply_markup)
                else:
                    if update.callback_query.message and update.callback_query.message.caption != harem_message:
                        await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                if update.message:
                    await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
                else:
                    if update.callback_query.message and update.callback_query.message.text != harem_message:
                        await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            if update.message:
                await update.message.reply_text("Your List is Empty :")

async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    _, page, user_id = data.split(':')
    page = int(page)
    user_id = int(user_id)

    if query.from_user.id != user_id:
        await query.answer("It's Not Your Harem", show_alert=True)
        return

    await query.answer()  # Await the answer coroutine

    await harem(update, context, page)

async def set_hmode(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    keyboard = [
        [
            InlineKeyboardButton("⌠⚪⌡", callback_data="common"),
            InlineKeyboardButton("⌠🟣⌡", callback_data="rare"),
            InlineKeyboardButton("⌠🟢⌡", callback_data="medium"),
        ],
        
        [
           
            InlineKeyboardButton("⌠🟡⌡", callback_data="legendary"),
            InlineKeyboardButton("⌠🎄⌡", callback_data="christmas"),
            InlineKeyboardButton("⌠💘⌡", callback_data="valentine"),
        ],
        [
            InlineKeyboardButton("⌠💮⌡ ", callback_data="exclusive"),
            InlineKeyboardButton("⌠🫧⌡", callback_data="special_edition"),
            InlineKeyboardButton("⌠🔮⌡ ", callback_data="limited_edition"),
            
        ],
        [
            InlineKeyboardButton("˹ 🎐 ˼ ℭ𝔢𝔩𝔢𝔰𝔱𝔦𝔞𝔩", callback_data="celestial"),
            InlineKeyboardButton("💋 [𝙓] 𝙑𝙚𝙧𝙨𝙚", callback_data="x_valentine"),
            InlineKeyboardButton("🔞 NSFW", callback_data="18+"),
            
           
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await update.message.reply_photo(
        photo="https://telegra.ph/file/d7b82b55e6bc6d6fcf58b.jpg",
        caption="Set your harem mode:",
        reply_markup=reply_markup,
    )

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    # Set hmode in Redis
    r.hset(f"{user_id}hmode", "rarity", data)
    await query.answer()  # Await the query.answer() coroutine
    await query.edit_message_caption(f"You set to {data}")

application.add_handler(CommandHandler(["harem", "collection"], harem, block=False))
harem_handler = CallbackQueryHandler(harem_callback, pattern='^harem', block=False)
application.add_handler(harem_handler)
application.add_handler(CommandHandler("hmode", set_hmode))
application.add_handler(CallbackQueryHandler(button))
