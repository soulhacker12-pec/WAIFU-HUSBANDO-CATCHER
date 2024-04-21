import asyncio
from shivu import application 
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler 
import redis

# Cooldown Tracking (in-memory for demonstration)
last_roll_reward = {}  # {user_id: timestamp}

# Redis connection setup
r = redis.Redis(
    host='redis-13192.c282.east-us-mz.azure.cloud.redislabs.com',
    port=13192,
    password='wKgGC52NC9NRhic36fDIvWh76dngPvP9')

def can_earn_reward(user_id):
    user_info_key = f'user:{user_id}'
    last_reward_time = r.get(user_info_key) 
    if last_reward_time:
        current_time = time.time()
        return current_time - float(last_reward_time) >= 60
    return True

async def roll(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if can_earn_reward(user_id):
        roll_result = random.randint(1, 6)
        reward = random.randint(500, 2000)
        user_info_key = f'user:{user_id}'
        r.hset(user_info_key, 'charms', 25000)  # Initialize if the hash field doesn't exist
     
        # 45% chance for "better luck next time" directly
        if random.random() < 0.45:  
            await update.message.reply_text('Better luck next time!')
        else:
            r.hincrby(user_info_key, 'charms' , +reward)  

            # Stage 1: Send the rolling dice
            await update.message.reply_dice(emoji='🎲')  

            #Stage 2: Send the result and rewards
            keyboard = [[InlineKeyboardButton("🎲", callback_data=str(roll_result))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f'You rolled and earned {reward} charms!', reply_markup=reply_markup)

        # Set cooldown in Redis
        r.setex(user_info_key, 60, time.time()) 

    else:
        await update.message.reply_text('Please wait before rolling again for rewards.')


# ... Your other bot setup code 

application.add_handler(CommandHandler("rolal", roll))
