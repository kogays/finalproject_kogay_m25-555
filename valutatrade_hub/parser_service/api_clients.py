from abc import ABC, abstractmethod

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    @abstractmethod
    def fetch_rates(self) -> dict:
        pass


class CoinGeckoClient(BaseApiClient):
    def __init__(self, config: ParserConfig):
        super().__init__()
        self.config = config

    def fetch_rates(self) -> dict:
        ids = ",".join(
            self.config.CRYPTO_ID_MAP[code] for code in self.config.CRYPTO_CURRENCIES
        )
        url = f"{self.config.COINGECKO_URL}?ids={ids}&vs_currencies={self.config.BASE_CURRENCY.lower()}"
        response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            rates = {}
            for code, coin_id in self.config.CRYPTO_ID_MAP.items():
                if (
                        coin_id in data
                        and self.config.BASE_CURRENCY.lower() in data[coin_id]
                ):
                    pair = f"{code}_{self.config.BASE_CURRENCY}"
                    rates[pair] = {
                        "rate": data[coin_id][self.config.BASE_CURRENCY.lower()],
                        "meta": {
                            "raw_id": coin_id,
                            "request_ms": response.elapsed.total_seconds() * 1000,
                            "status_code": response.status_code,
                            "etag": response.headers.get("etag", "")
                        }
                    }
            return rates
        else:
            raise ApiRequestError(f"Ошибка: {response.status_code}")


class ExchangeRateApiClient(BaseApiClient):
    def __init__(self, config: ParserConfig):
        super().__init__()
        self.config = config

    def fetch_rates(self) -> dict:
        if not self.config.EXCHANGERATE_API_KEY:
            raise ValueError("EXCHANGERATE_API_KEY не установлен")
        url = (f"{self.config.EXCHANGERATE_API_URL}/"
               f"{self.config.EXCHANGERATE_API_KEY}/latest/{self.config.BASE_CURRENCY}")
        response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("result") != "success":
                raise ApiRequestError(f"ExchangeRate-API: {data}")
            rates = {}
            base = self.config.BASE_CURRENCY
            for code in self.config.FIAT_CURRENCIES:
                if code in data["conversion_rates"]:
                    usd_to_code = data["conversion_rates"][code]
                    rate_code_usd = 1 / usd_to_code if usd_to_code != 0 else 0.0
                    pair = f"{code}_{base}"
                    rates[pair] = {
                        "rate": rate_code_usd,
                        "meta": {
                            "raw_rate": usd_to_code,
                            "request_ms": response.elapsed.total_seconds() * 1000,
                            "status_code": response.status_code,
                            "time_last_update_utc": data.get("time_last_update_utc", "")
                        }
                    }
            return rates
        else:
            raise ApiRequestError(f"Ошибка: {response.status_code}")