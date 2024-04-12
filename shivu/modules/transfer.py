from telegram import Update
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
        args = context.args
        if not args or len(args) < 2:
            await update.message.reply_text('Incorrect format. Please use: /transfer <username> <amount>')
            return

        sender = update.effective_user.first_name
        receiver_name = args[0]
        amount = int(args[1])

        if amount <= 0:
            await update.message.reply_text('Please enter a positive amount.')
            return

        await transfer_charms(sender, receiver_name, amount, operation)
        await update.message.reply_text(f'<b>{sender} ᴛʀᴀɴsғᴇʀʀᴇᴅ {amount} ᴄʜᴀʀᴍs ᴛᴏ {receiver_name}.</b>',parse_mode='html')

    except ValueError:
        await update.message.reply_text('Invalid amount. Please enter a valid number.')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

async def transfer_charms(sender_name, receiver_name, amount, operation):
    sender_key = f'user:{sender_name}'
    receiver_key = f'user:{receiver_name}'

    if operation == 'increase':
        r.hincrby(sender_key, 'charm', -amount)
        r.hincrby(receiver_key, 'charm', amount)
    elif operation == 'decrease':
        r.hincrby(sender_key, 'charm', amount)
        r.hincrby(receiver_key, 'charm', -amount)

TRANSFER_HANDLER = CommandHandler('transfer', lambda update, context: update_charms(update, context, 'increase'))
application.add_handler(TRANSFER_HANDLER)
