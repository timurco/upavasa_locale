import random

from telegram.ext import ConversationHandler

from bot import db, User, logger, Message
from bot.conversations import *
from bot.conversations.notifications import fasting_notification
from bot.services.weather import get_city
from bot.settings import settings
from bot.utils import emo
from bot.utils.i18n_start import set_lang
from bot.utils.phrases import *
from bot.utils.timezones import get_timezone
from fastings.calculations import calculate_fasting_days


async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END

    msg_input = update.message.text.split(" ", 1)
    if len(msg_input) != 2 or not (r := msg_input[1].split('-')):
        await update.message.reply_text("<b>format:</b> /admin_cancel [FROM]-[TO]", parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    last_message = await update.message.reply_text(emo.get(emo.time) + ' ' + t('words._moment'))

    _from = int(r[0])
    _to = int(r[1]) + 1

    deleted = 0
    for message_id in range(_from, _to):
        message = db.query(Message).filter_by(message_id=message_id).first()
        if not message:
            continue

        try:
            await context.bot.delete_message(message.user.tg_id, message_id)
            logger.info(f'🗑 Удаляю сообщение {message.id}:{message.message_id}')
            deleted += 1
        except Exception as e:
            logger.error(f'❌ Не получилось удалить сообщение {message.id}:{message.message_id}. Error: {e.__str__()}')

        db.delete(message)
    db.commit()
    await context.bot.edit_message_text(f"🗑 {deleted} из {_to-_from} сообщений удалено", update.effective_user.id, last_message.id)


async def admin_get_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END

    users = db.query(User).order_by(User.id).all()
    msg = f"Пользователей: <b>{len(users)}</b>"
    for user in users:
        tg = await context.bot.get_chat_member(user.tg_id, user.tg_id)
        msg += f'\n{random.choice(["🥸", "😜", "😇", "🥳", "🤩"])}<b>{user.id}</b>: {tg.user.mention_html()}, '
        msg += user.created_at.strftime("Создан: <b>(%-d %B %Yг. %H:%M:%S UTC)</b> ")

    await update.message.reply_text(
        msg,
        parse_mode=ParseMode.HTML
    )

    return ConversationHandler.END


async def admin_notify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END

    user = db.query(User).filter_by(tg_id=update.effective_user.id).first()
    set_lang(user.lang_code)
    tz = get_timezone(float(user.lat), float(user.long))
    if not await fasting_notification(user, context, tz, settings.notification_days):
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


def text_to_html(text: str, entities) -> str:
    """Конвертирует текст с entities в HTML-строку."""
    if not entities:
        return text

    # Группируем entities по позициям (offset, offset+length)
    # и комбинируем пересекающиеся
    position_map = {}
    for entity in entities:
        key = (entity.offset, entity.offset + entity.length)
        if key not in position_map:
            position_map[key] = []
        position_map[key].append(entity)

    result = ""
    last_offset = 0

    # Обрабатываем позиции в порядке offset
    for (start, end), entity_list in sorted(position_map.items()):
        # Добавляем текст до текущей позиции
        result += text[last_offset:start]

        # Получаем текст для этой позиции
        entity_text = text[start:end]

        # Собираем все типы форматирования для этой позиции
        formatting_tags = []
        for entity in entity_list:
            if entity.type == 'bold':
                formatting_tags.append(('b', '<b>', '</b>'))
            elif entity.type == 'italic':
                formatting_tags.append(('i', '<i>', '</i>'))
            elif entity.type == 'underline':
                formatting_tags.append(('u', '<u>', '</u>'))
            elif entity.type == 'strikethrough':
                formatting_tags.append(('s', '<s>', '</s>'))
            elif entity.type == 'code':
                formatting_tags.append(('code', '<code>', '</code>'))
            elif entity.type == 'pre':
                formatting_tags.append(('pre', '<pre>', '</pre>'))
            elif entity.type == 'text_link':
                formatting_tags.append(('a', f'<a href="{entity.url}">', '</a>'))
            elif entity.type == 'mention':
                formatting_tags.append(('mention', f'<a href="https://t.me/{entity_text[1:]}">', '</a>'))

        # Применяем форматирование - открываем теги в правильном порядке
        formatted_text = entity_text
        for _, open_tag, close_tag in formatting_tags:
            formatted_text = f"{open_tag}{formatted_text}{close_tag}"

        result += formatted_text
        last_offset = end

    # Добавляем оставшийся текст
    result += text[last_offset:]

    return result


def replace_placeholders(text: str) -> str:
    """Заменяет плейсхолдеры типа #namaskar на результат вызова соответствующих функций."""
    replacements = {
        '#namaskar': namaskar(),
        '#all_days_string': all_days_string(),
    }

    for placeholder, replacement in replacements.items():
        text = text.replace(placeholder, replacement)

    return text


async def admin_send_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало команды admin_send."""
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END

    await update.message.reply_text(
        "📝 <b>Создание массовой рассылки</b>\n\n"
        "Напишите сообщение для отправки всем пользователям.\n"
        "Вы можете использовать следующие плейсхолдеры:\n"
        "• <code>#namaskar</code> - приветствие\n"
        "• <code>#all_days_string</code> - список всех дней\n\n"
        "Отправьте сообщение или нажмите /cancel для отмены.",
        parse_mode=ParseMode.HTML
    )
    return ADMIN_MESSAGE


async def admin_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение сообщения от админа и показ превью."""
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END

    # Конвертируем текст с entities в HTML
    html_text = text_to_html(update.message.text, update.message.entities)
    processed_text = replace_placeholders(html_text)

    # Сохраняем оригинальное и обработанное сообщение в контексте
    context.user_data['original_html'] = html_text
    context.user_data['processed_message'] = processed_text

    # Создаем клавиатуру для подтверждения
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text='✅ Отправить всем', callback_data='admin_send_confirm'),
            InlineKeyboardButton(text='❌ Отменить', callback_data='admin_send_cancel'),
        ]
    ])

    # Показываем превью сообщения с форматированием
    preview_text = (
        "📋 <b>Превью сообщения:</b>\n\n"
        f"{processed_text}\n\n"
        "🤔 <b>Вы уверены, что хотите отправить это сообщение всем пользователям?</b>"
    )

    await update.message.reply_text(preview_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    return ADMIN_CONFIRM


async def admin_send_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Подтверждение и отправка сообщения всем пользователям."""
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END

    query = update.callback_query
    await query.answer()

    if query.data == 'admin_send_confirm':
        message_text = context.user_data.get('processed_message', '')

        if not message_text:
            await query.edit_message_text("❌ Ошибка: сообщение не найдено")
            return ConversationHandler.END

        # Получаем всех активных пользователей
        users = db.query(User).filter(User.active == True).all()
        sent_count = 0
        failed_count = 0

        status_message = await context.bot.send_message(
            settings.developer,
            f"📤 Начинаю рассылку {len(users)} пользователям..."
        )

        for user in users:
            try:
                await context.bot.send_message(
                    user.tg_id,
                    message_text,
                    parse_mode=ParseMode.HTML,
                    disable_notification=True
                )
                sent_count += 1

                # Обновляем счетчик каждые 10 сообщений
                if sent_count % 10 == 0:
                    await context.bot.edit_message_text(
                        f"📤 Отправлено: {sent_count}/{len(users)}",
                        settings.developer,
                        status_message.message_id
                    )

            except Exception as e:
                logger.error(f"❌ Не удалось отправить пользователю {user.tg_id}: {e}")
                failed_count += 1

        # Финальный отчет
        final_text = (
            f"✅ <b>Рассылка завершена!</b>\n\n"
            f"📤 Отправлено: {sent_count}\n"
            f"❌ Ошибок: {failed_count}\n"
            f"👥 Всего пользователей: {len(users)}"
        )

        await context.bot.edit_message_text(final_text, settings.developer, status_message.message_id, parse_mode=ParseMode.HTML)

    else:  # admin_send_cancel
        await query.edit_message_text("❌ Рассылка отменена")

    context.user_data.clear()
    return ConversationHandler.END


async def admin_send_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена рассылки."""
    if update.effective_user.id != settings.developer:
        return ConversationHandler.END

    await update.message.reply_text("❌ Рассылка отменена")
    context.user_data.clear()
    return ConversationHandler.END
