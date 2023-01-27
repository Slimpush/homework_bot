import logging
import os
import telegram
import time
import requests
import exceptions

from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

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
    chat_id = TELEGRAM_CHAT_ID
    text = message
    try:
        bot.send_message(chat_id, text)
        logging.debug('Сообщение отправлено успешно')
    except Exception as error:
        logging.error(error)


def get_api_answer(timestamp):
    """Отправляем запрос к API и получаем список домашних работ."""
    timestamp = {'from_date': 1676106000}
    params_request = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp},
    }
    try:
        response = requests.get(**params_request)
        if response.status_code != 200:
            raise exceptions.EndPointIsNotAvailiable(response.status_code)
        return response.json()
    except Exception as error:
        message = ('Неверный ответ API. Запрос: {url}, {headers}, {params}.'
                   ).format(**params_request)
        raise exceptions.WrongResponseCode(message, error)


def check_response(response):
    """Проверяем валидность ответа."""
    if not isinstance(response, dict):
        raise TypeError('Переменная response не соответствует документации')
    if 'homeworks' not in response or 'current_date' not in response:
        raise exceptions.EmptyResponse('В ответе API нет ключа homeworks')
    homeworks_list = response['homeworks']
    if not isinstance(homeworks_list, list):
        raise TypeError('Homeworks не является списком')
    return homeworks_list


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
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    if not check_tokens():
        message = 'Не хватает нужного токена'
        logging.critical(message)
        raise exceptions.TokenNotFoundException(message)

    while True:
        try:
            response = get_api_answer(timestamp)
            homework_list = check_response(response)
            homework = homework_list[0]
            message = parse_status(homework)
            send_message(bot, message)
            timestamp = response.get('current_date')

        except exceptions.MessageErrorException as error:
            message = f'Не удалось отправить сообщение в Telegram - {error}'
            logging.error(message)
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
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(
        'my_logger.log',
        maxBytes=50000000,
        backupCount=5
    )
    logger.addHandler(handler)

    main()
