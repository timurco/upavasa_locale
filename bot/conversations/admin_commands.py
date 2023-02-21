import i18n
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler

from bot import db, User
from bot.conversations import *
from bot.conversations.notifications import every_time
from bot.services.logger import logger
from bot.services.weather import get_city
from bot.settings import settings
from bot.utils.i18n_start import set_lang
from bot.utils.timezones import get_timezone
from fastings.calculations import calculate_fasting_days


async def admin_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END

    ids = [
        888583726, 184695223, 775274111, 1061480705, 1061480705,
        settings.developer]
    for id in ids:
        try:
            developer = await context.bot.get_chat_member(settings.developer, settings.developer)
            tg_user = await context.bot.get_chat_member(id, id)
            await context.bot.send_message(update.effective_user.id, tg_user)
        except Exception as e:
            logger.error(id)
            logger.error(e)
        # await update.message.reply_text(
        #     f'Намаскар, {tg_user.user.mention_html()}! ' +
        #     'Была ошибка при которой у тебя не получилось зарегистрироваться, ' +
        #     'можешь пожалуйста снова нажать на команду /start чтобы еще раз начать регистрацию? Спасибо!\n\n' +
        #     f'Если что-то не получится, напиши разработчику: {developer.user.mention_html()}',
        #     parse_mode=ParseMode.HTML
        # )
        context.user_data.clear()

    return ConversationHandler.END


async def admin_notify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END

    i18n.set("locale", update.effective_user.language_code)
    if not await every_time(context, safe=False):
        await update.message.reply_text("Возможно еще рано оповещать или ближайшее титхи не то, которое ты выбрал...")
    return ConversationHandler.END


async def admin_tithi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END

    msg_input = update.message.text.split(" ", 1)

    if len(msg_input) != 2:
        await update.message.reply_text("Город после команды")
        return ConversationHandler.END

    set_lang(update.effective_user.language_code)

    loc = await get_city(msg_input[1])
    if not loc:
        await update.message.reply_text(t('phrases.something_wrong') + '. ' + t('phrases.try_again'))
        return ConversationHandler.END

    tz = get_timezone(loc[0], loc[1])
    # Делаем более точный перерасчёт
    f = calculate_fasting_days(tz.place)
    fasting_message = ""

    for _, fasting in f.iterrows():
        is_ekadashi = fasting['tithi'] == 'ekadashi'
        this_row = '\n' + t('words.' + fasting['tithi'], count=1).capitalize()
        this_row += ":\n⌚ {:%-d %B, %H:%M} – ⌚ {:%-d %B, %H:%M}".format(
            fasting['starts'],
            fasting['ends'])
        fasting_message += '<b>' + this_row + '</b>' if is_ekadashi else this_row

    msg = t('words.regarding', place=tz.place) + ':'
    msg += fasting_message
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    return ConversationHandler.END