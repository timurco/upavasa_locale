from datetime import timedelta, datetime

from humanize import naturaltime
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot import User, db, logger
from bot.conversations import get_user_name
from bot.settings import settings
from bot.utils.humanization import gethumanday
from bot.utils.i18n_start import set_lang
from bot.utils.phrases import *
from bot.utils.timezones import get_timezone, Timezone
from fastings.calculations import calculate_fasting_days


async def fasting_notification(user: User, context: ContextTypes.DEFAULT_TYPE, tz: Timezone, until: int = 2) -> bool:
    f = calculate_fasting_days(tz.place)
    first = f.iloc[0]

    if user.days == 1 and not first['tithi'] == 'ekadashi':
        logger.debug('Не экадаши')
        return False

    fast_day = first['starts']
    if fast_day.hour > 18:
        fast_day += timedelta(days=1)

    until_event = fast_day.replace(tzinfo=None) - tz.time
    if until_event.days > until:
        logger.debug(f"❎🗓 Мероприятие начнётся только {naturaltime(-until_event)}")
        return False

    message = namaskar() + '\n'
    message += t('words.regarding', place=tz.place) + ',\n'
    message += gethumanday(fast_day.replace(tzinfo=None), tz.utc)
    message += fast_day.strftime(' <b>(🗓 %-d %B)</b> ') + t('words.starts') + ' '

    if first['tithi'] == 'ekadashi':
        message += t('phrases.ekadashi_full')
    else:
        if first['tithi'] == 'purnima':
            message += t('phrases.purnima_full')
        else:
            message += t('phrases.amavasya_full')

    message += expl() + '\n----\n'

    message += t('phrases.tithi_description') + "\n"
    message += "<b>⌚ {:%-d %B, %H:%M} – ⌚ {:%-d %B, %H:%M}</b>".format(first['starts'], first['ends'])

    message += '\n----\n'

    message += t('phrases.to_danate')
    message += '\n'
    message += t('phrases.can_stop')

    username = await get_user_name(user, context)
    logger.info(
        f"🔔 Оповещение пользователя #{username}. " +
        f"⌛️ Последнее {user.last_touch}, прошло {naturaltime(-(datetime.utcnow() - user.last_touch))}")
    await context.bot.send_message(user.tg_id, message, parse_mode=ParseMode.HTML)
    user.last_touch = datetime.utcnow()
    db.commit()
    return True


async def every_time(context: ContextTypes.DEFAULT_TYPE, safe=True) -> bool:
    users = db.query(User).all()
    for user in users:
        # Если пользователь отказался от уведомлений
        if not user.active or user.days == 0:
            continue

        user_safe = safe
        if not safe and user.tg_id != settings.developer:
            user_safe = True

        username = await get_user_name(user, context)

        # Если прошло меньше N дней от последнего уведомления
        last_touch = datetime.utcnow() - user.last_touch
        if last_touch.days < 1 and user_safe:
            logger.info(
                "Еще не время оповещать. " +
                f"Пользователь: #{username}. " +
                f"Последнее оповещение: {user.last_touch}, прошло всего {naturaltime(-last_touch)}")
            continue

        set_lang(user.lang_code)

        tz = get_timezone(float(user.lat), float(user.long))
        logger.debug("Пользователь: %s, Локация: %s, Время: %s" % (username, tz.place, tz.time))
        print(tz.time.hour)
        print(tz.time.hour < 7 or tz.time.hour > 22)
        print(user_safe)
        if (tz.time.hour < 7 or tz.time.hour > 22) and user_safe:
            logger.info("🤫 Тихий час!")
            return False

        return await fasting_notification(user, context, tz, 2 if safe else 10)
