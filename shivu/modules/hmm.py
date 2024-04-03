import asyncio  
from shivu import *
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext


def create_delete_button():
    keyboard = [[InlineKeyboardButton("🚮", callback_data="delete_message")]]
    return InlineKeyboardMarkup(keyboard)

@shivuu.on_callback_query(filters.create(lambda _, __, query: query.data == "delete_message"))
async def delete_message_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query

    # Delete the original message
    await query.message.delete()

    # Optional: Send a confirmation message (with a slight modification for clarity)
    confirmation_msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="Message deleted!") 
    await asyncio.sleep(2)  # Delay for 2 seconds
    await confirmation_msg.delete() 
