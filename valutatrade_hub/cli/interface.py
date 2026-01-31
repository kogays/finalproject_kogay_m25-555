import shlex

import prompt

from valutatrade_hub.core.usecases import buy, get_rate, login, register, sell, show_portfolio, show_rates, update_rates


def print_help():
    print('Регистрация пользователя: register --username <str> --password <str>')
    print('Авторизация пользователя: login --username <str> --password <str>')
    print('Показать портфолио пользователя в базовой валюте: show-portfolio')
    print('Показать портфолио пользователя в кастомной валюте: show-portfolio --base <str>')
    print('Купить валюту: buy --currency <str> --amount <float>')
    print('Продать валюту: sell --currency <str> --amount <float>')
    print('Получить текущий курс: get-rate --from <str> --to <str>')
    print('Получить актуальные курсы валют: update-rates')
    print('Показать список актуальных курсов: show-rates')
    print('Показать N самых дорогих валют: show-rates --top <int>')
    print('Показать курс конкретной валюты: show-rates --currency <str>')


logged_in = False
logged_id = None


def get_arg(args, name):
    if name in args:
        idx = args.index(name)
        if idx + 1 < len(args):
            return args[idx + 1]
    return None


def run():
    global logged_in, logged_id

    print_help()

    while True:
        query = prompt.string('Введите команду: ')
        args = shlex.split(query)

        if not args:
            continue

        command = args[0]

        try:
            match command:
                case 'register':
                    username = get_arg(args, '--username')
                    password = get_arg(args, '--password')

                    if not username or not password:
                        print('Нужно указать --username и --password')
                        continue

                    user_id = register(username, password)
                    if user_id:
                        print(
                            f"Пользователь '{username}' зарегистрирован (id={user_id}). "
                            f"Войдите: login --username {username} --password {'*' * len(password)}"
                        )

                case 'login':
                    username = get_arg(args, '--username')
                    password = get_arg(args, '--password')

                    logged_id = login(username, password)
                    if logged_id:
                        logged_in = True
                        print(f"Вы вошли как '{username}'")

                case 'show-portfolio':
                    if not logged_in:
                        print('Сначала выполните login')
                        continue

                    base = get_arg(args, '--base')
                    show_portfolio(logged_in, logged_id, base_currency=base)

                case 'buy':
                    if not logged_in:
                        print('Сначала выполните login')
                        continue

                    currency = get_arg(args, '--currency')
                    amount = get_arg(args, '--amount')
                    buy(logged_id, currency, amount)

                case 'sell':
                    if not logged_in:
                        print('Сначала выполните login')
                        continue

                    currency = get_arg(args, '--currency')
                    amount = get_arg(args, '--amount')
                    sell(logged_id, currency, amount)

                case 'get-rate':
                    from_cur = get_arg(args, '--from')
                    to_cur = get_arg(args, '--to')
                    get_rate(from_cur, to_cur)

                case 'update-rates':
                    source = get_arg(args, '--source')
                    update_rates(source)

                case 'show-rates':
                    currency = get_arg(args, '--currency')
                    top = get_arg(args, '--top')
                    base = get_arg(args, '--base')

                    show_rates(currency=currency, top=top, base=base)

                case 'help':
                    print_help()

                case 'exit':
                    print('Выход')
                    break

                case _:
                    print(f"Команда '{command}' не поддерживается")

        except Exception as e:
            print(f'Ошибка: {e}')
