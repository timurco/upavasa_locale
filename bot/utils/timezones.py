from datetime import datetime, timedelta

import pytz
from pydantic import BaseModel

from bot import tf


class Timezone(BaseModel):
    place: str
    time: datetime
    utc: timedelta


def get_timezone(lat: float, long: float) -> Timezone:
    timezone_str = tf.certain_timezone_at(lat=lat, lng=long)
    timezone = pytz.timezone(timezone_str)
    dt = datetime.utcnow()
    current_time = dt + timezone.utcoffset(dt)
    return Timezone(
        place=timezone_str,
        time=current_time,
        utc=timezone.utcoffset(dt)
    )
