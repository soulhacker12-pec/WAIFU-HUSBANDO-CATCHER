from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application
import redis

# Redis connection setup
r = redis.Redis(
    host='redis-13192.c282.east-us-mz.azure.cloud.redislabs.com',
    port=13192,
    password='wKgGC52NC9NRhic36fDIvWh76dngPvP9')

async def increase_charms(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        if not args or len(args) != 1:
            await update.message.reply_text('Incorrect format. Please use: /xbf827 {amount}')
            return

        amount = int(args[0])
        if amount <= 0:
            await update.message.reply_text('Please enter a positive amount to increase charms count.')
            return

        user_id = update.effective_user.id
        await add_charms(user_id, amount)

        await update.message.reply_text(f'Charms count increased by {amount}.')
    except ValueError:
        await update.message.reply_text('Invalid amount. Please enter a valid number.')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

async def add_charms(user_id, amount):
    user_info_key = f'user:{user_id}'
    r.hincrby(user_info_key, 'charm', amount)

CHARMS_COUNT_HANDLER = CommandHandler('xbf827', increase_charms)
application.add_handler(CHARMS_COUNT_HANDLER)
