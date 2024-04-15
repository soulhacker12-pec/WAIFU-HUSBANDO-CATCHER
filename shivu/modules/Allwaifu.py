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

from shivu import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, shivuu
from shivu import application, SUPPORT_CHAT, UPDATE_CHAT, db, LOGGER
from shivu.modules import ALL_MODULES
import redis

import os

async def all_waifu(update: Update, context: CallbackContext) -> None:
    all_characters = await collection.find({}).to_list(length=None)

    if not all_characters:
        await update.message.reply_text("No waifu data found.")
        return

    file_name = "allwaifu.txt"
    with open(file_name, "w", encoding="utf-8") as file:
        for character in all_characters:
            file.write(f"Name: {character['name']}\n")
            file.write(f"Anime: {character['anime']}\n")
            file.write(f"Rarity: {character['rarity']}\n")
            file.write(f"Img_url: {character['img_url']}\n")
            file.write(f"Character_id: {character['id']}\n\n")

    # Send the file to the chat
    with open(file_name, "rb") as file:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=file)

    # Delete the file locally after sending
    os.remove(file_name)

    await update.message.reply_text("Take this allwaifu.txt file.")

application.add_handler(CommandHandler("allwaifu", all_waifu, block=False))
