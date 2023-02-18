import locale

import humanize
from i18n import translations, config
from i18n.translator import pluralize, TranslationFormatter
import i18n

from bot import lang_codes
from bot.services.logger import logger

i18n.set('fallback', 'ru')
i18n.load_path.append('locale')


def set_lang(lang: str):
    i18n.set("locale", lang)
    # print('Locale' + locale.getlocale(locale.LC_ALL))

    if lang == 'en':
        humanize.i18n.deactivate()
        locale.setlocale(locale.LC_TIME, 'en_US')

    else:
        lang_code = lang_codes[lang]
        try:
            locale.setlocale(locale.LC_TIME, lang_code)

            humanize.i18n.activate(lang)
        except:
            logger.error("Ошибка с локализацией: %s - %s" % (lang, lang_code))
            locale.setlocale(locale.LC_TIME, 'en_US')
            humanize.i18n.deactivate()


def translate(key, **kwargs):
    locale = kwargs.pop('locale', config.get('locale'))
    translation = translations.get(key, locale=locale)
    if 'count' in kwargs:
        translation = pluralize(key, translation, kwargs['count'])

    if isinstance(translation, list):
        from random import choice
        return choice([TranslationFormatter(n).format(**kwargs) for n in translation])

    return TranslationFormatter(translation).format(**kwargs)


# replacing translate function
i18n.translator.translate.__code__ = translate.__code__
t = i18n.t
