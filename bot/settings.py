from dotenv import load_dotenv
from pydantic import BaseSettings


class Settings(BaseSettings):
    token: str
    weather_token: str
    location_pic: str = str('./data/location.png')
    database_url: str = 'postgresql://postgres:@localhost/botsociety'
    developer: int = 1240012
    # Interval for sending messages ( seconds )
    interval: int = 60 * 30


load_dotenv()

settings = Settings(
    _env_file='../.env',
    _env_file_encoding='utf-8'
)
