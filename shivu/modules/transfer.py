from telegram import Update, User
from telegram.ext import CommandHandler, CallbackContext
from shivu import application
import redis
import html

# Redis connection setup
r = redis.Redis(
    host='redis-13192.c282.east-us-mz.azure.cloud.redislabs.com',
    port=13192,
    password='wKgGC52NC9NRhic36fDIvWh76dngPvP9')

async def update_charms(update: Update, context: CallbackContext, operation: str) -> None:
    try:
        sender = update.effective_user
        args = context.args
        if not args or len(args) < 1:
            await update.message.reply_text('Incorrect format. Please use: /transfer <amount> (when replied user) or /transfer <username> <amount>')
            return

        amount = int(args[-1])  # Last argument is always the amount

        if amount <= 0:
            await update.message.reply_text('Please enter a positive amount.')
            return

        # Check if there's a replied user
        if update.message.reply_to_message and update.message.reply_to_message.from_user:
            receiver = update.message.reply_to_message.from_user
        else:
            receiver_name = args[0] if len(args) == 2 else None
            if not receiver_name:
                await update.message.reply_text('Please specify a receiver.')
                return
            receiver = await context.bot.get_chat_member(update.effective_chat.id, receiver_name)
            if receiver.user.is_bot:
                await update.message.reply_text("You can't transfer charms to bots.")
                return

        await transfer_charms(sender, receiver, amount, operation)
        await update.message.reply_text(f'<b>{sender.first_name} ᴛʀᴀɴsғᴇʀʀᴇᴅ {amount} ᴄʜᴀʀᴍs ᴛᴏ <code>{receiver.first_name}</code></b>', parse_mode='html')

    except ValueError:
        await update.message.reply_text('Invalid amount. Please enter a valid number.')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

async def transfer_charms(sender: User, receiver: User, amount: int, operation: str):
    sender_key = f'user:{sender.id}'
    receiver_key = f'user:{receiver.id}'

    if operation == 'increase':
        r.hincrby(sender_key, 'charm', -amount)
        r.hincrby(receiver_key, 'charm', amount)
    elif operation == 'decrease':
        r.hincrby(sender_key, 'charm', amount)
        r.hincrby(receiver_key, 'charm', -amount)

TRANSFER_HANDLER = CommandHandler('transfer', lambda update, context: update_charms(update, context, 'increase'))
application.add_handler(TRANSFER_HANDLER)
