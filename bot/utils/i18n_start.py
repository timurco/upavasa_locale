import locale

import humanize
from i18n import translations, config
from i18n.translator import pluralize, TranslationFormatter
import i18n

i18n.set('fallback', 'ru')
i18n.load_path.append('locale')

# Telegram languages code
# refs:
# - https://gist.github.com/jacobbubu/1836273
# - https://stackoverflow.com/questions/3191664/list-of-all-locales-and-their-short-codes
# Также мы используем humanize, у которого свой список языков:
# - https://pypi.org/project/humanize/

tg_lang_list = {
    'ru': 'ru_RU',  # Russian (Russia)
    'en': 'en_US',  # English (United States)
    # 'be': 'be_BY', # не доступен в humanize
    'ca': 'ca_ES',  # Catalan (Spain)
    'nl': 'nl_NL',  # Dutch (Netherlands)
    'fr': 'fr_FR',  # French (France)
    'de': 'de_DE',  # German (Germany)
    'it': 'it_IT',  # Italian (Italy)
    # 'ms': 'ms_MY', # не доступен в humanize
    'pl': 'pl_PL',  # Polish (Poland)
    'pt': 'pt_PT',  # Portuguese (Portugal)
    'es': 'es_ES',  # Spanish (Spain)
    'tr': 'tr_TR',  # Turkish (Turkey)
    'uk': 'uk_UA',  # Ukrainian (Ukraine)
}


def set_lang(lang: str):
    i18n.set("locale", lang)

    if lang == 'en':
        humanize.i18n.deactivate()
        locale.setlocale(locale.LC_TIME, 'en_US')

    else:
        if lang in tg_lang_list.keys():
            lang_code = tg_lang_list[lang]
            locale.setlocale(locale.LC_TIME, lang_code)
            humanize.i18n.activate(lang)
        else:
            locale.setlocale(locale.LC_TIME, 'en_US')
            humanize.i18n.deactivate()
            raise Exception("Ошибка с локализацией: %s - %s" % (lang, lang))


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
