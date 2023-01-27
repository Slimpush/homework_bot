class TokenNotFoundException(Exception):
    """Обработка исключения при отсуствии токена."""
    pass


class MessageErrorException(Exception):
    """Обработка исключения при неверном chat_id."""
    pass


class EndPointIsNotAvailiable(Exception):
    """Обработка исключения при недоступности ENDPOINT API."""
    pass


class WrongResponseCode(Exception):
    """Неверный ответ API."""
    pass


class EmptyResponse(Exception):
    """Пустой ответ API."""
    pass
