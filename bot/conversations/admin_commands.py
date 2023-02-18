import i18n
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from bot import db
from bot.conversations import *
from bot.conversations.notifications import every_time
from bot.utils import *


async def admin_notify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END
    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    i18n.set("locale", update.effective_user.language_code)
    await every_time(context, safe=False)
    return ConversationHandler.END
