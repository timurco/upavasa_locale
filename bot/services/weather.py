import json
from typing import List, Optional

import requests

from bot.services.logger import logger
from bot.settings import settings


def get_city(query: str) -> Optional[List[float]]:
    url = 'https://api.openweathermap.org/geo/1.0/direct?q=%s&appid=%s' % (query, settings.weather_token)
    try:
        city_request = requests.get(url)
        parsed_data = json.loads(city_request.text)
        return [parsed_data[0]['lat'], parsed_data[0]['lon']]
    except Exception as err:
        logger.error("❌ Ошибка при определении города: {}".format(err))
        return None
