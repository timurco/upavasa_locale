from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from bot.utils.i18n_start import t
from bot.utils.phrases import all_days_string

LOCATION, DAYS, EKADASHI, ALLDAYS, ZERODAYS, \
CANCEL, DONE, SET_LOCATION, SET_DAYS, YES, NO, LOC_CONFIRMATION = range(12)


def get_confirm_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text=t('words.yes_answer'), callback_data=str(YES)),
            InlineKeyboardButton(text=t('words.no_answer'), callback_data=str(NO)),
        ],
        [
            InlineKeyboardButton(text=t('words.cancel'), callback_data=str(CANCEL)),
        ]
    ])


def get_days_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text=t('words.only_ekadashi',
                                        ekadashi=t('words.ekadashi', count=2)), callback_data=str(EKADASHI)),
            InlineKeyboardButton(text=all_days_string(), callback_data=str(ALLDAYS)),
        ], [
            InlineKeyboardButton(text=t('words.zero_days'), callback_data=str(ZERODAYS)),
            InlineKeyboardButton(text=t('words.cancel'), callback_data=str(CANCEL)),
        ],
    ])
