import datetime
import html
import json
import traceback

import i18n
from telegram.ext import ConversationHandler, CallbackContext

from bot import db, emo, logger, User, utils
from bot.conversations import *
from bot.settings import settings
from bot.utils.emo import sad
from bot.utils.phrases import namaskar, okay


async def error_handler(update: object, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""

    # Exclude Network Errors
    if type(context.error).__name__ in ['NetworkError', 'TimedOut']:
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = ''.join(tb_list[-5:])
        logger.trace(f'NetworkError:\n{tb_string}')
        # await context.bot.send_message(
        #     chat_id=settings.developer,
        #     text=f'<b>NetworkError</b>\n<pre>{html.escape(tb_string)}</pre>', parse_mode=ParseMode.HTML)
        return

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

    message = utils.truncate_middle(message)
    # if len(message) > 4096:
    #     for x in range(0, len(message), 4096):
    #         await context.bot.send_message(chat_id=settings.developer, text=message[x:x + 4096], parse_mode='HTML')
    #     return

    # Finally, send the message
    await context.bot.send_message(chat_id=settings.developer, text=message, parse_mode=ParseMode.HTML)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    i18n.set("locale", user.lang_code if user else update.effective_user.language_code)
    msg = t('info.help',
            mission=t('phrases.mission'),
            my_name=t('phrases.my_name', name=t('words.name')))
    await context.bot.send_message(
        update.effective_user.id,
        msg,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True)
    return ConversationHandler.END


async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    i18n.set("locale", user.lang_code if user else update.effective_user.language_code)

    msg = t('info.donate_jamalpur')
    await context.bot.send_message(update.effective_user.id, msg, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()

    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    i18n.set("locale", user.lang_code if user else update.effective_user.language_code)

    msg = namaskar('%s') % update.effective_user.mention_html()
    msg += '\n'
    msg += t('phrases.mission')
    msg += '\n'
    msg += t('phrases.start_choose_location')

    await update.effective_user.send_photo(
        settings.location_pic,
        msg,
        parse_mode=ParseMode.HTML,
    )
    return LOCATION


async def set_record(update: Update, context: ContextTypes.DEFAULT_TYPE, active: bool = True) -> int:
    logger.trace(f"Пробуем добавить или изменить нового пользователя: {context.user_data}")
    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    i18n.set("locale", user.lang_code if user else update.effective_user.language_code)
    new_user = not user
    days = context.user_data['days'] if 'days' in context.user_data.keys() else 0
    if user:
        if 'location' in context.user_data.keys():
            location = [str(context.user_data['location'][0]), str(context.user_data['location'][1])]
            user.lat = location[0]
            user.long = location[1]
        user.days = days
        user.active = active
        username = await get_user_name(user, context)
        logger.info(f"✅️ Пользователь изменил данные: {username}")
        # если пользователь изменил язык
        user.lang_code = update.effective_user.language_code
        user.last_touch = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    else:
        location = [str(context.user_data['location'][0]), str(context.user_data['location'][1])]
        user = User(
            tg_id=update.effective_user.id,
            lang_code=update.effective_user.language_code,
            lat=location[0],
            long=location[1],
            days=days,
            active=True,
            created_at=datetime.datetime.utcnow()
        )
        user.last_demand = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        user.last_touch = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        username = await get_user_name(user, context)
        logger.info(f"❇️ У нас новый пользователь: {username}")
        db.add(user)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        await context.bot.send_message(update.effective_user.id,
                                       t('phrases.something_wrong') + '. ' + t('phrases.try_again') + '... /start')
        raise Exception(
            f"❌ У пользователя {update.effective_user.mention_html()} не получилось зарегистрироваться. Сообщение:{e.__str__()}")
    if new_user:
        await context.bot.send_message(
            settings.developer,
            f"❇️ У нас новый пользователь:\nid: {user.id} – {update.effective_user.mention_html()}",
            parse_mode=ParseMode.HTML,
            disable_notification=True,
        )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    i18n.set("locale", user.lang_code if user else update.effective_user.language_code)

    context.user_data.clear()

    if db.query(User).filter_by(tg_id=update.effective_user.id).first():
        msg = okay() + '\n' + t('phrases.again')
    else:
        msg = okay() + t('phrases.no_answer') + emo.get(sad) + '\n' + t('phrases.again')

    await replace_message(msg, update, context)
    return ConversationHandler.END


async def no_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = okay() + '\n' + t('phrases.no_send')
    await replace_message(msg, update, context)
    await set_record(update, context, active=False)
    return ConversationHandler.END


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()

    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    i18n.set("locale", user.lang_code if user else update.effective_user.language_code)
    if not user:
        await replace_message(t('phrases.no_user'), update, context)
    else:
        msg = okay() + t('phrases.stop') + '\n' + t('phrases.again')
        await replace_message(msg, update, context)
        await set_record(update, context, False)

    return ConversationHandler.END
