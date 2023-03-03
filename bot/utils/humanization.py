import locale
from datetime import timedelta, date, datetime
import humanize
from bot.services.logger import logger
from bot.utils.i18n_start import t
from bot.utils.timezones import Timezone


def gethumanday(event_date, tz: Timezone):
    is_date_only = type(event_date) is date
    # Возводим дату в вид с отображением часов, если получили дату без времени
    if is_date_only:
        event_date = datetime.fromordinal(event_date.toordinal())
        event_date = event_date.replace(hour=6, minute=0)

    # seconds=4*60*60 – начинаем считать день с 4:00 утра
    midnight = (tz.time - timedelta(seconds=4 * 60 * 60)).replace(hour=0, minute=0)
    diff_real = event_date - tz.time
    diff = event_date - midnight

    logger.debug('Midnight: {:%-d %B, %H:%M}'.format(midnight))
    logger.debug(f'Разница (реальная): {diff_real}')
    logger.debug(f'Разница (с смещением): {diff}')

    DAY_ALTERNATIVES = {
        0: t("words.today"),
        1: t("words.tomorrow"),
        2: t("words.aftertomorrow"),
    }

    if diff.days in range(1, 3) or diff.days == 0 and diff_real.seconds > 10 * 60 * 60:
        return DAY_ALTERNATIVES[diff.days]

    if locale.getlocale(locale.LC_TIME)[0] and 'en' in locale.getlocale(locale.LC_TIME)[0]:
        return 'at ' + humanize.naturaltime(-diff)
    return humanize.naturaltime(-diff)
