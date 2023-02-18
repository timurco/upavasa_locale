import datetime
import html
import json
import traceback

import i18n
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler, CallbackContext

from bot import db, emo, logger
from bot.conversations import *
from bot.utils import *
from bot.utils.emo import sad
from bot.utils.phrases import namaskar, okay


async def error_handler(update: object, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    # context_str = context.
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>\n'
        # f'<pre>context = {html.escape(json.dumps(context_str, indent=2, ensure_ascii=False))}</pre>\n'
        f'\n<pre>{html.escape(tb_string)}</pre>'
    )

    # Finally, send the message
    await context.bot.send_message(chat_id=settings.developer, text=message, parse_mode='HTML')


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    i18n.set("locale", update.effective_user.language_code)
    msg = t('info.help',
            mission=t('phrases.mission'),
            my_name=t('phrases.my_name', name=t('words.name')))
    await context.bot.send_message(update.effective_user.id, msg, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    i18n.set("locale", update.effective_user.language_code)
    msg = t('info.donate')
    await context.bot.send_message(update.effective_user.id, msg, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    i18n.set("locale", user.language_code)
    msg = namaskar('%s') % user.mention_html()
    msg += '\n'
    msg += t('phrases.mission')
    msg += '\n'
    msg += t('phrases.start_choose_location')

    await update.message.reply_photo(
        settings.location_pic,
        msg,
        parse_mode=ParseMode.HTML,
    )
    logger.info(user)
    context.user_data.clear()
    return LOCATION


async def set_record(update: Update, context: ContextTypes.DEFAULT_TYPE, active: bool = True) -> int:
    i18n.set("locale", update.effective_user.language_code)
    logger.info(f"Пробуем добавить или изменить нового пользователя: {context.user_data}")
    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    if user:
        if 'location' in context.user_data.keys():
            user.lat = str(context.user_data['location'][0])
            user.long = str(context.user_data['location'][1])
        if 'days' in context.user_data.keys():
            user.days = context.user_data['days']
        user.active = active
        logger.info(f"✅️ Пользователь изменил данные: {user}")
        user.last_demand = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
        user.last_touch = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    else:
        user = User(
            tg_id=update.effective_user.id,
            lang_code=update.effective_user.language_code,
            lat=str(context.user_data['location'][0]),
            long=str(context.user_data['location'][1]),
            days=context.user_data['days'],
            active=True,
        )
        logger.info(f"❇️ У нас новый пользователь: {user}")
    db.add(user)
    db.commit()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    i18n.set("locale", update.effective_user.language_code)

    context.user_data.clear()

    if db.query(User).filter_by(tg_id=update.effective_user.id).first():
        msg = okay() + '\n' + t('phrases.again')
    else:
        msg = okay() + t('phrases.no_answer') + emo.get(sad) + '\n' + t('phrases.again')

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(msg)
        except:
            await update.callback_query.delete_message()
            await context.bot.send_message(update.effective_user.id, msg)
    else:
        await update.message.reply_text(msg)
    return ConversationHandler.END


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    i18n.set("locale", update.effective_user.language_code)

    context.user_data.clear()

    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()

    if not user:
        await update.message.reply_text(t('phrases.no_user'))
    else:
        msg = okay() + t('phrases.stop') + '\n' + t('phrases.again')
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(msg)
            except:
                await update.callback_query.delete_message()
                await context.bot.send_message(update.effective_user.id, msg)
        else:
            await update.message.reply_text(msg)

        await set_record(update, context, False)

    return ConversationHandler.END
