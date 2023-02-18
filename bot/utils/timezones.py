from datetime import datetime, timedelta

import pytz
from pydantic import BaseModel

from bot import User, tf


class Timezone(BaseModel):
    place: str
    time: datetime
    utc: timedelta


def get_timezone(user: User) -> Timezone:
    timezone_str = tf.certain_timezone_at(lat=float(user.lat), lng=float(user.long))
    timezone = pytz.timezone(timezone_str)
    dt = datetime.utcnow()
    current_time = dt + timezone.utcoffset(dt)
    return Timezone(
        place=timezone_str,
        time=current_time,
        utc=timezone.utcoffset(dt)
    )