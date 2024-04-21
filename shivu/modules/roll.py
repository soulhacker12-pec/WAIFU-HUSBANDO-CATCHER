import asyncio
from shivu import application 
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler 
import redis
import html

# Cooldown Tracking (in-memory for demonstration)
last_roll_reward = {}  # {user_id: timestamp}

# Redis connection setup
r = redis.Redis(
    host='redis-13192.c282.east-us-mz.azure.cloud.redislabs.com',
    port=13192,
    password='wKgGC52NC9NRhic36fDIvWh76dngPvP9')


def can_earn_reward(user_id):
    key = f'user:{user_id}'
    key2 = f'user:{user_id}x'
    last_reward_time = r.get(key)
    if last_reward_time:
        cooldown_seconds = 60 - (time.time() - float(last_reward_time))
        return False, cooldown_seconds
    return True, 0  


async def roll(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    ready, cooldown_seconds = can_earn_reward(user_id)

    if ready:
        roll_result = random.randint(1, 6)
        reward = random.randint(500, 2000)
        key = f'user:{user_id}'
        if not r.exists(key): 
          r.hset(key, 'charm', 50000)
         # Initialize if needed 
        
        if random.random() < 0.45:  # 45% chance
            await update.message.reply_text('Better luck next time!')
        else:
            r.hincrby(key, 'charm', reward)
            await update.message.reply_dice('🎲') 
            await update.message.reply_text(
                f'<b>You rolled and earned {reward} charms!</b>',parse_mode='html', 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎲", callback_data=str(roll_result))]])
            )
        r.setex(key2, 60, time.time()) 
    else:
        await update.message.reply_text(f'<b>Try again in {int(cooldown_seconds)} seconds.</b>',parse_mode='html')


# ... Your other bot setup code 

application.add_handler(CommandHandler("rolal", roll))
