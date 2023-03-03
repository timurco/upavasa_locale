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


async def fasting_notification(user: User, context: ContextTypes.DEFAULT_TYPE, tz: Timezone, until: int = 2,
                               safe=True) -> bool:
    f = calculate_fasting_days(tz.place)
    first = f.iloc[0]

    if user.days == 1 and not first['tithi'] == 'ekadashi':
        logger.debug('Не экадаши')
        if safe: return False

    fast_day = first['starts']
    if fast_day.hour > 18:
        fast_day += timedelta(days=1)

    # tz.time += timedelta(days=1)
    time_zero = tz.time.replace(hour=0, minute=0, second=0, microsecond=0)
    fast_day_zero = fast_day.replace(tzinfo=None).replace(hour=0, minute=0, second=0, microsecond=0)
    until_event = fast_day_zero - time_zero

    logger.debug('День голодания: {:%-d %B, %H:%M}'.format(fast_day))
    logger.debug('День голодания (обнуленный): {:%-d %B, %H:%M}'.format(fast_day_zero))
    logger.debug('Время: {:%-d %B, %H:%M}'.format(tz.time))
    logger.debug('Время (обнуленный): {:%-d %B, %H:%M}'.format(time_zero))
    logger.debug(f'До события: {until_event}')

    if until_event.days > until:
        logger.debug(f"❎🗓 Мероприятие начнётся только {naturaltime(-until_event)}")
        if safe: return False

    message = namaskar() + '\n'
    message += t('words.regarding', place=tz.place) + ', '
    message += gethumanday(fast_day.replace(tzinfo=None), tz)
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
        f"⌛️ Последнее {user.last_touch}, {naturaltime((datetime.utcnow() - user.last_touch))}")
    await context.bot.send_message(user.tg_id, message, parse_mode=ParseMode.HTML)
    user.last_touch = datetime.utcnow()
    # if not safe:
    #     # Если админский запрос, то не сохраняем в базу дату оповещения
    #     return True
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise Exception(f"Ошибка изменения в базе. Сообщение:{e.__str__()}")
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
            logger.debug(
                "Еще не время оповещать. " +
                f"Пользователь: #{username}. " +
                f"Последнее оповещение: {user.last_touch}, прошло всего {naturaltime(-last_touch)}")
            continue

        set_lang(user.lang_code)

        tz = get_timezone(float(user.lat), float(user.long))
        logger.debug("Пользователь: %s, Локация: %s, Время: %s" % (username, tz.place, tz.time))
        if (tz.time.hour < 7 or tz.time.hour > 22) and user_safe:
            logger.debug("🤫 Тихий час!")
            continue

        await fasting_notification(user, context, tz, settings.notification_days, safe)
    return False
