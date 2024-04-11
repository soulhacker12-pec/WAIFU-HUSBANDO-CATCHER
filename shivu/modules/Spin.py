import random
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
import html
# Assuming these are already defined in your existing code
from shivu import application, collection, user_collection
import redis

# Redis connection setup
r = redis.Redis(
    host='redis-13192.c282.east-us-mz.azure.cloud.redislabs.com',
    port=13192,
    password='wKgGC52NC9NRhic36fDIvWh76dngPvP9')

async def add_waifu_to_user(user_id, waifus):
    user = await user_collection.find_one({'id': user_id})
    if user:
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': {'$each': waifus}}})
        await deduct_charms(user_id, 200 * len(waifus))  # Deduct 250 charms for each waifu added
    else:
        await user_collection.insert_one({'id': user_id, 'characters': waifus})

async def deduct_charms(user_id, amount):
    user_info_key = f'user:{user_id}'
    current_charms = r.hget(user_info_key, 'charm')
    if current_charms:
        current_charms = int(current_charms)
        if current_charms >= amount:
            r.hincrby(user_info_key, 'charm', -amount)  # Deduct the specified amount of charms
        else:
            
            # For example, send a message to the user or take appropriate action
            pass
    else:
        # Handle if user has no charm data
        pass

async def spin(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Incorrect format. Please use: /spin {number}')
            return

        spin_count = int(args[0])
        if spin_count <= 0:
            await update.message.reply_text('Please enter a positive number for spins.')
            return
        elif spin_count > 10:
            await update.message.reply_text('You can only spin up to 10 times.')
            return

        all_waifus = await collection.find({}).to_list(length=None)
        random.shuffle(all_waifus)
        waifus = all_waifus[:spin_count]

        if waifus:
            # Add the waifus obtained from spin to the user's collection
            user_id = update.effective_user.id
            await add_waifu_to_user(user_id, waifus)

            reply_message = "\n".join([f'˹✘˼ <b>ᴀɴɪᴍᴇ</b>: <code>{waifu["name"]}</code>\n˹✘˼ <b>ᴀɴɪᴍᴇ</b>: <code>{waifu["anime"]}</code>\n˹✘˼ <b>ʀᴀʀɪᴛʏ</b> <code>{waifu["rarity"]}</code>\n\n' for waifu in waifus])
            await update.message.reply_text(reply_message,parse_mode='html')
        else:
            await update.message.reply_text('No waifus found.')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

SPIN_HANDLER = CommandHandler('spin', spin, block=False)
application.add_handler(SPIN_HANDLER)
