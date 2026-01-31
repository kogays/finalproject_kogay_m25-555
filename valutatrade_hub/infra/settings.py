
import json
from pathlib import Path


class SettingsLoader:
    _instance= None
    class _SettingsMeta(type):
        """Метакласс для реализации Singleton."""
        def __call__(cls, *args, **kwargs):
            if cls._instance is None:
                cls._instance = super().__call__(*args, **kwargs)
            return cls._instance

    def __init__(self):
        # Гарантируем, что инициализация выполняется только один раз
        if not hasattr(self, "_initialized"):
            self._config = {}
            self._config_file = "pyproject.toml"
            self._custom_config_file = None
            self._load_config()
            self._initialized = True

    def _load_config(self) -> None:
        """Загружает конфигурацию из файлов."""
        # Базовые настройки по умолчанию
        default_config = {
            "data_directory": "data",
            "rates_ttl_seconds": 300,  # 5 минут
            "default_base_currency": "USD",
            "log_directory": "logs",
            "log_level": "INFO",
            "log_format": "text",  # или "json"
            "max_log_size_mb": 10,
            "backup_log_files": 5,
            "supported_currencies": ["USD", "EUR", "RUB", "GBP", "JPY", "BTC", "ETH"],
        }

        self._config = default_config

        # Пытаемся загрузить из pyproject.toml
        try:
            import tomllib

            with open(self._config_file, "rb") as f:
                pyproject_data = tomllib.load(f)

            # Извлекаем настройки из секции [tool.valutatrade]
            valuta_config = pyproject_data.get("tool", {}).get("valutatrade", {})
            self._config.update(valuta_config)

        except (FileNotFoundError, ImportError, KeyError):
            # Если файл не найден или нет секции, используем значения по умолчанию
            pass

        # Пытаемся загрузить из custom config.json
        custom_config_path = self._custom_config_file or "config.json"
        if Path(custom_config_path).exists():
            try:
                with open(custom_config_path, "r", encoding="utf-8") as f:
                    custom_config = json.load(f)
                self._config.update(custom_config)
            except (json.JSONDecodeError, Exception):
                # Игнорируем ошибки при загрузке кастомного конфига
                pass

    def get(self, key: str, default = None):
        """Возвращает значение настройки по ключу."""
        return self._config.get(key, default)

    def set(self, key: str, value) -> None:
        """Устанавливает значение настройки."""
        self._config[key] = value

    def reload(self) -> None:
        """Перезагружает конфигурацию из файлов."""
        self._load_config()

    def set_config_file(self, file_path: str) -> None:
        """Устанавливает путь к кастомному файлу конфигурации."""
        self._custom_config_file = file_path
        self.reload()

    @property
    def data_directory(self) -> str:
        return self.get("data_directory", "data")

    @property
    def rates_ttl_seconds(self) -> int:
        return self.get("rates_ttl_seconds", 300)

    @property
    def default_base_currency(self) -> str:
        return self.get("default_base_currency", "USD")

    @property
    def log_directory(self) -> str:
        return self.get("log_directory", "logs")

    @property
    def log_level(self) -> str:
        return self.get("log_level", "INFO")

    @property
    def log_format(self) -> str:
        return self.get("log_format", "text")

    def get_data_file_path(self, filename: str) -> str:
        """Возвращает полный путь к файлу данных."""
        return str(Path(self.data_directory) / filename)


# Создаем глобальный экземпляр настроек
settings = SettingsLoader()