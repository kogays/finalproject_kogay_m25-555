from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    def __init__(self, name, code):
        if name != '':
            self.name = name
        if code == code.upper() and 2 <= len(code) <= 5 and ' ' not in code:
            self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        pass


class FiatCurrency(Currency):
    def __init__(self, name, code, issuing_country):
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f'Fiat: "[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"'


class CryptoCurrency(Currency):
    def __init__(self, name, code, algorithm, market_cap):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        return f'Crypto: "[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {self.market_cap})"'


class CurrencyMaker():
    def __init__(self):
        self.__currency_dict = {'USD': FiatCurrency('US Dollar', 'USD', 'United States'),
                                'BTC': CryptoCurrency('Bitcoin', 'BTC', 'SHA-256', '1.12e12'),
                                'ETH': CryptoCurrency('Ethirium', 'ETH', 'SHA-256', '1.12e12'),
                                'SOL': CryptoCurrency('Solana', 'SOL', 'SHA-256', '1.12e12'),
                                'EUR': FiatCurrency('Euro', 'EUR', 'European Union'),
                                'GBR': FiatCurrency('Britain Pound', 'GBR', 'Great Britain'),
                                'RUB': FiatCurrency('Ruble', 'RUB', 'Russian Federation'),
                                }

    def get_currency(self, code: str):
        code_upper = code.upper()
        currency = self.__currency_dict.get(code_upper)
        if currency is None:
            raise CurrencyNotFoundError(code_upper)
        return currency

    def get_currency_list(self):
        return self.__currency_dict.keys()