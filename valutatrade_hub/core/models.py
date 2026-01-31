import hashlib

from valutatrade_hub.core.exceptions import InsufficientFundsError


class User():
    '''
    Пример хранения в JSON (users.json):
    [
    {
    "user_id": 1,
    "username": "alice",
    "hashed_password": "3e2a19...",
    "salt": "x5T9!",
    "registration_date": "2025-10-09T12:00:00"
    }
    ]
    '''

    def __init__(self, user_id, username, password, salt, date):
        self.__user_id = user_id
        self.__username = username
        self.__hashed_password = password
        self.__salt = salt
        self.__registration_date = date

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(
            (password + self.__salt).encode()
        ).hexdigest()


    @property
    def username(self):
        return self.__username

    @username.setter
    def username(self, name):
        if not name:
            raise ValueError("Имя не может быть пустым")
        self.__username = name

    @property
    def user_id(self):
        return self.__user_id

    @user_id.setter
    def user_id(self, value: int):
        if value <= 0:
            raise ValueError("user_id должен быть положительным")
        self.__user_id = value

    @property
    def registration_date(self):
        return self.__registration_date

    def get_user_info(self) -> dict:
        return {
            "user_id": self.__user_id,
            "username": self.__username,
            "registration_date": self.__registration_date,
        }

    def change_password(self, new_password: str):
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self.__hashed_password = self._hash_password(new_password)

    def verify_password(self, password: str) -> bool:
        return self.__hashed_password == self._hash_password(password)


class Wallet():
    '''
    Пример хранения в JSON (в составе портфеля):
    {
    "BTC": {"currency_code": "BTC", "balance": 0.05},
    "USD": {"currency_code": "USD", "balance": 1200.0}
    }
    '''

    def __init__(self, currency_code):
        self.currency_code = currency_code
        self.__balance = 0.0

    @property
    def balance(self) -> float:
        return self.__balance

    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self.__balance = float(value)

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        self.balance += amount

    def withdraw(self, amount: float):
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        if amount > self.balance:
            raise InsufficientFundsError(self.currency_code, self.balance, amount)
        self.balance -= amount

    def get_balance_info(self) -> dict:
        return {
            "currency": self.currency_code,
            "balance": self.balance
        }


class Portfolio():
    '''
    При покупке валюты сумма списывается с USD-кошелька.
    При продаже — сумма начисляется на USD-кошелёк.
    Пример хранения в JSON (portfolios.json):

    [
    {
    "user_id": 1,
    "wallets": {
    "USD": {"balance": 1500.0},
    "BTC": {"balance": 0.05},
    "EUR": {"balance": 200.0}
    }
    }
    ]
    '''

    def __init__(self, user_id, wallets: dict[str, Wallet]):
        self.__user_id = user_id
        self.__wallets = wallets

    def add_currency(self, currency_code: str):
        if not currency_code:
            raise ValueError("Код валюты не может быть пустым")

        currency_code = currency_code.upper()

        if currency_code not in self.__wallets:
            self.__wallets[currency_code] = Wallet(currency_code)

    def get_total_value(self, base_currency='USD'):
        '''
        возвращает общую стоимость всех валют пользователя в указанной базовой валюте
        '''
        exchange_rates = {
            "USD": 1.0,
            "EUR": 1.08,
            "RUB": 0.010,
            "BTC": 59000,
        }

        if base_currency not in exchange_rates:
            raise ValueError(f"Неизвестная базовая валюта '{base_currency}'")

        total = 0.0
        for code, wallet in self.__wallets.items():
            if code not in exchange_rates:
                continue
            total += wallet.balance * exchange_rates[code] / exchange_rates[base_currency]

        return total

    def get_wallet(self, currency_code):
        '''
        возвращает объект Wallet по коду валюты.
        '''
        return self.__wallets.get(currency_code)

    @property
    def user_id(self):
        return self.__user_id

    @property
    def wallets(self):
        return self.__wallets.copy()
