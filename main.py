import os

import requests
from telegram import ReplyKeyboardMarkup
from telegram.ext import (CommandHandler, Updater)

from get_data import get_all_data
from transform_data import (transform_data,
                            delete_data_from_server,
                            upload_data_to_server)
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHATS = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://api.thecatapi.com/v1/images/search'

updater = Updater(token=TELEGRAM_TOKEN, use_context=True)


def get_new_image():
    response = requests.get(URL).json()
    return response[0].get('url')


def new_cat(update, context):
    chat = update.effective_chat
    allowed_chats = list(map(int, TELEGRAM_CHATS.split()))
    if chat['id'] in allowed_chats:
        context.bot.send_photo(chat.id, get_new_image())
    else:
        context.bot.send_message(
            chat.id,
            'У вас нет прав для выполнения этой команды!')


def update_data(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    allowed_chats = list(map(int, TELEGRAM_CHATS.split()))
    if chat['id'] in allowed_chats:
        context.bot.send_message(
            chat.id,
            'Одну секунду, {}, команда выполняется...'.format(name))
        data = transform_data(get_all_data())
        context.bot.send_message(
            chat.id,
            'Данные с Google sheets загружены...')
        delete_data_from_server()
        context.bot.send_message(
            chat.id,
            'Старые данные с сайта удалены успешно...')
        upload_data_to_server(data)
        context.bot.send_message(
            chat.id,
            'Информация обновлена! Всего строк: ' + str(len(data['results'])))
    else:
        context.bot.send_message(
            chat.id,
            'У вас недостаточно прав для выполнения этой команды!')


def wake_up(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    button = ReplyKeyboardMarkup([['/newcat', '/update']],
                                 resize_keyboard=True)

    context.bot.send_message(
        chat_id=chat.id,
        text='Привет, {}. Активация прошла успешно!'.format(name),
        reply_markup=button
    )


if __name__ == '__main__':
    updater.dispatcher.add_handler(CommandHandler('start', wake_up))
    updater.dispatcher.add_handler(CommandHandler('newcat', new_cat))
    updater.dispatcher.add_handler(CommandHandler('update', update_data))

    updater.start_polling()
    updater.idle()
