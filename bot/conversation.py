# import traceback
#
# from telegram import InlineKeyboardMarkup, InlineKeyboardButton
# from telegram.constants import ParseMode
# from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler, \
#     CallbackQueryHandler, CallbackContext
#
# from bot.services.database import db
# from bot.utils import *
# from fastings import calculate_fastings
# from bot.services.logger import logger
# from settings import settings
# import html
# import json
#
# LOCATION, DAYS, EKADASHI, ALLDAYS, ZERODAYS, CANCEL, DONE, SET_LOCATION, SET_DAYS = range(9)
#
#
# async def error_handler(update: object, context: CallbackContext) -> None:
#     """Log the error and send a telegram message to notify the developer."""
#     # Log the error before we do anything else, so we can see it even if something breaks.
#     logger.error(msg="Exception while handling an update:", exc_info=context.error)
#
#     # traceback.format_exception returns the usual python message about an exception, but as a
#     # list of strings rather than a single string, so we have to join them together.
#     tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
#     tb_string = ''.join(tb_list)
#
#     # Build the message with some markup and additional information about what happened.
#     # You might need to add some logic to deal with messages longer than the 4096 character limit.
#     update_str = update.to_dict() if isinstance(update, Update) else str(update)
#     # context_str = context.
#     message = (
#         f'An exception was raised while handling an update\n'
#         f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>\n'
#         # f'<pre>context = {html.escape(json.dumps(context_str, indent=2, ensure_ascii=False))}</pre>\n'
#         f'\n<pre>{html.escape(tb_string)}</pre>'
#     )
#
#     # Finally, send the message
#     await context.bot.send_message(chat_id=settings.developer, text=message, parse_mode='HTML')
#
#
# @user_language
# async def start(s: dict, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     user = update.effective_user
#
#     await update.message.reply_photo(
#         settings.location_pic,
#         s['hello'] % user.mention_html() + ' ' + s['my_name'] + '\n' + s['mission'] + '\n\n' + s[
#             'start_choose_location'],
#         parse_mode=ParseMode.HTML,
#     )
#     logger.info(user)
#     context.user_data.clear()
#     return LOCATION
#
#
# def get_days_keyboard(s: dict):
#     return InlineKeyboardMarkup([
#         [
#             InlineKeyboardButton(text=s['only_ekadashi'], callback_data=str(EKADASHI)),
#             InlineKeyboardButton(text=s['all_days'], callback_data=str(ALLDAYS)),
#         ],
#         [
#             InlineKeyboardButton(text=s['zero_days'], callback_data=str(ZERODAYS)),
#             InlineKeyboardButton(text=s['cancel'], callback_data=str(CANCEL)),
#         ],
#     ])
#
#
# @user_language
# async def location(s: dict, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     user_location = update.message.location
#     context.user_data['location'] = [user_location.latitude, user_location.longitude]
#
#     await update.message.reply_text(
#         s['ok'] + ' ' + s['location_update'] + '\n' + s['start_choose_day'],
#         reply_markup=get_days_keyboard(s)
#     )
#
#     return DAYS
#
#
# @user_language
# async def ekadashi(s: dict, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     context.user_data['days'] = 1
#     await update.callback_query.edit_message_text(
#         s['ok'] + ' ' + s['ready_to_send'] % s['ekadashi_format'] + '\n' +
#         s['days_update'],
#         parse_mode=ParseMode.HTML
#     )
#     return await set_record(update, context)
#
#
# @user_language
# async def all_days(s: dict, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     context.user_data['days'] = 2
#     await set_record(update, context)
#     await update.callback_query.edit_message_text(
#         s['ok'] + ' ' + s['ready_to_send'] % s['all_days_format'] + '\n' +
#         s['days_update'],
#         parse_mode=ParseMode.HTML
#     )
#     return ConversationHandler.END
#
#
# async def set_record(update: Update, context: ContextTypes.DEFAULT_TYPE, active: bool = True) -> int:
#     logger.info(f"Пробуем добавить или изменить нового пользователя: {context.user_data}")
#
#     user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
#
#     if user:
#         if 'location' in context.user_data.keys():
#             user.lat = str(context.user_data['location'][0])
#             user.long = str(context.user_data['location'][1])
#         if 'days' in context.user_data.keys():
#             user.days = context.user_data['days']
#         user.active = active
#         logger.info(f"✅️ Пользователь изменил данные: {user}")
#         user.last_demand = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
#         user.last_touch = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
#     else:
#         user = User(
#             tg_id=update.effective_user.id,
#             lang_code=update.effective_user.language_code,
#             lat=str(context.user_data['location'][0]),
#             long=str(context.user_data['location'][1]),
#             days=context.user_data['days'],
#             active=True,
#         )
#         logger.info(f"❇️ У нас новый пользователь: {user}")
#     db.add(user)
#     db.commit()
#     return ConversationHandler.END
#
#
# @user_language
# async def cancel(s: dict, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     if db.query(User).filter_by(tg_id=update.effective_user.id).first():
#         msg = s['ok'] + '\n' + s['again']
#     else:
#         msg = s['ok'] + ' ' + s['no_answer'] + '\n' + s['again']
#
#     if update.callback_query:
#         await update.callback_query.edit_message_text(msg)
#     else:
#         await update.message.reply_text(msg)
#     return ConversationHandler.END
#
#
# @user_language
# async def stop(s: dict, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
#
#     if not user:
#         await update.message.reply_text(s['no_user'])
#     else:
#         msg = s['ok'] + ' ' + s['again']
#         if update.callback_query:
#             await update.callback_query.edit_message_text(msg)
#         else:
#             await update.message.reply_text(msg)
#
#         await set_record(update, context, False)
#
#     return ConversationHandler.END
#
#
# @user_language
# async def update_location(s: dict, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
#     if not user:
#         return await start(update, context)
#
#     msg = s['ok'] + ' ' + s['start_choose_location'];
#     if update.callback_query:
#         await context.bot.send_photo(
#             update.callback_query.from_user.id, settings.location_pic, msg, parse_mode=ParseMode.HTML)
#     else:
#         await update.message.reply_photo(settings.location_pic, msg, parse_mode=ParseMode.HTML)
#     return SET_LOCATION
#
#
# @user_language
# async def set_location(s: dict, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     user_location = update.message.location
#     context.user_data['location'] = [user_location.latitude, user_location.longitude]
#     await set_record(update, context)
#     await update.message.reply_text(s['ok'] + ' ' + s['set_location'], parse_mode=ParseMode.HTML)
#     return ConversationHandler.END
#
#
# @user_language
# async def update_days(s: dict, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
#     if not user:
#         await update.message.reply_text(s['location_first'], parse_mode=ParseMode.HTML)
#         return ConversationHandler.END
#
#     await update.message.reply_text(s['ok'] + ' ' + s['start_choose_day'], reply_markup=get_days_keyboard(s))
#     return DAYS
#
#
# @user_language_custom
# async def get_user_fasting(s: dict, user: User, context: ContextTypes.DEFAULT_TYPE):
#     last_message = await context.bot.send_message(user.tg_id, s['tithi_wait'], parse_mode=ParseMode.HTML)
#
#     f = calculate_fastings(lat=float(user.lat), long=float(user.long), num=4)
#     fasting_message = ""
#     for fasting in f:
#         is_ekadashi = fasting['name'] == 'ekadashi'
#         if user.days == 1 and is_ekadashi:
#             continue
#         this_row = "\n%s" % s['tithi'][fasting['name']]
#         this_row += ": ⌚ {:%-d %B, %H:%M} – ⌚ {:%-d %B, %H:%M}".format(
#             fasting['start'],
#             fasting['end'])
#
#         fasting_message += '<b>' + this_row + '</b>' if is_ekadashi else this_row
#
#     await last_message.edit_text(s['tithi_answer'] + fasting_message, parse_mode=ParseMode.HTML)
#
#
# @user_language
# async def demand_fasting(s: dict, update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
#     if not user:
#         await update.message.reply_text(s['meet_first'], parse_mode=ParseMode.HTML)
#         return
#
#     last_demand = datetime.datetime.utcnow() - user.last_demand
#     if last_demand.seconds // 60 < 10:
#         logger.info(f"Последний запрос (минуты): {last_demand.seconds // 60}")
#         await update.message.reply_text(s['to_early'], parse_mode=ParseMode.HTML)
#         return
#
#     user.last_demand = datetime.datetime.utcnow()
#     db.commit()
#     await get_user_fasting(user, context)
#
#
# # noinspection PyTypeChecker
# def StartConversation():
#     # Create the Application and pass it your bot's token.
#     application = Application.builder().token(settings.token).build()
#
#     # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
#     conv_handler = ConversationHandler(
#         entry_points=[
#             CommandHandler("start", start),
#             CommandHandler('update_location', update_location),
#             CommandHandler('update_days', update_days)
#         ],
#         states={
#             LOCATION: [MessageHandler(filters.LOCATION, location)],
#             DAYS: [
#                 CallbackQueryHandler(ekadashi, pattern="^" + str(EKADASHI) + "$"),
#                 CallbackQueryHandler(all_days, pattern="^" + str(ALLDAYS) + "$"),
#                 CallbackQueryHandler(cancel, pattern="^" + str(CANCEL) + "$"),
#                 CallbackQueryHandler(stop, pattern="^" + str(ZERODAYS) + "$")
#             ],
#             SET_LOCATION: [MessageHandler(filters.LOCATION, set_location)]
#         },
#         fallbacks=[
#             CommandHandler("cancel", cancel),
#         ],
#     )
#
#     application.add_handler(CommandHandler('get_fasting', demand_fasting))
#     application.add_handler(CommandHandler('stop', stop))
#     application.add_handler(conv_handler)
#     application.add_error_handler(error_handler)
#
#     return application
