import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import application, collection, user_collection
import redis

# Redis connection setup
r = redis.Redis(
    host='redis-13192.c282.east-us-mz.azure.cloud.redislabs.com',
    port=13192,
    password='wKgGC52NC9NRhic36fDIvWh76dngPvP9'
)

async def set_collection(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    keyboard = [
        [
            InlineKeyboardButton("⌠User Collection⌡", callback_data="user_collection"),
            InlineKeyboardButton("⌠Collection 2⌡", callback_data="collection_2"),
            InlineKeyboardButton("⌠Collection 3⌡", callback_data="collection_3"),
        ],
        [
            InlineKeyboardButton("⌠Collection 4⌡", callback_data="collection_4"),
            InlineKeyboardButton("⌠Collection 5⌡", callback_data="collection_5"),
            InlineKeyboardButton("⌠Collection 6⌡", callback_data="collection_6"),
        ],
        [
            InlineKeyboardButton("⌠Collection 7⌡", callback_data="collection_7"),
            InlineKeyboardButton("⌠Collection 8⌡", callback_data="collection_8"),
            InlineKeyboardButton("⌠Collection 9⌡", callback_data="collection_9"),
        ],
        [
            InlineKeyboardButton("⌠Collection 10⌡", callback_data="collection_10"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await update.message.reply_text(
        "Please select a collection:",
        reply_markup=reply_markup
    )


async def select_collection_callback(update: Update, context: CallbackContext) -> None:
    try:
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data

        # Set selected collection in Redis
        r.hset(f"user:{user_id}", "selected_collection", data)
        await query.answer()  # Await the query.answer() coroutine
        await query.edit_message_text(f"You selected collection: {data}")
    except Exception as e:
        print(f"Error in select_collection_callback: {str(e)}")


async def add_waifu_to_user(user_id, waifus, selected_collection):
    try:
        # Here you can use 'selected_collection' to know which collection the user selected
        user = await user_collection.find_one({'id': user_id})
        if user:
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': {'$each': waifus}}})
            await deduct_charms(user_id, 50 * len(waifus))  # Deduct 250 charms for each waifu added
        else:
            await user_collection.insert_one({'id': user_id, 'characters': waifus})
    except Exception as e:
        print(f"Error in add_waifu_to_user: {str(e)}")

async def deduct_charms(user_id, amount):
    try:
        user_info_key = f'user:{user_id}'
        current_charms = r.hget(user_info_key, 'charm')
        if current_charms:
            current_charms = int(current_charms)
            if current_charms >= amount:
                r.hincrby(user_info_key, 'charm', -amount)  # Deduct the specified amount of charms
            else:
                # Handle if user doesn't have enough charms
                raise ValueError('Insufficient charms')
    except Exception as e:
        print(f"Error in deduct_charms: {str(e)}")

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
        elif spin_count > 5000:
            await update.message.reply_text('You can only spin up to 1000 times.')
            return

        # Check if the user has sufficient charms for the spin
        user_id = update.effective_user.id
        charms_needed = 50 * spin_count
        sufficient_charms = await check_sufficient_charms(user_id, charms_needed)

        if not sufficient_charms:
            await update.message.reply_text('You do not have enough charms for this spin.')
            return

        # Get the selected collection from Redis
        selected_collection = r.hget(f"user:{user_id}", "selected_collection")

        all_waifus = await collection.find({}).to_list(length=None)
        random.shuffle(all_waifus)
        waifus = all_waifus[:spin_count]

        if waifus:
            # Add the waifus obtained from spin to the user's collection
            await add_waifu_to_user(user_id, waifus, selected_collection)

            reply_message = "\n".join([f'˹✘˼ <b>ᴀɴɪᴍᴇ</b>: <code>{waifu["name"]}</code>\n˹✘˼ <b>ᴀɴɪᴍᴇ</b>: <code>{waifu["anime"]}</code>\n˹✘˼ <b>ʀᴀʀɪᴛʏ</b> <code>{waifu["rarity"]}</code>\n<b>˹✘˼ 𝐈𝐃</b>: {waifu["id"]}\n\n' for waifu in waifus])

            # Check if reply exceeds 4000 characters or more than 20 waifus
            if len(reply_message) > 4000:
                with open('reply.txt', 'w') as file:
                    file.write(reply_message)
                await update.message.reply_document(document=open('reply.txt', 'rb'), caption='ʀᴇᴘʟʏ ᴛᴇxᴛ ᴇxᴄᴇᴇᴅs ᴛɢ\'s ʟɪᴍɪᴛs. ᴘʟᴇᴀsᴇ ᴄʜᴇᴄᴋ ᴛʜᴇ ғɪʟᴇ, ғᴏʀ ʏᴏᴜʀ ᴅʀᴀᴡɴ ᴡᴀɪғᴜs.')
            else:
                await update.message.reply_text(reply_message, parse_mode='html')
        else:
            await update.message.reply_text('No waifus found.')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

async def check_sufficient_charms(user_id, charms_needed):
    try:
        user_info_key = f'user:{user_id}'
        current_charms = r.hget(user_info_key, 'charm')
        if current_charms:
            current_charms = int(current_charms)
            return current_charms >= charms_needed
        return False
    except Exception as e:
        print(f"Error in check_sufficient_charms: {str(e)}")
        return False

SPIN_HANDLER = CommandHandler('spin', spin, block=False)
application.add_handler(SPIN_HANDLER)

COLLECTION_HANDLER = CommandHandler("select_collection", set_collection)
application.add_handler(COLLECTION_HANDLER)

COLLECTION_CALLBACK_HANDLER = CallbackQueryHandler(select_collection_callback, pattern='^collection_', pass_user_data=True)
application.add_handler(COLLECTION_CALLBACK_HANDLER)
