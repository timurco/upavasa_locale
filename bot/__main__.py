# Enable relative imports https://fortierq.github.io/python-import/
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parents[1]))

from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from bot.conversations.admin_commands import *
from bot.conversations import ADMIN_MESSAGE, ADMIN_CONFIRM
from bot.conversations.commands import *
from bot.conversations.days import *
from bot.conversations.fasting import *
from bot.conversations.locations import *
from bot.conversations.notifications import every_time

application = Application.builder().token(settings.token).build()
application.add_error_handler(error_handler)
application.add_handler(CommandHandler("help", help))
application.add_handler(CommandHandler("donate", donate))
application.add_handler(CommandHandler('stop', stop))
application.add_handler(CommandHandler('get_fasting', demand_fasting))
# admin commands
application.add_handler(CommandHandler('admin_cancel', admin_cancel))
application.add_handler(CommandHandler('admin_preview', admin_preview))
application.add_handler(CommandHandler('admin_tithi', admin_tithi))
application.add_handler(CommandHandler('admin_get_users', admin_get_users))

# admin send conversation
application.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler('admin_send', admin_send_start)],
        states={
            ADMIN_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_send_message),
            ],
            ADMIN_CONFIRM: [
                CallbackQueryHandler(admin_send_confirm, pattern="^admin_send_confirm$"),
                CallbackQueryHandler(admin_send_confirm, pattern="^admin_send_cancel$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", admin_send_cancel),
            CommandHandler("admin_send", admin_send_start),
        ]
    )
)

application.add_handler(
    ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler('update_location', update_location),
            CommandHandler('update_days', update_days)
        ],
        states={
            LOCATION: [
                MessageHandler(filters.LOCATION, location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, text_location),
            ],
            DAYS: [
                CallbackQueryHandler(ekadashi, pattern="^" + str(EKADASHI) + "$"),
                CallbackQueryHandler(all_days, pattern="^" + str(ALLDAYS) + "$"),
                CallbackQueryHandler(cancel, pattern="^" + str(CANCEL) + "$"),
                CallbackQueryHandler(no_send, pattern="^" + str(ZERODAYS) + "$")
            ],
            LOC_CONFIRMATION: [
                CallbackQueryHandler(location, pattern="^" + str(YES) + "$"),
                CallbackQueryHandler(cancel, pattern="^" + str(CANCEL) + "$"),
                CallbackQueryHandler(no_location, pattern="^" + str(NO) + "$"),
            ],
            SET_LOCATION: [
                MessageHandler(filters.LOCATION | filters.TEXT & ~filters.COMMAND, set_location)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern="^" + str(CANCEL) + "$"),
            CommandHandler("cancel", cancel),
            CommandHandler("help", help),
            CommandHandler("donate", donate),
            CommandHandler('stop', stop),
            CommandHandler('start', start),
            CommandHandler('get_fasting', demand_fasting),
            CommandHandler('update_location', update_location),
            CommandHandler('update_days', update_days)
        ]
    )
)
# interval - в секундах, first - через сколько первый запуск
application.job_queue.run_repeating(every_time, interval=settings.interval, first=1)
# Run the bot until the user presses Ctrl-C
application.run_polling()
