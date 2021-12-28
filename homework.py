import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

logging.basicConfig(
    level=logging.INFO,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('my_logger.log', maxBytes=50000000,
                              backupCount=5)
logger.addHandler(handler)

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    correct_responses = ['approved', 'rejected']
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None:
        raise Exception('Домашняя работа в ответе сервера не найдена!')
    if homework_status is None:
        raise Exception('Не удалось распознать статус в результатах проверки!')
    if homework_status not in correct_responses:
        raise Exception('Неверный ответ сервера!')
    if homework_status == 'rejected':
        verdict = 'К сожалению, в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(URL, headers=headers, params=payload)
        return homework_statuses.json()
    except requests.exceptions.Timeout:
        raise Exception('Сервер отвалился по таймауту')
    except requests.exceptions.RequestException:
        raise Exception('Что-то не так с запросом к серверу')
    except requests.exceptions.ConnectionError:
        raise Exception('Не удалось соедениться с сайтом Яндекс.Практикум')
    except requests.exceptions.InvalidHeader:
        raise Exception('Ошибка в Header')
    except requests.exceptions.InvalidURL:
        raise Exception('Неаверно сформирована ссылка')
    except TypeError:
        raise Exception('Не удалось преобразовать ответ в JSON')
    except ValueError:
        raise Exception('Не удалось преобразовать ответ в JSON (Value error)')
    except Exception as e:
        raise Exception(e)


def send_message(message):
    return bot.send_message(CHAT_ID, message)


def main():
    current_timestamp = int(time.time())
    logging.debug('Скрипт успешно запущен.')
    while True:
        try:
            all_homeworks = get_homeworks(current_timestamp)
            if len(all_homeworks['homeworks']) > 0:
                homework = all_homeworks['homeworks'][0]
                send_message(parse_homework_status(homework))
                homework_name = homework.get('homework_name')
                logging.info('Статус для домашней работы '
                             f'{homework_name} обновлен и отправлен')
                current_timestamp = int(all_homeworks['current_date'])
            time.sleep(5 * 60)

        except Exception as e:
            logging.error(e, exc_info=True)
            send_message(f'Бот упал с ошибкой: {e}')
            time.sleep(5 * 60)


if __name__ == '__main__':
    main()
