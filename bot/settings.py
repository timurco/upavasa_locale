from dotenv import load_dotenv
from pydantic import BaseSettings


class Settings(BaseSettings):
    token: str
    weather_token: str
    location_pic: str = str('./data/location.jpg')
    database_url: str = 'postgresql://postgres:@localhost/botsociety'
    developer: int = 1240012
    # Interval for sending messages ( seconds )
    interval: int = 60 * 30

    # Шаг расчета для Титхи в минутах для оповещений в секундах
    # например: 3 * 60 * 60 - 3 часа
    roug_calc_step: int = 3 * 60 * 60
    exact_calc_step: int = 120
    # За сколько дней начать оповещения
    # 1: за 1 день
    # 2: за 2 дня и т.д.
    notification_days: int = 1
    # Период уведомлений в секундах
    period_seconds: int = 24 * 60 * 60


load_dotenv()

settings = Settings(
    _env_file='../.env',
    _env_file_encoding='utf-8'
)
