class CurrencyNotFoundError(Exception):
    """
    Неизвестная валюта.
    """
    def __init__(self, code: str):
        self.currency_code = code
        super().__init__(f"Неизвестная валюта '{code}'")


class InsufficientFundsError(Exception):
    """
    Недостаточно средств.
    """
    def __init__(self, code: str, available: float, required: float):
        self.currency_code = code
        self.available = available
        self.required = required
        super().__init__(
            f"Недостаточно средств: доступно {available} {code}, требуется {required} {code}"
        )


class ApiRequestError(Exception):
    """
    Ошибка внешнего API.
    """
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
