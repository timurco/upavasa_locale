"""
Тесты для расчета дней голодания в разных городах.
Показывает реальные примеры титхи и расчет рекомендуемых дней голодания
на основе периода бодрствования (5:00 - 22:00).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from datetime import datetime, timedelta
from typing import List, Tuple, Dict

from fastings.calculations import (
    calculate_most_fasting_days,
    calculate_fasting_days,
    get_awake_period,
    calculate_recommended_fasting_day
)
from bot.utils.timezones import get_timezone


class TestFastingDays(unittest.TestCase):
    """Тесты для расчета дней голодания в разных городах."""

    def setUp(self):
        """Настройка тестовых данных."""
        # Координаты городов
        self.cities = {
            'Moscow': {'lat': 55.7558, 'lon': 37.6176, 'name': 'Москва'},
            'Barnaul': {'lat': 53.3606, 'lon': 83.7636, 'name': 'Барнаул'},
            'Tbilisi': {'lat': 41.7167, 'lon': 44.7833, 'name': 'Тбилиси'}
        }

    def get_city_timezone(self, city_key: str) -> str:
        """Получить timezone для города по его координатам."""
        city_data = self.cities[city_key]
        tz_info = get_timezone(city_data['lat'], city_data['lon'])
        return tz_info.place

    def calculate_duration_intervals(self, start_time: datetime, end_time: datetime, tz_str: str) -> List[Dict]:
        """Рассчитать продолжительность титхи в каждый день с точными временными интервалами."""
        current_day = start_time.date()
        day_durations = []

        while current_day <= end_time.date():
            day_start, day_end = get_awake_period(
                datetime.combine(current_day, datetime.min.time()).replace(tzinfo=start_time.tzinfo)
            )

            tithi_day_start = max(start_time, day_start)
            tithi_day_end = min(end_time, day_end)

            if tithi_day_start < tithi_day_end:
                duration = tithi_day_end - tithi_day_start
                hours, remainder = divmod(duration.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                duration_str = f"{hours:02d}:{minutes:02d}"

                # Определяем реальные временные интервалы
                actual_start = max(start_time, day_start)
                actual_end = min(end_time, day_end)

                interval_str = f"({actual_start.strftime('%H:%M')} - {actual_end.strftime('%H:%M')})"

                day_durations.append({
                    'day': current_day,
                    'duration': duration,
                    'duration_str': duration_str,
                    'interval': interval_str,
                    'day_num': len(day_durations) + 1
                })
            else:
                day_durations.append({
                    'day': current_day,
                    'duration': timedelta(0),
                    'duration_str': "00:00",
                    'interval': "(00:00 - 00:00)",
                    'day_num': len(day_durations) + 1
                })

            current_day += timedelta(days=1)

        return day_durations

    def test_upcoming_fasting_days_formatted(self):
        """Тест показа ближайших дней голодания в красивом формате для разных городов."""
        print("\n🗓 Upcoming Fasting Days Test (next 10 days)")
        print("=" * 60)

        for city_key, city_data in self.cities.items():
            tz_str = self.get_city_timezone(city_key)
            tithis_df = calculate_most_fasting_days(tz_str, period=30)

            if not tithis_df.empty:
                print(f"\n🏙 {city_data['name']} (lat: {city_data['lat']}, lon: {city_data['lon']})")
                print("-" * 40)
                print(f"   Timezone: {tz_str}")

                for idx, tithi in tithis_df.iterrows():
                    if idx >= 2:  # Показываем только первые 2 примера для каждого города
                        break

                    start_time = tithi['starts']
                    end_time = tithi['ends']
                    recommended_day = tithi['recommended_day']

                    # Используем новую функцию для расчета интервалов
                    day_durations = self.calculate_duration_intervals(start_time, end_time, tz_str)

                    # Определяем эмодзи для типа титхи
                    tithi_emoji = {
                        'ekadashi': '🌙',
                        'purnima': '🌕',
                        'amavasya': '🌑'
                    }.get(tithi['tithi'], '🌙')

                    print(f"\n{tithi_emoji} {tithi['tithi'].capitalize()}: {recommended_day.strftime('%Y-%m-%d')}")
                    print(f"   └─ Tithi: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}")

                    # Показываем продолжительность по дням с точными интервалами
                    for duration_info in day_durations:
                        day_num = "first" if duration_info['day_num'] == 1 else "second" if duration_info['day_num'] == 2 else f"day {duration_info['day_num']}"
                        print(f"   └─ Duration in {day_num} day: {duration_info['duration_str']} {duration_info['interval']}")

                    # Сравнение и рекомендация
                    if len(day_durations) >= 2:
                        first_duration = day_durations[0]['duration_str']
                        second_duration = day_durations[1]['duration_str']
                        first_time = day_durations[0]['duration']
                        second_time = day_durations[1]['duration']
                        comparison = f"{first_duration} > {second_duration}" if first_time > second_time else f"{first_duration} < {second_duration}"
                        print(f"   └─ {comparison}, Recommended day is: {recommended_day.strftime('%Y-%m-%d')}")

                    print()

    def test_calculations_work(self):
        """Простой тест, проверяющий что все функции работают."""
        # Проверяем расчет периода бодрствования
        test_date = datetime(2024, 10, 1, 12, 0, 0)
        awake_start, awake_end = get_awake_period(test_date)
        self.assertEqual(awake_start.hour, 5)
        self.assertEqual(awake_end.hour, 22)

        # Проверяем получение титхи для Москвы
        moscow_tz = self.get_city_timezone('Moscow')
        tithis_df = calculate_most_fasting_days(moscow_tz, period=30)
        self.assertGreater(len(tithis_df), 0)

        # Проверяем, что у каждого титхи есть рекомендуемый день
        first_tithi = tithis_df.iloc[0]
        self.assertIn('recommended_day', first_tithi)
        self.assertIn('awake_duration', first_tithi)


if __name__ == '__main__':
    unittest.main()
