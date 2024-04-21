import asyncio
from shivu import application 
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler 
import redis
import html

# Redis connection setup
r = redis.Redis(
    host='redis-13192.c282.east-us-mz.azure.cloud.redislabs.com',
    port=13192,
    password='wKgGC52NC9NRhic36fDIvWh76dngPvP9')


async def roll(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Cooldown Handling
    cooldown_key = f'user:{user_id}:cooldown'  # Specific cooldown key
    last_reward_time = r.get(cooldown_key)
    if last_reward_time:
        cooldown_seconds = 60 - (time.time() - float(last_reward_time))
        await update.message.reply_text(f'<b>Try again in {int(cooldown_seconds)} seconds.</b>', parse_mode='html')
        return  # Exit if on cooldown 

    # Roll Logic
    roll_result = random.randint(1, 6)
    reward = random.randint(500, 2000)
    user_info_key = f'user:{user_id}'

    if not r.exists(user_info_key): 
        r.hset(user_info_key, 'charms', 50000)  # Initialize if needed 
    
    if random.random() < 0.45:  # 45% chance
        await update.message.reply_text('Better luck next time!')
    else:
        r.hincrby(user_info_key, 'charms', reward)
        await update.message.reply_dice('🎲') 
        await update.message.reply_text(
            f'You rolled and earned {reward} charms!',parse_mode='html', 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎲", callback_data=str(roll_result))]])
        )

    r.setex(cooldown_key, 60, time.time())  



application.add_handler(CommandHandler("l", roll))
