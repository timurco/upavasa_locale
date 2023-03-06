from datetime import timedelta, datetime
from typing import Optional

from humanize import naturaltime
from telegram.constants import ParseMode
from telegram.error import Forbidden
from telegram.ext import ContextTypes

from bot import User, db, logger, Message
from bot.conversations import get_user_name
from bot.settings import settings
from bot.utils.humanization import gethumanday
from bot.utils.i18n_start import set_lang
from bot.utils.phrases import *
from bot.utils.timezones import get_timezone, Timezone
from fastings.calculations import calculate_fasting_days


async def fasting_notification(
        user: User, context: ContextTypes.DEFAULT_TYPE, tz: Timezone, until: int = 2
) -> Optional[Message]:
    if settings.mode == 'DEV':
        # Кастомное время для отладки
        tz.time += timedelta(seconds=-15 * 3600)

    f = calculate_fasting_days(tz.place)
    first = f.iloc[0]

    if user.days == 1 and not first['tithi'] == 'ekadashi':
        logger.trace('Не экадаши')
        return None

    fast_day = first['starts']
    if fast_day.hour > 18:
        fast_day += timedelta(days=1)

    time_zero = tz.time.replace(hour=0, minute=0, second=0, microsecond=0)
    fast_day_zero = fast_day.replace(tzinfo=None).replace(hour=0, minute=0, second=0, microsecond=0)
    until_event = fast_day_zero - time_zero

    logger.trace('День голодания: {:%-d %B, %H:%M}'.format(fast_day))
    logger.trace('День голодания (обнуленный): {:%-d %B, %H:%M}'.format(fast_day_zero))
    logger.trace('Время: {:%-d %B, %H:%M}'.format(tz.time))
    logger.trace('Время (обнуленный): {:%-d %B, %H:%M}'.format(time_zero))
    logger.trace(f'До события: {until_event}')
    logger.trace(f'{until_event.days} > {until} = {until_event.days > until}')

    if until_event.days < 1:
        logger.trace("❎🗓 Мероприятие уже идет")
        return None

    if until_event.days > until:
        logger.trace(f"❎🗓 Мероприятие начнётся только {naturaltime(-until_event)}")
        return None

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

    result = None
    try:
        answer = await context.bot.send_message(user.tg_id, message, parse_mode=ParseMode.HTML)
        result = Message(type=first['tithi'], user=user, message_id=answer.message_id)
        db.add(result)
    except Forbidden as e:
        logger.error(f'Пользователь заблочил бота, отключаем в базе. Ошибка: {e.__str__()}')
        user.active = False

    if not (settings.mode == 'DEV' and user.tg_id == settings.developer):
        user.last_touch = datetime.utcnow()

    try:
        db.commit()
        if result:
            db.refresh(result)
            return result
    except Exception as e:
        db.rollback()
        raise Exception(f"Ошибка изменения в базе. Сообщение:{e.__str__()}")
    return None


async def every_time(context: ContextTypes.DEFAULT_TYPE):
    users = db.query(User).all()
    messages = []
    for user in users:
        # Если пользователь отказался от уведомлений
        if not user.active or user.days == 0:
            continue

        username = await get_user_name(user, context)

        # Если прошло меньше N дней от последнего уведомления
        last_touch = datetime.utcnow() - user.last_touch
        if last_touch.total_seconds() < settings.period_seconds:
            logger.trace(
                "Еще не время оповещать. " +
                f"Пользователь: #{username}. " +
                f"Последнее оповещение: {user.last_touch}, прошло всего {naturaltime(-last_touch)}")
            continue

        set_lang(user.lang_code)

        tz = get_timezone(float(user.lat), float(user.long))
        logger.trace("Пользователь: %s, Локация: %s, Время: %s" % (username, tz.place, tz.time))
        if tz.time.hour < 7 or tz.time.hour > 22:
            logger.trace("🤫 Тихий час!")
            continue

        result = await fasting_notification(user, context, tz, settings.notification_days)
        if result:
            messages += [result]

    if len(messages):
        set_lang('ru')
        msg = f'Я только что выслал сообщений <u>{len(messages)}</u>, следующим людям:'
        for m in messages:
            msg += f'\n{choice(["🌎", "🥰", "🤗", "❤️", "🥸", "😜", "😇", "🥳", "🤩"])} '
            msg += f'<b>{m.message_id}</b>: '
            msg += await m.user.get_user_html(context)
            msg += f' [<i>{t("phrases." + m.type + "_full")}</i>]'

        await context.bot.send_message(settings.developer, msg, parse_mode=ParseMode.HTML, disable_notification=True)
