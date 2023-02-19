import asyncio
import json
from typing import List, Optional

import requests

from bot.services.logger import logger
from bot.settings import settings


async def get_city(query: str) -> Optional[List[float]]:
    url = 'https://api.openweathermap.org/geo/1.0/direct?q=%s&appid=%s' % (query, settings.weather_token)
    try:
        loop = asyncio.get_event_loop()
        req = loop.run_in_executor(None, requests.get, url)
        city_request = await req
        parsed_data = json.loads(city_request.text)
        return [parsed_data[0]['lat'], parsed_data[0]['lon']]
    except Exception as err:
        logger.error("❌ Ошибка при определении города: {}".format(err))
        return None
