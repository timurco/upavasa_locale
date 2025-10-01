from datetime import datetime, timedelta, date
from typing import Tuple

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


def get_awake_period(dt: datetime) -> Tuple[datetime, datetime]:
    """
    Returns the awake period for a given datetime.
    """
    day_start = dt.replace(hour=5, minute=0, second=0, microsecond=0)
    day_end = dt.replace(hour=22, minute=0, second=0, microsecond=0)
    return day_start, day_end


def calculate_recommended_fasting_day(tithis: pd.DataFrame) -> pd.Series:
    """
    Calculates the recommended fasting day based on which day has the most tithi time
    during awake hours (get_awake_period).

    Args:
        tithis: DataFrame with tithi data (from calculate_fasting_days)

    Returns:
        pd.Series: The tithi row with recommended fasting day
    """
    if tithis.empty:
        return None

    # For each tithi, calculate how much time it spends in awake hours on each day
    best_tithi = None
    max_awake_time = timedelta(0)

    for idx, tithi in tithis.iterrows():
        start_time = tithi['starts']
        end_time = tithi['ends']

        # Get all days this tithi spans
        current_day = start_time.date()
        days_data = []

        while current_day <= end_time.date():
            day_start, day_end = get_awake_period(datetime.combine(current_day, datetime.min.time()).replace(tzinfo=start_time.tzinfo))

            # Calculate intersection of tithi with awake period on this day
            tithi_day_start = max(start_time, day_start)
            tithi_day_end = min(end_time, day_end)

            if tithi_day_start < tithi_day_end:
                awake_duration = tithi_day_end - tithi_day_start
                days_data.append((current_day, awake_duration))

            current_day += timedelta(days=1)

        # Find the day with maximum awake time for this tithi
        if days_data:
            day_with_max_time, max_time = max(days_data, key=lambda x: x[1])

            if max_time > max_awake_time:
                max_awake_time = max_time
                best_tithi = tithi.copy()
                # Set the recommended fasting day
                best_tithi['recommended_day'] = datetime.combine(day_with_max_time, datetime.min.time()).replace(tzinfo=start_time.tzinfo)
                best_tithi['awake_duration'] = max_time

    return best_tithi


def calculate_most_fasting_days(tz: str, period: int = 30, starts=datetime.utcnow()) -> pd.DataFrame:
    """
    Calculates fasting days with recommended day based on awake period logic.

    Returns DataFrame with additional columns:
    - recommended_day: datetime of recommended fasting day
    - awake_duration: timedelta of tithi time in awake hours
    """
    tithis = calculate_fasting_days(tz, period, starts)

    if not tithis.empty:
        # Calculate recommendation for each tithi individually
        recommendations = []
        for i in range(len(tithis)):
            single_tithi_df = tithis.iloc[[i]]
            recommended = calculate_recommended_fasting_day(single_tithi_df)
            if recommended is not None:
                recommendations.append({
                    'recommended_day': recommended['recommended_day'],
                    'awake_duration': recommended['awake_duration']
                })
            else:
                tithi = tithis.iloc[i]
                recommendations.append({
                    'recommended_day': tithi['starts'].replace(hour=0, minute=0, second=0, microsecond=0),
                    'awake_duration': timedelta(0)
                })

        # Add recommendations to DataFrame
        rec_df = pd.DataFrame(recommendations)
        tithis = pd.concat([tithis.reset_index(drop=True), rec_df], axis=1)

    return tithis
