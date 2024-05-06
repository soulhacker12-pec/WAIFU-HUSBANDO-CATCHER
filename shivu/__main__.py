import importlib
import time
import random
import re
import asyncio
from html import escape 
import html
import locale

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from telegram import *

from shivu import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, shivuu
from shivu import application, SUPPORT_CHAT, UPDATE_CHAT, db, LOGGER
from shivu.modules import ALL_MODULES
import redis

# Redis connection setup
r = redis.Redis(
    host='redis-13192.c282.east-us-mz.azure.cloud.redislabs.com',
    port=13192,
    password='wKgGC52NC9NRhic36fDIvWh76dngPvP9')


zen_dict = {}  # Our dictionary to store channel ID and character name pairs
locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}


unwanted_rarities = [
    "💮 Exclusive",
    "🫧 Special Edition",
    "🔮 Limited Edition",
    "🎐 Celestial",
    "🎄 Christmas",
    "💘 Valentine",
    "💋 [𝙓] 𝙑𝙚𝙧𝙨𝙚",
    "🔞 NSFW",
    "💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]",
]


for module_name in ALL_MODULES:
    imported_module = importlib.import_module("shivu.modules." + module_name)


last_user = {}
warned_users = {}
def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

async def message_counter(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        
        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        if chat_frequency:
            message_frequency = chat_frequency.get('message_frequency', 100)
        else:
            message_frequency = 30

        # Check if the message is sent in the specified group ID
        if chat_id ==  6783092268:
            r.hincrby(f'user:{user_id}', 'charm', 0)
        else:
            r.hincrby(f'user:{user_id}', 'charm', 0)
        
        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 5000:
            
                if user_id in warned_users and time.time() - warned_users[user_id] < 600:
                    return
                else:
                    
                    await update.message.reply_text(f"⚠️ Don't Spam {update.effective_user.first_name}...\nYour Messages Will be ignored for 10 Minutes...")
                    warned_users[user_id] = time.time()
                    return
        else:
            last_user[chat_id] = {'user_id': user_id, 'count': 1}

    
        if chat_id in message_counts:
            message_counts[chat_id] += 1
        else:
            message_counts[chat_id] = 1

    
        if message_counts[chat_id] % message_frequency == 0:
            await send_image(update, context)
            
            message_counts[chat_id] = 0
            


async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    all_characters = list(await collection.find({}).to_list(length=None))
    
    if chat_id not in sent_characters:
        sent_characters[chat_id] = []

    if chat_id in zen_dict:
        del zen_dict[chat_id]
        

    if len(sent_characters[chat_id]) == len(all_characters):
        sent_characters[chat_id] = []

    character = random.choice([c for c in all_characters if c['id'] not in sent_characters[chat_id]])

    sent_characters[chat_id].append(character['id'])
    last_characters[chat_id] = character
    zen_dict[chat_id] = character['name'] 
    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=character['img_url'],
        caption=f"""A New {character['rarity']}  ᴡᴀɪғᴜ ʜᴀs ᴀᴘᴘᴇᴀʀᴇᴅ!
ǫᴜɪᴄᴋ! ᴜsᴇ..../grab ɴᴀᴍᴇ ᴛᴏ ᴀᴅᴅ ʜᴇʀ ᴛᴏ ʏᴏᴜʀ ʜᴀʀᴇᴍ!""",
        parse_mode='Markdown')

async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in last_characters:
        return

    if chat_id in first_correct_guesses:
        return
        

    user_info_key = f'user:{user_id}'
    if not r.exists(user_info_key):
        r.hincrby(user_info_key, 'charm', 25000)
        await update.message.reply_text('<b>You claimed <code>25000 </code>Charms</b>.', parse_mode='html')

    guess = ' '.join(context.args).lower() if context.args else ''
    
    if "()" in guess or "&" in guess.lower():
        await update.message.reply_text("You Can't use This Types of words in your guess..")
        return

    name_parts = last_characters[chat_id]['name'].lower().split()

    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):
        first_correct_guesses[chat_id] = user_id

        # Increment charms by 50 upon correct guess
        r.hincrby(user_info_key, 'charm', 500)

        user = await user_collection.find_one({'id': user_id})
        
        keyboard = [[InlineKeyboardButton(f" ⟭⟬ ᴄᴏɴᴄᴜʙɪɴᴇs", switch_inline_query_current_chat=f"collection.{user_id}")]]
        await update.message.reply_text(f'<b><a href="tg://user?id={user_id}">{escape(update.effective_user.first_name)}</a></b> You Guessed a New Character ✅️ \n\n𝗡𝗔𝗠𝗘: <b>{last_characters[chat_id]["name"]}</b> \n𝗔𝗡𝗜𝗠𝗘: <b>{last_characters[chat_id]["anime"]}</b> \n𝗥𝗔𝗜𝗥𝗧𝗬: <b>{last_characters[chat_id]["rarity"]}</b>\n\nThis Character added in Your harem.. use /harem To see your harem', parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

        if user:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != user.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != user.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await user_collection.update_one({'id': user_id}, {'$set': update_fields})
            
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': last_characters[chat_id]}})
      
        elif hasattr(update.effective_user, 'username'):
            await user_collection.insert_one({
                'id': user_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'characters': [last_characters[chat_id]],
            })

        group_user_total = await group_user_totals_collection.find_one({'user_id': user_id, 'group_id': chat_id})
        if group_user_total:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != group_user_total.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != group_user_total.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$set': update_fields})
            
            await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$inc': {'count': 1}})
      
        else:
            await group_user_totals_collection.insert_one({
                'user_id': user_id,
                'group_id': chat_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'count': 1,
            })

        group_info = await top_global_groups_collection.find_one({'group_id': chat_id})
        if group_info:
            update_fields = {}
            if update.effective_chat.title != group_info.get('group_name'):
                update_fields['group_name'] = update.effective_chat.title
            if update_fields:
                await top_global_groups_collection.update_one({'group_id': chat_id}, {'$set': update_fields})
            
            await top_global_groups_collection.update_one({'group_id': chat_id}, {'$inc': {'count': 1}})
      
        else:
            await top_global_groups_collection.insert_one({
                'group_id': chat_id,
                'group_name': update.effective_chat.title,
                'count': 1,
            })


        if chat_id in zen_dict:
            del zen_dict[chat_id]
            
    else:
        await update.message.reply_text('rip, that\'s not quite right...')

async def fav(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    
    if not context.args:
        await update.message.reply_text('Please provide Character id...')
        return

    character_id = context.args[0]

    
    user = await user_collection.find_one({'id': user_id})
    if not user:
        await update.message.reply_text('You have not Guessed any characters yet....')
        return


    character = next((c for c in user['characters'] if c['id'] == character_id), None)
    if not character:
        await update.message.reply_text('This Character is Not In your collection')
        return

    
    user['favorites'] = [character_id]

    
    await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})

    await update.message.reply_text(f'Character {character["name"]} has been added to your favorite...')

async def store_character(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    if chat_id not in zen_dict:
        return

    character_name = zen_dict[chat_id]  # Retrieve the stored name
      # Clear the entry after sending

    await update.message.reply_text(f'<b>Character name</b>: <code>{character_name}</code>\n\n<b>Copy-String</b>: <code>/protecc {character_name}</code>',parse_mode='html') # Send the corrected message 

async def get_charm_count(user_id: int) -> int:
    """Get the charm count for a user."""
    user_info_key = f'user:{user_id}'
    charm_count = r.hget(user_info_key, 'charm')
    return int(charm_count) if charm_count else 0

async def send_charm_count(update: Update, context: CallbackContext) -> None:
    """Send the formatted charm count message to the user."""
    user_id = update.effective_user.id
    charm_count = await get_charm_count(user_id)
    
    locale.setlocale(locale.LC_ALL, '')  # Set the locale to the system's default
    formatted_charm_count = locale.format_string("%d", charm_count, grouping=True)

    message = (
        f"<b>┏━┅┅┄┄⟞⟦🎐⟧⟝┄┄┉┉━┓\n"
        f"┣ ¢нαямѕ ˹𝕮𝖔𝖚𝖓𝖙˼</b> <code>➾ {formatted_charm_count}</code>\n"
        f"┗━┅┅┄┄⟞⟦🎐⟧⟝┄┄┉┉━┛\n"
    )
    await update.message.reply_text(message, parse_mode='html')
    LOGGER.info("Sex")

async def dong(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(f"Hmmm... I think you might find something interesting over at: https://telegra.ph/file/9984fc1ee8bfe50d4ff30.jpg. 😉 Just be sure to open it discreetly!")


async def sss(update, context):
    # URL to be displayed without being parsed as a link
    url = "https://telegra.ph/file/9984fc1ee8bfe50d4ff30.jpg"
    
    # Message with the escaped URL
    escaped_url = '\u200B'.join(url)  # Insert zero-width characters between each character in the URL
    message = f"Here is the URL: {escaped_url}"
    
    # Send the message with the escaped URL
    await update.message.reply_text(message)


def main() -> None:
    """Run bot."""

    application.add_handler(CommandHandler(["protecc", "collect", "grab", "hunt"], guess, block=False))
    application.add_handler(CommandHandler("fav", fav, block=False))
    application.add_handler(CommandHandler("s", store_character, block=False))
    application.add_handler(CommandHandler("charms", send_charm_count, block=False))
    application.add_handler(MessageHandler(filters.ALL, message_counter, block=False))
    application.add_handler(CommandHandler("dong", sss))
    application.add_handler(CommandHandler("charm", send_charm_count, block=False))
    application.run_polling(drop_pending_updates=True)
    
if __name__ == "__main__":
    shivuu.start()
    LOGGER.info("Bot started")
    main()
