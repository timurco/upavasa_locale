import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from bot import User, emo, logger, db
from bot.conversations import get_user_name
from bot.settings import settings
from bot.utils.i18n_start import t, set_lang
from bot.utils.timezones import get_timezone
from fastings.calculations import calculate_fasting_days


async def get_user_fasting(user: User, context: ContextTypes.DEFAULT_TYPE):
    last_message = await context.bot.send_message(
        user.tg_id,
        emo.get(emo.time) + ' ' + t('phrases.tithi_wait'),
        parse_mode=ParseMode.HTML
    )

    username = await get_user_name(user, context)
    logger.info(
        f"📡 Пользователь #{username} " +
        f"⌛️ запросил расчет {user.last_demand}")

    try:
        tz = get_timezone(float(user.lat), float(user.long))
    except Exception as e:
        await last_message.edit_text(t('phrases.location_error'), parse_mode=ParseMode.HTML)
        raise e

    f = calculate_fasting_days(tz.place)
    fasting_message = ""
    for _, fasting in f.iterrows():
        is_ekadashi = fasting['tithi'] == 'ekadashi'
        if user.days == 1 and not is_ekadashi:
            continue
        this_row = '\n'
        this_row += t('words.' + fasting['tithi'], count=1)
        this_row += ":\n⌚ {:%-d %B, %H:%M} – ⌚ {:%-d %B, %H:%M}".format(
            fasting['starts'],
            fasting['ends'])

        fasting_message += '<b>' + this_row + '</b>' if is_ekadashi else this_row

    tz = get_timezone(float(user.lat), float(user.long))
    msg = t('phrases.tithi_answer',
            place=tz.place,
            utc='%+d' % int(tz.utc.seconds/60/60),
            ) + '\n'
    msg += fasting_message
    await last_message.edit_text(msg, parse_mode=ParseMode.HTML)


async def demand_fasting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    if not user:
        await update.message.reply_text(t('phrases.meet_first'), parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    set_lang(user.lang_code)

    last_demand = datetime.datetime.utcnow() - user.last_demand
    if last_demand.seconds < 30 and user.tg_id != settings.developer:
        logger.trace(f"Последний запрос (минуты): {last_demand.seconds // 60}")
        await update.message.reply_text(t('phrases.to_early') + emo.get(emo.namo), parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    user.last_demand = datetime.datetime.utcnow()
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise Exception(f"Ошибка изменения базе. Сообщение: {e.__str__()}")
    await get_user_fasting(user, context)
    return ConversationHandler.END
