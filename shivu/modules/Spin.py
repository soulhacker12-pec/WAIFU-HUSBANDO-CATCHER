import random
import time
import asyncio
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
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
            # Handle if user doesn't have enough charms
            raise ValueError('Insufficient charms')

async def check_spin_rate(chat_id):
    # Get the current timestamp
    current_time = time.time()

    # Check if there is an entry for this chat ID in Redis
    if r.hexists('spin_rate_limit', chat_id):
        # Get the previous timestamp and request count
        prev_timestamp, request_count = map(int, r.hmget('spin_rate_limit', chat_id))
        # Calculate the time difference in seconds
        time_diff = current_time - prev_timestamp

        # If less than 60 seconds have passed, check the request count
        if time_diff < 60:
            if request_count >= 15:
                return False  # Limit exceeded
            else:
                # Increment the request count
                r.hset('spin_rate_limit', chat_id, current_time, request_count + 1)
        else:
            # Reset the request count and update the timestamp
            r.hset('spin_rate_limit', chat_id, current_time, 1)
    else:
        # First request from this chat ID
        r.hset('spin_rate_limit', chat_id, current_time, 1)

    return True  # Request within limits

async def spin(update: Update, context: CallbackContext) -> None:
    try:
        chat_id = update.effective_chat.id
        within_limits = await check_spin_rate(chat_id)
        
        if not within_limits:
            await update.message.reply_text('You have reached the spin rate limit. Please wait before spinning again.')
            return
        
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

        # Check if the user has sufficient charms for the spin
        user_id = update.effective_user.id
        charms_needed = 200 * spin_count
        sufficient_charms = await check_sufficient_charms(user_id, charms_needed)

        if not sufficient_charms:
            await update.message.reply_text('You do not have enough charms for this spin.')
            return

        all_waifus = await collection.find({}).to_list(length=None)
        random.shuffle(all_waifus)
        waifus = all_waifus[:spin_count]

        if waifus:
            # Add the waifus obtained from spin to the user's collection
            await add_waifu_to_user(user_id, waifus)

            reply_message = "\n".join([f'˹✘˼ <b>ᴀɴɪᴍᴇ</b>: <code>{waifu["name"]}</code>\n˹✘˼ <b>ᴀɴɪᴍᴇ</b>: <code>{waifu["anime"]}</code>\n˹✘˼ <b>ʀᴀʀɪᴛʏ</b> <code>{waifu["rarity"]}</code>\n\n' for waifu in waifus])
            await update.message.reply_text(reply_message, parse_mode='html')
        else:
            await update.message.reply_text('No waifus found.')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

async def check_sufficient_charms(user_id, charms_needed):
    user_info_key = f'user:{user_id}'
    current_charms = r.hget(user_info_key, 'charm')
    if current_charms:
        current_charms = int(current_charms)
        return current_charms >= charms_needed
    return False

SPIN_HANDLER = CommandHandler('spin', spin, block=False)
application.add_handler(SPIN_HANDLER)
