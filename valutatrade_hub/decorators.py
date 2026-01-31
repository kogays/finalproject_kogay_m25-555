import functools
from datetime import datetime


def log_action(mode='INFO', verbose=False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                print(f'{mode} {datetime.now()} {func.__name__.upper()} {kwargs} result={e}')
                raise e
            else:
                print(f'{mode} {datetime.now()} {func.__name__.upper()} {kwargs} result=OK')
                return result
        return wrapper
    return decorator