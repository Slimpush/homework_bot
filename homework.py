import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRAC_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    logging.info('Начало отправки сообщения в telegram')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except exceptions.TelegramError as error:
        raise exceptions.TelegramError(
            f'Не удалось отправить сообщение {error}')
    except Exception as error:
        logging.error(error)
    else:
        logging.debug('Сообщение отправлено успешно')


def get_api_answer(timestamp):
    """Отправляем запрос к API и получаем список домашних работ."""
    logging.info('Начат запрос к API')
    act_timestamp = timestamp or int(time.time())
    params_request = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': act_timestamp},
    }
    try:
        response = requests.get(**params_request)
        if response.status_code != 200:
            raise exceptions.EndPointIsNotAvailiable(response.status_code)
    except Exception as error:
        message = ('Неверный ответ API. Запрос: {url}, {headers}, {params}.'
                   ).format(**params_request)
        raise exceptions.WrongResponseCode(message, error)
    return response.json()


def check_response(response):
    """Проверяем валидность ответа."""
    if not isinstance(response, dict):
        raise TypeError('Переменная response не соответствует документации')
    if 'homeworks' not in response or 'current_date' not in response:
        raise exceptions.EmptyResponse('В ответе API нет ключа homeworks')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError('Homeworks не является списком')
    return homeworks


def parse_status(homework):
    """Извлекаем информацию о статусе конкретной домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError('В ответе API отсутсвует ключ homework_name')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in (HOMEWORK_VERDICTS):
        raise KeyError('Данного статуса не существует')
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    logging.info('Изменился статус проверки работы')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Не хватает нужного токена'
        logging.critical(message)
        sys.exit('Отсутсвуют переменные окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            homework_list = check_response(response)
            homework = homework_list[0]
            message = parse_status(homework)
            send_message(bot, message)
            timestamp = response.get('current_date')

        except exceptions.EndPointIsNotAvailiable as error:
            message = f'ENDPOINT недоступен. Код ответа API: {error}'
            logging.error(message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.DEBUG,
        filename='main.log',
        filemode='w'
    )
    handler = RotatingFileHandler(
        'my_logger.log',
        maxBytes=50000000,
        backupCount=5
    )
    main()
