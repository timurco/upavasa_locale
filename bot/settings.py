from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseSettings
from random import choice


class Settings(BaseSettings):
    token: str
    weather_token: str
    location_pic: str = str('./data/location.png')
    database_url: str = 'postgresql://postgres:@localhost/botsociety'
    developer: int = 1240012
    # Interval for sending messages ( seconds )
    interval: int = 60 * 30
    strings: dict = {
        'ru': {
            'ok': choice(['Принято!', 'Ясно!', 'Понял!', 'Готово!', 'Отлично!', 'Супер!', 'Класс!', 'Кайф!']),
            'cancel': 'Отмена',
            'zero_days': 'Не надо ничего слать',
            'only_ekadashi': 'Только Экадаши',
            'all_days': 'Экадаши, Пурнимы и Амавасьи',
            'hello': 'Намаскар, %s! 🙏',
            'my_name': 'Меня зовут <b>Упаваса Бот</b>.',
            'mission': 'Я здесь для того, чтобы рассчитывать дни голодания (<i>Экадаши, Амавасьи, Пурнимы</i>) ' +
                       'согласно твоему месту проживания.',
            'start_choose_location': 'Пожалуйста, нажми на скрепку (где обычно прикрепляют файлы) и выбери <b>Location</b> или <b>Местоположение</b>',
            'start_choose_day': 'Давай выберем день, когда ты хочешь получать уведомления о голоданиях.',
            'location_update': "Ты сможешь обновить свою локацию в любой момент, через команду /update_location",
            'set_location': "Твоя локация обновлена!",
            'location_first': 'Для начала добавь локацию через команду /start',
            'days_update': "Ты сможешь обновить дни в которые голодаешь в любой момент, через команду /update_days",
            'ekadashi_format': '<b>Экадаши</b>',
            'all_days_format': '<b>Экадаши</b>, <b>Пурнимы</b> и <b>Амавасьи</b>',
            'ready_to_send': 'За день до %s, я буду присылать тебе напоминания о них.',
            'ready_stop': 'Если захочешь отписаться от уведомлений, введи команду /stop',
            'no_answer': 'Без вариантов ответа я, к сожалению, не смогу рассчитывать дни голоданий 😢',
            'again': 'Нажми на /start если снова захочешь запустить эти процессы',
            'no_user': 'Тебя нету у меня в списке. Так что тут нечего останавливать. Но если захочешь, можно начать уведомления через /start',
            'meet_first': 'Для начала, мне нужны твое местоположения и какие дни для голодания тебе нужны.\nНажми на /start чтобы начать.',
            'to_early': 'Пожалуйста, не нагружай меня так часто с расчетами. ' +
                        'Эти цифры, синусы, косинусы... От этого уже начинает болеть голова. ' +
                        'Подожди хотя бы несколько минут! 🙏',
            'location_error': 'Что-то не так с координатами. Не могу считать.\nПопробуй обновить свою локацию /update_location',
            'tithi_wait': '🕐 Секунду, сейчас взгляну на небо. Нужно провести расчёты... X*y*sin*cos*tan*E*pi/2...',
            'tithi_answer': '<u>Ближайшие благоприятные дни для голоданий:</u>',
            'tithi': {'amavasya': 'Амавасья', 'purnima': 'Пурнима', 'ekadashi': 'Экадаши'},
        }
    }


load_dotenv()

settings = Settings(
    _env_file='../.env',
    _env_file_encoding='utf-8'
)
