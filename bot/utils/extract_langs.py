import lxml.etree
import urllib.request
import iso639
import json


def get_territory_languages():
    url = "https://raw.githubusercontent.com/unicode-org/cldr/master/common/supplemental/supplementalData.xml"
    langxml = urllib.request.urlopen(url)
    langtree = lxml.etree.XML(langxml.read())

    territory_languages = {}
    for t in langtree.find('territoryInfo').findall('territory'):
        langs = {}
        for l in t.findall('languagePopulation'):
            langs[l.get('type')] = {
                'percent': float(l.get('populationPercent')),
                'official': bool(l.get('officialStatus'))
            }
        territory_languages[t.get('type')] = langs
    return territory_languages


TERRITORY_LANGUAGES = get_territory_languages()


def get_official_locale_ids(country_code):
    country_code = country_code.upper()
    langs = TERRITORY_LANGUAGES[country_code].items()
    # most widely-spoken first:
    # langs.sort(key=lambda l: l[1]['percent'], reverse=True)
    return [
        '{lang}_{terr}'.format(lang=lang, terr=country_code)
        for lang, spec in langs if spec['official']
    ]


def get_locale(lang_code):
    countries = {}
    for key in TERRITORY_LANGUAGES.keys():
        for lang in TERRITORY_LANGUAGES[key].keys():
            if lang_code.upper() == lang.upper():
                countries[key] = TERRITORY_LANGUAGES[key][lang]['percent']
                break
    try:
        max_value = max(countries, key=countries.get)
        return '{lang}_{terr}'.format(lang=lang_code, terr=max_value)
    except:
        return None


languages = {}
for lang in iso639.iter_langs():
    if lang.pt1:
        locale = get_locale(lang.pt1)
        if locale:
            languages[lang.pt1] = locale

print(languages)
with open('langs.json', 'w') as fp:
    json.dump(languages, fp)
