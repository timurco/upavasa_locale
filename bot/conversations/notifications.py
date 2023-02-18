from datetime import timedelta, datetime

import pytz
from humanize import naturaltime
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot import User, db, logger, tf
from bot.settings import settings
from bot.utils.humanization import gethumanday
from bot.utils.phrases import *
from bot.utils.timezones import get_timezone, Timezone
from fastings import calculate_fastings
from bot.utils.i18n_start import t, set_lang


async def fasting_notification(user: User, context: ContextTypes.DEFAULT_TYPE, tz: Timezone):
    # Очень грубый расчет
    f = calculate_fastings(lat=user.lat, long=user.long, num=2, step=60 * 60)
    logger.info("ℹ️ Ближайшее {}: 🗓 {:%A, %-d %B}".format(t('words.' + f[0]['name'], count=1), f[0]['start']))

    if user.days == 1 and not f[0]['name'] == 'ekadashi':
        logger.info('Не экадаши')
        return

    fast_day = f[0]['start']
    if fast_day.hour > 18:
        fast_day += timedelta(days=1)

    until_event = fast_day - datetime.now()
    if until_event.days > 2:
        logger.info(f"❎🗓 Мероприятие начнётся только {naturaltime(-until_event)}")
        return

    # Делаем более точный перерасчёт
    f = calculate_fastings(lat=user.lat, long=user.long, num=2, step=30, tz_offset=tz.utc)

    message = namaskar() + '\n'
    message += t('words.regarding', place=tz.place) + ',\n'
    message += gethumanday(fast_day, tz.utc)
    message += fast_day.strftime(' <b>(🗓 %-d %B)</b> ') + t('words.starts') + ' '

    if f[0]['name'] == 'ekadashi':
        message += t('phrases.ekadashi_full')
    else:
        if f[0]['name'] == 'purnima':
            message += t('phrases.purnima_full')
        else:
            message += t('phrases.amavasya_full')

    message += expl() + '\n----\n'

    message += t('phrases.tithi_description') + "\n"
    message += "<b>⌚ {:%-d %B, %H:%M} – ⌚ {:%-d %B, %H:%M}</b>".format(f[0]['start'], f[0]['end'])

    message += '\n----\n'

    message += t('phrases.to_danate')
    message += '\n'
    message += t('phrases.can_stop')

    await context.bot.send_message(user.tg_id, message, parse_mode=ParseMode.HTML)
    user.last_touch = datetime.utcnow()
    db.commit()


async def every_time(context: ContextTypes.DEFAULT_TYPE, safe=True):
    users = db.query(User).all()
    for user in users:
        # Если пользователь отказался от уведомлений
        if not user.active or user.days == 0:
            continue

        user_safe = safe
        if not safe and user.tg_id != settings.developer:
            logger.info(
                'Пользователь %d не девелопер' % user.tg_id
            )
            user_safe = True

        # Если прошло меньше N дней от последнего уведомления
        last_touch = datetime.utcnow() - user.last_touch
        if last_touch.days < 1 and user_safe:
            logger.info(
                "Еще не время оповещать. " +
                f"Пользователь: #{user.id}. " +
                f"Последнее оповещение: {user.last_touch}, прошло всего {naturaltime(-last_touch)}")
            continue

        set_lang(user.lang_code)

        try:
            tz = get_timezone(user)
            logger.info("Пользователь: %d, Локация: %s, Время: %s" % (user.tg_id, tz.place, tz.time))
            if (tz.time.hour < 7 or tz.time.hour > 22) and user_safe:
                logger.info("🤫 Тихий час!")
                return

            await fasting_notification(user, context, tz)
        except Exception as e:
            logger.warning("Невозможно определить временную зону у пользователя %s" % user.tg_id)
            await context.bot.send_message(user.tg_id, t('phrases.location_error'), parse_mode=ParseMode.HTML)
            user.last_touch = datetime.utcnow()
            raise Exception(str(e) + '\n' + user.__repr__())
