import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from bot import User, emo, logger, db
from bot.settings import settings
from bot.utils.i18n_start import t, set_lang
from bot.utils.timezones import get_timezone
from fastings import calculate_fastings


async def get_user_fasting(user: User, context: ContextTypes.DEFAULT_TYPE):
    last_message = await context.bot.send_message(
        user.tg_id,
        emo.get(emo.time) + ' ' + t('phrases.tithi_wait'),
        parse_mode=ParseMode.HTML
    )

    f = calculate_fastings(lat=float(user.lat), long=float(user.long), num=4)
    fasting_message = ""
    for fasting in f:
        is_ekadashi = fasting['name'] == 'ekadashi'
        if user.days == 1 and is_ekadashi:
            continue
        this_row = '\n<u>' + t('words.' + fasting['name'], count=1)
        this_row += "</u>:\n⌚ {:%-d %B, %H:%M} – ⌚ {:%-d %B, %H:%M}".format(
            fasting['start'],
            fasting['end'])

        fasting_message += '<b>' + this_row + '</b>' if is_ekadashi else this_row

    tz = get_timezone(user)
    msg = t('phrases.tithi_answer',
            place=tz.place,
            utc='%+d' % int(tz.utc.seconds/60/60),
            )
    msg += fasting_message
    await last_message.edit_text(msg, parse_mode=ParseMode.HTML)


async def demand_fasting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    set_lang(update.effective_user.language_code)

    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    if not user:
        await update.message.reply_text(t('phrases.meet_first'), parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    last_demand = datetime.datetime.utcnow() - user.last_demand
    if last_demand.seconds // 60 < 10 and user.tg_id != settings.developer:
        logger.info(f"Последний запрос (минуты): {last_demand.seconds // 60}")
        await update.message.reply_text(t('phrases.to_early') + emo.get(emo.namo), parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    user.last_demand = datetime.datetime.utcnow()
    db.commit()
    await get_user_fasting(user, context)
    return ConversationHandler.END
