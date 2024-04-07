import urllib.request
from pymongo import ReturnDocument

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

# Assuming these are already defined in your existing code
from shivu import application, sudo_users, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT

async def check_character(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Incorrect format. Please use: /check {character_id}')
            return

        character_id = args[0]
        character = await collection.find_one({'id': character_id})
        
        if character:
            rarity_emoji = {
                '⚪': 'Common',
                '🟣': 'Rare',
                '🟡': 'Legendary',
                '🟢': 'Medium',
                '💮': 'Exclusive',
                '🫧': 'Special Edition',
                '🔮': 'Limited Edition',
                '🎐': 'Celestial',
                '🎄': 'Christmas',
                '💘': 'Valentine',
                '💋': '[𝙓] 𝙑𝙚𝙧𝙨𝙚'
            }

            rarity_symbol = character['rarity'][0]  # Get the first character of rarity to use as symbol
            rarity_text = rarity_emoji.get(rarity_symbol, 'Unknown Rarity')

            reply_message = (
                f'<b>Character Name:</b> {character["name"]}\n'
                f'<b>Anime:</b> {character["anime"]}\n'
                f'<b>Rarity:</b> {rarity_symbol} {rarity_text}\n'
                f'<b>Character ID:</b> {character["id"]}'
            )

            await update.message.reply_photo(
                photo=character["img_url"],
                caption=reply_message,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text('Character not found.')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

CHECK_HANDLER = CommandHandler('check', check_character, pass_args=True, block=False)
application.add_handler(CHECK_HANDLER)
