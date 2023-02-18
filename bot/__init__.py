import json
import timezonefinder
from bot.models import User
from bot.services.database import db
from bot.services.logger import logger
from bot.utils import emo


tf = timezonefinder.TimezoneFinder()

with open('bot/utils/langs.json', 'r') as fp:
    lang_codes = json.load(fp)

# @user_language_custom
# async def fasting_notification(s: dict, user: User, context: ContextTypes.DEFAULT_TYPE, tz_offset: timedelta):
#     # Очень грубый расчет
#     f = calculate_fastings(lat=user.lat, long=user.long, num=2, step=60 * 60)
#     logger.info("ℹ️ Ближайшее {}: 🗓 {:%A, %-d %B}".format(s['tithi'][f[0]['name']], f[0]['start']))
#     if user.days == 1 and not f[0]['name'] == 'ekadashi':
#         logger.info('Не экадаши')
#         return
#
#     fast_day = f[0]['start']
#     if fast_day.hour > 18:
#         fast_day += datetime.timedelta(days=1)
#
#     until_event = fast_day - datetime.datetime.now()
#     if until_event.days > 3:
#         logger.info(f"❎🗓 Мероприятие начнётся только {naturaltime(-until_event)}")
#         return
#
#     # Делаем более точный перерасчёт
#     f = calculate_fastings(lat=user.lat, long=user.long, num=2, step=30, tz_offset=tz_offset)
#
#     message = "Намаскар! 🙏 "
#     message += f"Уже {gethumanday(fast_day)} ({dt.ru_strftime('🗓 %-d %B', fast_day, inflected=True, inflected_day=True)}), "
#     message += f"\n{dt.ru_strftime('В %A', fast_day, inflected=True, inflected_day=True)}, начнется"
#
#
#
#     if f[0]['name'] == 'ekadashi':
#         message += " Экадаши 🌘 – одиннадцатый день после новолуния или полнолуния, наиболее благоприятный день для голодания!"
#     else:
#         if f[0]['name'] == 'purnima':
#             message += " Пурнима 🌕 (Полнолуние)"
#         else:
#             message += " Амавасья 🌑 (Новолуние)"
#     message += '\n----\n'
#
#     message += f"Время начала титхи и его конец:\n"
#     message += "<b>⌚ {:%-d %B, %H:%M} – ⌚ {:%-d %B, %H:%M}</b>".format(f[0]['start'], f[0]['end'])
#
#     message += '\n----\n'
#
#     message += "Ты можешь в любой момент отписаться от рассылки через команду /stop."
#     await context.bot.send_message(user.tg_id, message, parse_mode=ParseMode.HTML)
#
#
# async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     users = db.query(User).all()
#     for user in users:
#         if not user.active:
#             continue
#         await fasting_notification(user, context)
#
#
# @user_language_custom
# async def send_local_message(s: dict, user: User, key: str, context: ContextTypes.DEFAULT_TYPE) -> Message:
#     return await context.bot.send_message(user.tg_id, s[key], parse_mode=ParseMode.HTML)
#
#
# async def every_time(context: ContextTypes.DEFAULT_TYPE):
#     users = db.query(User).all()
#     for user in users:
#         # Если пользователь отказался от уведомлений
#         if not user.active or user.days == 0:
#             continue
#
#         # Если прошло меньше N дней от последнего уведомления
#         last_touch = datetime.datetime.utcnow() - user.last_touch
#         if last_touch.days < 1:
#             logger.info(
#                 "Еще не время оповещать. " +
#                 f"Пользователь: #{user.id}. " +
#                 f"Последнее оповещение: {user.last_touch}, прошло всего {naturaltime(-last_touch)}")
#             continue
#
#         try:
#             timezone_str = tf.certain_timezone_at(lat=float(user.lat), lng=float(user.long))
#         except Exception as e:
#             logger.info("Could not determine the time zone")
#             await send_local_message(user, 'location_error', context)
#             user.last_touch = datetime.datetime.utcnow()
#             raise Exception(str(e) + '\n' + user.__repr__())
#
#         # Display the current time in that time zone
#         timezone = pytz.timezone(timezone_str)
#         dt = datetime.datetime.utcnow()
#         current_time = dt + timezone.utcoffset(dt)
#         logger.info("id: %d, The time in %s is %s" % (user.tg_id, timezone_str, current_time))
#         # Тихий час
#         if current_time.hour < 7 or current_time.hour > 22:
#             logger.info("🤫 Тихий час!")
#             return
#
#         await fasting_notification(user, context, timezone.utcoffset(dt))
#         user.last_touch = datetime.datetime.utcnow()
#         db.commit()
#
#
# def main():
#     application = StartConversation()
#     application.add_handler(CommandHandler('test', test))
#
#     # interval - в секундах, first - через сколько первый запуск
#     application.job_queue.run_repeating(every_time, interval=120 * 60, first=1)
#     # Run the bot until the user presses Ctrl-C
#     application.run_polling()
