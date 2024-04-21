import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
import asyncio
from shivu import application 
import redis

# Cooldown Tracking (in-memory for demonstration)
last_roll_reward = {}  # {user_id: timestamp}

# Redis connection setup
r = redis.Redis(
    host='redis-13192.c282.east-us-mz.azure.cloud.redislabs.com',
    port=13192,
    password='wKgGC52NC9NRhic36fDIvWh76dngPvP9')

async def roll(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if can_earn_reward(user_id):
        roll_result = random.randint(1, 6)
        reward = random.randint(500, 2000)
        user_info_key = f'user:{user_id}'
        r.setex(user_info_key, 60, time.time())
        r.hincrby(user_info_key, +reward)


        # Stage 1: Send the rolling dice
        await update.message.reply_dice(emoji='🎲')  

        # Stage 2: Send the result and rewards
        keyboard = [[InlineKeyboardButton("🎲", callback_data=str(roll_result))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f'You rolled and earned {reward} charms!', reply_markup=reply_markup)

        last_roll_reward[user_id] = time.time()
    else:
        await update.message.reply_text('Please wait before rolling again for rewards.')


async def can_earn_reward(user_id):
    if user_id not in last_roll_reward:
        return True  # First roll is allowed

    last_reward_time = last_roll_reward[user_id]
    current_time = time.time()
    return current_time - last_reward_time >= 60  # 60 seconds cooldown

# ... Your other bot setup code 

application.add_handler(CommandHandler("rolal", roll))
