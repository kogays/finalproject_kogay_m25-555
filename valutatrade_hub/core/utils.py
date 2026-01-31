import json
from datetime import datetime

from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.updater import RatesUpdater

config = ParserConfig()

def from_json(filepath):
    '''
    Загружает данные из JSON-файла.
    Если файл не найден, возвращает пустой словарь {}.
    Используйте try...except FileNotFoundError.
    '''
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return {}

def to_json(filepath, data):
    '''
    Сохраняет переданные данные в JSON-файл.
    '''
    with open(filepath, 'w') as file:
        json.dump(data, file)

def get_rates(to_currency: str):
    try:
        with open("data/rates.json", "r") as file:
            loaded = json.load(file)

        pairs = loaded.get("pairs", {})
        last_refresh_str = loaded.get("last_refresh")

        need_update = False

        if not last_refresh_str:
            need_update = True
        else:
            try:
                last_refresh = datetime.strptime(
                    last_refresh_str, "%Y-%m-%dT%H:%M:%S"
                )
                minutes = (datetime.now() - last_refresh).total_seconds() / 60
                if minutes > 5:
                    need_update = True
            except ValueError:
                need_update = True

        if need_update:
            updater = RatesUpdater(config)
            updater.run_update(None)

            with open("data/rates.json", "r") as file:
                loaded = json.load(file)
            pairs = loaded.get("pairs", {})
            last_refresh_str = loaded.get("last_refresh")

        # фильтрация курсов
        valid_rates = {
            pair.split("_")[0]: data["rate"]
            for pair, data in pairs.items()
            if pair.endswith(f"_{to_currency}")
        }

        update_dates = [last_refresh_str] * len(valid_rates)

        return valid_rates, update_dates

    except FileNotFoundError:
        return {}, []
