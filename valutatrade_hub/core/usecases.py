import hashlib
import random
from datetime import datetime

from prettytable import PrettyTable

from valutatrade_hub.core.currencies import CurrencyMaker
from valutatrade_hub.core.exceptions import CurrencyNotFoundError, InsufficientFundsError
from valutatrade_hub.core.utils import from_json, get_rates, to_json
from valutatrade_hub.decorators import log_action
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.updater import RatesUpdater

config = ParserConfig()


def register(username, password):
    data = from_json('data/users.json')
    names = [val.get('username') for val in data]
    ids = [val.get('user_id') for val in data]
    if username in names:
        print(f'Имя пользователя {username} уже занято')
        return None
    if len(password) < 4:
        print('Пароль должен быть не короче 4 символов')
        return None
    current_id = len(ids) + 1
    symbols = list('1234567890-=+*%!?><$#@;:qwertyuiopasdfghjklzxcvbnm')
    salt = ''.join(random.choices(symbols, k=random.randint(5, 20)))
    hashed_password = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    current_datetime = datetime.now()
    new_user_info = {"user_id": current_id,
                     "username": username,
                     "hashed_password": hashed_password,
                     "salt": salt,
                     "registration_date": str(current_datetime)}
    data.append(new_user_info)
    to_json('data/users.json', data)
    portfolio_info = {"user_id": current_id, "wallets": {}}
    portfolios = from_json('data/portfolios.json')
    portfolios.append(portfolio_info)
    to_json('data/portfolios.json', portfolios)
    return current_id


def login(username, password):
    data = from_json('data/users.json')
    res = [(val.get('salt'),
            val.get('hashed_password'),
            val.get('user_id'))
           for val in data if val.get('username') == username]
    if len(res) == 0:
        print(f'Пользователь {username} не найден')
        return None
    salt, hashed_password, current_id = res[0]
    if hashed_password != hashlib.sha256((password + salt).encode('utf-8')).hexdigest():
        print('Неверный пароль')
        return None
    return current_id


def show_portfolio(logged_in, logged_id, base_currency=config.BASE_CURRENCY):
    if not logged_in:
        print('Сначала выполните login')
        return None
    if base_currency is None:
        base_currency = config.BASE_CURRENCY
    portfolios = from_json('data/portfolios.json')
    portfolio = [val for val in portfolios if val.get('user_id') == logged_id][0]
    wallets = portfolio.get('wallets')
    if len(wallets.keys()) == 0:
        print('Кошельков нет')
        return None
    if base_currency != config.BASE_CURRENCY:
        print(f'Неизвестная базовая валюта {base_currency}')
        return None
    exchange_rates, _ = get_rates(base_currency)
    result = 0.0
    for key in wallets.keys():
        wallet = wallets.get(key)
        if key != config.BASE_CURRENCY:
            diff = wallet.get('balance') * exchange_rates.get(key)
        else:
            diff = wallet.get('balance')
        result += diff
        print(f"- {key}: {wallet.get('balance')}  → {diff} {base_currency}")
    print(f'ИТОГО: {result} {base_currency}')


@log_action()
def buy(logged_id, currency, amount):
    if not logged_id:
        print('Сначала выполните login')
        return None
    amount = float(amount)
    if amount < 0:
        print(f'{amount} должен быть положительным числом')
        return None
    exchange_rates, _ = get_rates(config.BASE_CURRENCY)
    if currency not in exchange_rates.keys():
        print(f'Не удалось получить курс для {currency}→{config.BASE_CURRENCY}')
        return None
    portfolios = from_json('data/portfolios.json')
    portfolio_index = [i for i in range(len(portfolios)) if portfolios[i].get('user_id') == logged_id][0]
    portfolio = portfolios[portfolio_index]
    wallets = portfolio.get('wallets')
    if currency not in wallets.keys():
        wallets.update({currency: {"balance": 0.0}})
    before = wallets[currency]["balance"]
    cost = amount * exchange_rates[currency]

    if "USD" not in wallets or wallets["USD"]["balance"] < cost:
        raise InsufficientFundsError(
            "USD",
            wallets["USD"]["balance"] if "USD" in wallets else 0,
            cost
        )

    wallets["USD"]["balance"] -= cost
    wallets[currency]["balance"] += amount

    print(f'- {currency}: было {before} → стало {wallets[currency]["balance"]}')
    print(f'Оценочная стоимость покупки: {cost} {config.BASE_CURRENCY}')
    portfolio['wallets'].update(wallets)
    portfolios[portfolio_index] = portfolio
    to_json('data/portfolios.json', portfolios)


@log_action()
def sell(logged_id, currency, amount):
    if not logged_id:
        print('Сначала выполните login')
        return None
    amount = float(amount)
    portfolios = from_json('data/portfolios.json')
    portfolio_index = [i for i in range(len(portfolios)) if portfolios[i].get('user_id') == logged_id][0]
    portfolio = portfolios[portfolio_index]
    wallets = portfolio.get('wallets')
    if currency not in wallets.keys():
        print(f'У вас нет кошелька {currency}. Добавьте валюту: она создаётся автоматически при первой покупке.')
        return None
    before = wallets[currency]["balance"]
    amount = float(amount)
    try:
        if before < amount:
            raise InsufficientFundsError(currency, before, amount)
    except InsufficientFundsError as e:
        print(e)
        return None
    exchange_rates, _ = get_rates(config.BASE_CURRENCY)
    cost = amount * exchange_rates.get(currency)
    if wallets.get(config.BASE_CURRENCY) is None:
        wallets.update({config.BASE_CURRENCY: {"balance": 0.0}})
    wallets[config.BASE_CURRENCY]["balance"] += cost
    wallets[currency]["balance"] -= amount
    print(
        f'Продажа выполнена: {amount} {currency} по курсу '
        f'{exchange_rates.get(currency)} {config.BASE_CURRENCY}/{currency}')
    print('Изменения в портфеле:')
    print(f'- {currency}: было {before} → стало {wallets[currency]["balance"]}')
    print(f'Оценочная выручка: {cost} {config.BASE_CURRENCY}')
    portfolio['wallets'].update(wallets)
    portfolios[portfolio_index] = portfolio
    to_json('data/portfolios.json', portfolios)


def get_rate(curr_from, curr_to):
    cm = CurrencyMaker()
    try:
        cm.get_currency(curr_from)
        cm.get_currency(curr_to)
    except CurrencyNotFoundError as e:
        print(e)
        currs = ', '.join(cm.get_currency_list())
        print(f'Список доступных валют: {currs}')
        return None
    exchange_rates, update_dates = get_rates(curr_to)
    if len(exchange_rates.keys()) == 0:
        print(f'Курс {curr_from}→{curr_to} недоступен. Повторите попытку позже.')
        return None
    date = update_dates[list(exchange_rates.keys()).index(curr_from)]
    print(f'Курс {curr_from}→{curr_to}: {exchange_rates.get(curr_from)} (обновлено: {date})')
    print(f'Обратный курс {curr_to}→{curr_from}: {1 / exchange_rates.get(curr_from)}')


def update_rates(source):
    sources = [source] if source else None
    try:
        updater = RatesUpdater(config)
        count = updater.run_update(sources)
        last_refresh = datetime.now()
        if count > 0:
            print(
                f"Update successful. Total rates updated: {count}. Last refresh: {last_refresh}"
            )
        else:
            print("Update completed with errors. Check logs/parser.log for details.")
    except Exception as e:
        print(f"Update failed. Error: {e}. Check logs/parser.log for details.")


def show_rates(currency: str | None, top: str | None, base: str | None):
    base = base.upper() if base else config.BASE_CURRENCY

    rates_data = from_json("data/rates.json")
    if (
        not isinstance(rates_data, dict)
        or "pairs" not in rates_data
        or not rates_data["pairs"]
    ):
        print("Кеш курсов пуст. Выполните update-rates")
        return

    pairs = rates_data["pairs"]
    last_update = rates_data.get("last_refresh", "unknown")

    print(f"Rates from cache (updated at {last_update})")

    table = PrettyTable(["Pair", "Rate"])

    # --- курс base → USD ---
    if base == "USD":
        base_usd_rate = 1.0
    else:
        base_usd_pair = f"{base}_USD"
        if base_usd_pair not in pairs:
            print(f"Базовая валюта '{base}' не найдена в кеше")
            return
        base_usd_rate = pairs[base_usd_pair]["rate"]

    # --- показать конкретную валюту ---
    if currency:
        currency = currency.upper()
        pair_usd = f"{currency}_USD"

        if pair_usd not in pairs:
            print(f"Курс для '{currency}' не найден")
            return

        rate_usd = pairs[pair_usd]["rate"]
        rate_base = rate_usd / base_usd_rate

        table.add_row([f"{currency}_{base}", f"{rate_base:.5f}"])
        print(table)
        return

    # --- показать TOP N ---
    if top:
        top_n = int(top)

        crypto_pairs = {
            code: data["rate"]
            for pair, data in pairs.items()
            if (code := pair.split("_")[0]) in config.CRYPTO_CURRENCIES
        }

        sorted_crypto = sorted(
            crypto_pairs.items(),
            key=lambda x: x[1] / base_usd_rate,
            reverse=True
        )[:top_n]

        for code, rate_usd in sorted_crypto:
            rate_base = rate_usd / base_usd_rate
            table.add_row([f"{code}_{base}", f"{rate_base:.5f}"])

        print(table)
        return

    # --- показать все курсы ---
    for pair_usd, data in sorted(pairs.items()):
        code = pair_usd.split("_")[0]
        rate_usd = data["rate"]
        rate_base = rate_usd / base_usd_rate
        table.add_row([f"{code}_{base}", f"{rate_base:.5f}"])

    print(table)
