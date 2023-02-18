from random import choice

from bot.utils import emo
from bot.utils.i18n_start import t
from bot.utils.shuffler import Shuffler


def luck() -> bool:
    return choice((True, False))


def expl() -> str:
    return "!" if luck else "."


def me() -> str:
    return '🤖 '


def all_days_string() -> str:
    return t('words.all_days',
             ekadashi=t('words.ekadashi', count=2),
             amavasya=t('words.amavasya', count=2),
             purnima=t('words.purnima', count=2))


def namaskar(name: str = None) -> str:
    args = [
        t('words.namaskar'),
        name if name else t('words.friend')
    ]
    return Shuffler(*args).compile(['!!!', '!', '.']) + emo.get(emo.namo, mx=1)


def okay() -> str:
    return t('words._ok') + expl() + ' '
