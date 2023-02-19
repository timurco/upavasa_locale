import i18n
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler

from bot import db, User
from bot.conversations import *
from bot.conversations.commands import start, set_record
from bot.services.weather import get_city
from bot.settings import settings
from bot.utils.phrases import okay


async def no_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    i18n.set("locale", update.effective_user.language_code)
    msg = t('phrases.try_again')
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(msg)
        except:
            await update.callback_query.delete_message()
            await context.bot.send_message(update.effective_user.id, msg)
    else:
        await update.message.reply_text(msg)
    return LOCATION


async def text_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    i18n.set("locale", update.effective_user.language_code)
    message = await update.message.reply_text(t('words._moment'))
    loc = await get_city(update.message.text)

    if not loc:
        await message.edit_text(t('phrases.something_wrong') + '. ' + t('phrases.try_again'))
        return LOCATION

    context.user_data['probably_location'] = loc
    await message.delete()
    await update.message.reply_location(loc[0], loc[1])
    await update.message.reply_text(t('phrases.check_location'), reply_markup=get_confirm_keyboard())
    return LOC_CONFIRMATION


async def update_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    if not user:
        return await start(update, context)

    i18n.set("locale", user.lang_code)
    msg = okay() + t('phrases.start_choose_location')
    if update.callback_query:
        await context.bot.send_photo(
            update.callback_query.from_user.id, settings.location_pic, msg, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_photo(settings.location_pic, msg, parse_mode=ParseMode.HTML)
    return SET_LOCATION


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    i18n.set("locale", update.effective_user.language_code)
    if update.callback_query and int(update.callback_query.data) == YES:
        context.user_data['location'] = context.user_data['probably_location']
    else:
        user_location = update.message.location
        context.user_data['location'] = [user_location.latitude, user_location.longitude]

    msg = okay() + t('phrases.location_update')
    msg += '\n'
    msg += t('phrases.start_choose_day', and_now=t('words._and_now'))
    if 'skip_days' in context.user_data.keys():
        await set_record(update, context)
        await update.callback_query.edit_message_text(okay() + t('phrases.set_location'), parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=get_days_keyboard())
    else:
        await update.message.reply_text(msg, reply_markup=get_days_keyboard())

    return DAYS


async def set_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    if not update.message.location and update.message.text:
        context.user_data['skip_days'] = True
        return await text_location(update, context)

    user_location = update.message.location
    context.user_data['location'] = [user_location.latitude, user_location.longitude]

    await set_record(update, context)
    await update.message.reply_text(okay() + t('phrases.set_location'), parse_mode=ParseMode.HTML)

    return ConversationHandler.END
