from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application
import redis

# Redis connection setup
r = redis.Redis(
    host='redis-13192.c282.east-us-mz.azure.cloud.redislabs.com',
    port=13192,
    password='wKgGC52NC9NRhic36fDIvWh76dngPvP9')

async def update_charms(update: Update, context: CallbackContext, operation: str) -> None:
    try:
        args = context.args
        if not args or len(args) != 2:
            await update.message.reply_text('Incorrect format. Please use: /xbf827 <userid> <amount>')
            return

        user_id, amount = args[0], int(args[1])
        if amount <= 0:
            await update.message.reply_text('Please enter a positive amount.')
            return

        await modify_charms(user_id, amount, operation)

        if operation == 'increase':
            await update.message.reply_text(f'Charms count for user {user_id} increased by {amount}.')
        elif operation == 'decrease':
            await update.message.reply_text(f'Charms count for user {user_id} decreased by {amount}.')
    except ValueError:
        await update.message.reply_text('Invalid amount. Please enter a valid number.')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

async def modify_charms(user_id, amount, operation):
    user_info_key = f'user:{user_id}'
    if operation == 'increase':
        r.hincrby(user_info_key, 'charm', amount)
    elif operation == 'decrease':
        r.hincrby(user_info_key, 'charm', -amount)

INCREASE_CHARMS_HANDLER = CommandHandler('gg222', lambda update, context: update_charms(update, context, 'increase'))
DECREASE_CHARMS_HANDLER = CommandHandler('bb222', lambda update, context: update_charms(update, context, 'decrease'))

application.add_handler(INCREASE_CHARMS_HANDLER)
application.add_handler(DECREASE_CHARMS_HANDLER)
