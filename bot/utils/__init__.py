from functools import wraps

from telegram import Update

from bot.models import User
from bot.settings import settings


def user_language(func):
    @wraps(func)
    async def wrapped(update: Update, *args):
        lang = update.effective_user.language_code
        if lang == "ru":
            s = settings.strings['ru']
        else:
            s = settings.strings['ru']
        return await func(s, update, *args)

    return wrapped


def user_language_custom(func):
    @wraps(func)
    async def wrapped(user: User, *args):
        if user.lang_code == "ru":
            s = settings.strings['ru']
        else:
            s = settings.strings['ru']

        return await func(s, user, *args)

    return wrapped
