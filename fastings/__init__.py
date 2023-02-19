# Дата и время
import math
import sys
import traceback
from datetime import datetime, timedelta

import ephem.cities

from bot.services.logger import logger
from fastings.tithi import *


def offset():
    d1 = datetime.now().replace(second=0, microsecond=0)
    d2 = datetime.utcnow().replace(second=0, microsecond=0)
    r = d1 - d2
    return r


def calculate_fastings(lat: float, long: float, num=2, period=30, step=30, tz_offset: timedelta = offset()):
    """Расчитывает дни Экадаши, Амавасьи и Пурнимы исходя из Широты и Долготы

        Args:
            lat (:obj:`float`): Широта
            long (:obj:`float`): Долгота
            num (:obj:`int`): Количество: титей, которые нужны
            period (:obj:`int`): Дни - период на который нужно сделать расчёт
            step (:obj:`int`): Секунды - шаг расчета: чем меньше – тем дольше, но точнее
            tz_offset (:obj:`timedelta`): Смещение для временной зоны

        """
    utc_datetime = datetime.utcnow() - timedelta(days=1)
    start_time = datetime.now()  # Для расчета времени работы скрипта

    UTC_str = 'UTC%+d' % int(tz_offset.seconds / 60 / 60)
    logger.debug(f"🕘 Начинаю расчёт голоданий для {lat}, {long} и {UTC_str}")
    # Observer
    obs = ephem.Observer()
    obs.lat, obs.lon = str(lat), str(long)
    obs.date = utc_datetime
    sun, moon = ephem.Sun(), ephem.Moon()


    # sun.compute()
    # moon.compute()
    # print("Sunrise:", ephem.Date(obs.next_rising(sun)).datetime() + tz_offset)
    # print('Time:', obs.date.datetime() + tz_offset)
    def dates_generator(start_date, end_date=None, delta=None):
        if delta is None:
            delta = timedelta(seconds=30)
        if end_date is None:
            end_date = start_date + timedelta(days=1)
            end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        value = start_date

        while value < end_date:
            yield value
            value += delta
        return

    # Calculation
    dates = dates_generator(utc_datetime, end_date=utc_datetime + timedelta(days=period), delta=timedelta(seconds=step))

    def compute_tithi(calc_date):
        # calc_date += tz_offset
        obs.date = calc_date
        sun.compute(calc_date)
        moon.compute(calc_date)
        # if math.floor((math.degrees(diff)%12)*100)/100 == 6:
        #     print(ephem.localtime(obs.date), math.degrees(diff))
        # print(ephem.localtime(obs.date), calc_date, obs.date.datetime(), math.degrees(moon.ra))
        return calculate_tithi(moon.ra, sun.ra)

    i = 0
    tithies = []
    (prev_tithi, _) = compute_tithi(utc_datetime)
    for each_date in dates:
        (tithi, diff) = compute_tithi(each_date)
        # Если в списке содержится текущий или предыдущий титхи
        if tithi != prev_tithi:
            # 0 - Амавасья, 11 - Экадаши, 15 - Пурнима, 26 - Экадаши
            if tithi in [0, 11, 15, 26]:
                tithies.append([(tithi, each_date + tz_offset, 0)])
                i += 1
            if prev_tithi in [0, 11, 15, 26]:
                if i == 0:
                    prev_tithi = tithi
                    continue
                tithies[len(tithies) - 1].append(
                    (prev_tithi, each_date + tz_offset, 1)
                )
                i += 1
            if i >= num * 2 and len(tithies[-1]) == 2:
                break
        prev_tithi = tithi

    if len(tithies[-1]) != 2:
        tithies = tithies[:-1]

    logger.info(
        f'🕘 Длительность расчёта: {datetime.now() - start_time} для {UTC_str}. ' +
        f'Получено элементов: {i}/{len(tithies)}')
    result = []
    try:
        result = [{'name': TITHI_INFO[x[0][0]][0].lower(), 'start': x[0][1], 'end': x[1][1]} for x in tithies]
    except Exception as err:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        err_msg = "❌ Ошибка при расчёте Титхи!\n%s: %s\n%s" % (exc_type, err, traceback.format_exc())
        logger.error(err_msg, "Текущие данные:", *tithies, sep='\n')

    return result
