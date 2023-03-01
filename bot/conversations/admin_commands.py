import random

import i18n
from telegram.ext import ConversationHandler

from bot import db, User, logger
from bot.conversations import *
from bot.conversations.notifications import every_time
from bot.services.weather import get_city
from bot.settings import settings
from bot.utils.i18n_start import set_lang
from bot.utils.timezones import get_timezone
from fastings.calculations import calculate_fasting_days


async def admin_get_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END

    users = db.query(User).order_by(User.id).all()
    msg = f"Пользователей: <b>{len(users)}</b>"
    for user in users:

        tg = await context.bot.get_chat_member(user.tg_id, user.tg_id)
        msg += f'\n{random.choice(["🥸","😜","😇","🥳","🤩"])}<b>{user.id}</b>: {tg.user.mention_html()}, '
        msg += user.created_at.strftime("Создан: <b>(%-d %B %Yг. %H:%M:%S UTC)</b> ")

    await update.message.reply_text(
        msg,
        parse_mode=ParseMode.HTML
    )

    return ConversationHandler.END


async def admin_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END

    msg_input = update.message.text.split(" ", 1)

    if len(msg_input) != 2:
        await update.message.reply_text("IDs после комманды")
        return ConversationHandler.END

    ids = [int(n) for n in msg_input[1].split(', ')] + [settings.developer]

    for idx in ids:
        try:
            developer = await context.bot.get_chat_member(settings.developer, settings.developer)
            tg_user = await context.bot.get_chat_member(idx, idx)
            await context.bot.send_message(idx,
               f'Намаскар, {tg_user.user.mention_html()}! ' +
               'Была ошибка при которой у тебя не получилось зарегистрироваться, ' +
               'можешь пожалуйста снова нажать на команду /start чтобы еще раз начать регистрацию? Спасибо!\n\n' +
               f'Если что-то не получится, напиши разработчику: {developer.user.mention_html()}',
                                           parse_mode=ParseMode.HTML
                                           )
        except Exception as e:
            logger.error(f'{e}: {idx}')
            await context.bot.send_message(idx, f'<pre>{e}: {idx}</pre>')
        context.user_data.clear()

    return ConversationHandler.END


async def admin_notify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END

    i18n.set("locale", update.effective_user.language_code)
    if not await every_time(context, safe=False):
        await update.message.reply_text("Возможно еще рано оповещать или ближайшее титхи не то, которое ты выбрал...")
    return ConversationHandler.END


async def admin_tithi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END

    msg_input = update.message.text.split(" ", 1)

    if len(msg_input) != 2:
        await update.message.reply_text("Город после команды")
        return ConversationHandler.END

    set_lang(update.effective_user.language_code)

    loc = await get_city(msg_input[1])
    if not loc:
        await update.message.reply_text(t('phrases.something_wrong') + '. ' + t('phrases.try_again'))
        return ConversationHandler.END

    tz = get_timezone(loc[0], loc[1])
    # Делаем более точный перерасчёт
    f = calculate_fasting_days(tz.place)
    fasting_message = ""

    for _, fasting in f.iterrows():
        is_ekadashi = fasting['tithi'] == 'ekadashi'
        this_row = '\n' + t('words.' + fasting['tithi'], count=1).capitalize()
        this_row += ":\n⌚ {:%-d %B, %H:%M} – ⌚ {:%-d %B, %H:%M}".format(
            fasting['starts'],
            fasting['ends'])
        fasting_message += '<b>' + this_row + '</b>' if is_ekadashi else this_row

    msg = t('words.regarding', place=tz.place) + ':'
    msg += fasting_message
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    return ConversationHandler.END
