import os
import random
import html

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
import redis

from shivu import shivuu
from shivu import (application, PHOTO_URL, OWNER_ID,
                    user_collection, top_global_groups_collection, top_global_groups_collection, 
                    group_user_totals_collection)

from shivu import sudo_users as SUDO_USERS 
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler
from telegram.ext import *

# Redis connection setup
r = redis.Redis(
    host='redis-13192.c282.east-us-mz.azure.cloud.redislabs.com',
    port=13192,
    password='wKgGC52NC9NRhic36fDIvWh76dngPvP9')

async def tops(update: Update, context: CallbackContext) -> None:
    try:
        # Fetch charm counts for all users
        user_charms = {}
        all_user_ids = r.smembers("user_ids")  # Assuming user IDs are stored in a Redis set

        for user_id in all_user_ids:
            charms = r.hget("user:" + user_id.decode('utf-8'), 'charms')
            if charms is not None:
                user_charms[user_id.decode('utf-8')] = int(charms)

        # Sort users by charm counts in descending order
        sorted_users = sorted(user_charms.items(), key=lambda x: x[1], reverse=True)

        if not sorted_users:
            await update.message.reply_text('No data found for leaderboard.')
            return

        leaderboard_message = "<b>Top Charms Leaderboard</b>\n\n"

        for i, (user_id, charms) in enumerate(sorted_users[:10], start=1):
            user_info_key = "user:" + user_id
            username = r.hget(user_info_key, 'username').decode('utf-8')
            first_name = r.hget(user_info_key, 'first_name').decode('utf-8')
            ranking = i  # Ranking is based on the sorted list

            if len(first_name) > 10:
                first_name = first_name[:12] + '...'
            leaderboard_message += f'{ranking}. <a href="https://t.me/{username}">{first_name}</a> ➾ Charms: <code>{charms}</code>\n'

        photo_url = random.choice(PHOTO_URL)

        # Setup inline buttons
        keyboard = [[InlineKeyboardButton("🚮 Delete", callback_data='delete')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send message with inline buttons
        message = await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML', reply_markup=reply_markup)
        
        # Store the message ID for later deletion
        context.user_data['message_to_delete'] = message.message_id
    except Exception as e:
        print(f"Error in tops function: {e}")
        await update.message.reply_text('An error occurred while fetching the leaderboard.')

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == 'delete':
        # Delete the message using the stored message ID
        message_to_delete = context.user_data.get('message_to_delete')
        if message_to_delete:
            try:
                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=message_to_delete)
            except Exception as e:
                print(f"Error deleting message: {e}")
        else:
            print("Message to delete not found.")

# Add the command and callback handlers
application.add_handler(CommandHandler('tops', tops, block=False))
application.add_handler(CallbackQueryHandler(button))
