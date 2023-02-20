import i18n
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler

from bot import db, User
from bot.conversations import *
from bot.conversations.commands import set_record
from bot.utils.phrases import okay


async def ekadashi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    i18n.set("locale", user.lang_code if user else update.effective_user.language_code)

    context.user_data['days'] = 1
    msg = okay() + t('phrases.ready_to_send', days=t('words.ekadashi'))
    msg += '\n'
    msg += t('phrases.days_update')
    await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML)
    return await set_record(update, context)


async def all_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    i18n.set("locale", user.lang_code if user else update.effective_user.language_code)
    context.user_data['days'] = 2
    await set_record(update, context)
    msg = okay() + t('phrases.ready_to_send', days=all_days_string())
    msg += '\n'
    msg += t('phrases.days_update')
    await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


async def update_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    if not user:
        i18n.set("locale", update.effective_user.language_code)
        await update.message.reply_text(t('phrases.location_first'), parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    i18n.set("locale", user.lang_code)
    msg = okay()
    msg += t('phrases.start_choose_day', and_now=t('words._and_now'))
    await update.message.reply_text(msg, reply_markup=get_days_keyboard())

    return DAYS
