from datetime import datetime, timedelta

import ephem
import pandas as pd
from pytz import timezone, utc

TITHI_NAMES = (
    "amavasya", "pratipada", "dwitiya", "tritiya", "chaturthi",
    "panchami", "shashti", "saptami", "ashtami", "navami", "dashami ",
    "ekadashi", "dwadashi", "trayodashi", "chaturdashi", "purnima",
    "pratipada", "dwitiya", "tritiya", "chaturthi", "panchami",
    "shashti", "saptami", "ashtami", "navami", "dashami", "ekadashi",
    "dwadashi", "trayodashi", "chaturdashi", "amavasya"
)


def get_timezone_time(utc_date: datetime, timezone_str: str) -> datetime:
    zon = timezone(timezone_str)
    s_utc = utc.localize(utc_date)
    s_loc = s_utc.astimezone(zon)
    return s_loc


def get_utc_tithi(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    sd, ed = ephem.Date(start_date), ephem.Date(end_date)
    first_amavasya = ephem.previous_new_moon(sd)
    raw_tithis = []
    last_amavasya = ephem.next_new_moon(ed).datetime().replace(second=0, microsecond=0)

    while first_amavasya < ed:
        l1 = [ephem._find_moon_phase(first_amavasya, ephem.twopi, ephem.pi * i / 15) for i in range(30)]
        days = [[1, first_amavasya.datetime()]] + [[i + 1, l1[i].datetime()] for i in range(1, 30)]
        raw_tithis += days
        first_amavasya = l1[0]

    tithis = []
    for i, v in enumerate(raw_tithis):
        tithis += [[
            TITHI_NAMES[v[0]],
            # start date
            v[1].replace(second=0, microsecond=0),
            # end of tithi date
            raw_tithis[i + 1][1].replace(second=0, microsecond=0)
            if i < len(raw_tithis) - 1 else last_amavasya
        ]]

    return pd.DataFrame(tithis, columns=['tithi', 'starts', 'ends'])


def calculate_fasting_days(tz: str, period: int = 30, starts=datetime.utcnow()) -> pd.DataFrame:
    """
        Расчитывает дни Экадаши, Амавасьи и Пурнимы исходя из Временной зоны
        **Более быстрый вариант расчета.**

        *Все вычисления производятся в UTC!!!*

        Источник: https://github.com/Fallcon777/panchang/blob/master/panchang.py

        Args:
            tz (:obj:`str`): Строка временной зоны
            period (:obj:`int`): На сколько дней будет расчёт
            starts (:obj:`datetime`): Начало расчета

    """
    starts_offset = starts - timedelta(days=1)
    ends = starts_offset + timedelta(days=period)
    print(starts_offset)
    tithis = get_utc_tithi(starts_offset, ends)
    # filter only from Start to End
    tithis = tithis[~(tithis['starts'] < starts) & ~(tithis['starts'] > ends)]
    # filter only Fasting Days
    tithis = tithis[tithis['tithi'].isin(['ekadashi', 'amavasya', 'purnima'])]

    # Convert to given Timezone
    zon = timezone(tz)
    tithis['starts'] = tithis['starts'].apply(lambda dt: utc.localize(dt).astimezone(zon))
    tithis['ends'] = tithis['ends'].apply(lambda dt: utc.localize(dt).astimezone(zon))
    return tithis
