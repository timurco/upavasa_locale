import i18n
from telegram import Update
from telegram.ext import ConversationHandler

from bot import db, User
from bot.conversations import *
from bot.conversations.notifications import every_time
from bot.settings import settings


async def admin_notify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END
    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    i18n.set("locale", update.effective_user.language_code)
    await every_time(context, safe=False)
    return ConversationHandler.END
