class EndPointIsNotAvailiable(Exception):
    """Обработка исключения при недоступности ENDPOINT API."""
    pass


class WrongResponseCode(Exception):
    """Неверный ответ API."""
    pass


class EmptyResponse(Exception):
    """Пустой ответ API."""
    pass
