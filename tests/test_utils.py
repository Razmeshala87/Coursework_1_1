from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.utils import CurrencyRate, StockPrice, get_currency_rates, get_greeting, get_stock_prices, load_transactions

# Тестовые данные
TEST_EXCEL_DATA: Dict[str, List[Any]] = {
    "Дата операции": ["01.01.2023 12:00:00", "02.01.2023 13:00:00"],
    "Категория": ["Еда", "Транспорт"],
    "Сумма операции": [1000, 2000],
    "Кэшбэк": [10, 20],
    "Описание": ["Продукты", "Такси"]
}


@pytest.fixture
def mock_excel_file(tmp_path: Path) -> Path:
    file_path = tmp_path / "test_transactions.xlsx"
    df = pd.DataFrame(TEST_EXCEL_DATA)
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def mock_env() -> Generator[None, None, None]:
    with patch.dict('os.environ', {
        'CURRENCY_API_KEY': 'test_currency_key',
        'STOCK_API_KEY': 'test_stock_key',
        'TESTING': 'False'
    }):
        yield


def test_load_transactions_success(mock_excel_file: Path) -> None:
    """Тест успешной загрузки транзакций"""
    df = load_transactions(mock_excel_file)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == list(TEST_EXCEL_DATA.keys())
    assert df['Дата операции'].iloc[0] == '2023-01-01'


def test_load_transactions_file_not_found() -> None:
    """Тест загрузки с несуществующим файлом"""
    with pytest.raises(FileNotFoundError):
        load_transactions("nonexistent_file.xlsx")


def test_load_transactions_missing_columns(tmp_path: Path) -> None:
    """Тест загрузки с отсутствующими колонками"""
    file_path = tmp_path / "bad_data.xlsx"
    bad_data: Dict[str, List[Any]] = {"Дата операции": ["01.01.2023"], "Сумма операции": [1000]}
    pd.DataFrame(bad_data).to_excel(file_path, index=False)

    with pytest.raises(ValueError, match="Отсутствуют колонки"):
        load_transactions(file_path)


def test_get_greeting() -> None:
    """Тест получения приветствия"""
    assert get_greeting(datetime(2023, 1, 1, 6)) == "Доброе утро"
    assert get_greeting(datetime(2023, 1, 1, 12)) == "Добрый день"
    assert get_greeting(datetime(2023, 1, 1, 18)) == "Добрый вечер"
    assert get_greeting(datetime(2023, 1, 1, 3)) == "Доброй ночи"


def test_get_currency_rates_success(mock_env: None) -> None:
    """Тест получения курсов валют (успешный)"""
    test_rates: Dict[str, float] = {"USD": 1.0, "EUR": 0.9, "RUB": 75.5}

    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": test_rates}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        rates: List[CurrencyRate] = get_currency_rates(["USD", "EUR", "RUB"])

        assert len(rates) == 3
        assert isinstance(rates[0], dict)
        assert rates[0]["currency"] == "USD"
        assert rates[0]["rate"] == 1.0


def test_get_currency_rates_test_mode() -> None:
    """Тест получения курсов валют в тестовом режиме"""
    with patch.dict('os.environ', {'TESTING': 'True'}):
        rates: List[CurrencyRate] = get_currency_rates(["USD", "EUR"])
        assert rates == [{"currency": "USD", "rate": 1.0},
                         {"currency": "EUR", "rate": 1.0}]


def test_get_currency_rates_api_error(mock_env: None) -> None:
    """Тест ошибки API для курсов валют"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        with pytest.raises(requests.exceptions.RequestException):
            get_currency_rates(["USD"])


def test_get_stock_prices_success(mock_env: None) -> None:
    """Тест получения цен акций (успешный)"""
    test_data: Dict[str, Dict[str, str]] = {
        "Global Quote": {
            "05. price": "150.25"
        }
    }

    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = test_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        prices: List[StockPrice] = get_stock_prices(["AAPL"])

        assert len(prices) == 1
        assert isinstance(prices[0], dict)
        assert prices[0]["stock"] == "AAPL"
        assert prices[0]["price"] == 150.25


def test_get_stock_prices_test_mode() -> None:
    """Тест получения цен акций в тестовом режиме"""
    with patch.dict('os.environ', {'TESTING': 'True'}):
        prices: List[StockPrice] = get_stock_prices(["AAPL", "GOOGL"])
        assert prices == [
            {"stock": "AAPL", "price": 100.0},
            {"stock": "GOOGL", "price": 100.0}
        ]


def test_get_stock_prices_api_error(mock_env: None) -> None:
    """Тест ошибки API для цен акций"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        with pytest.raises(requests.exceptions.RequestException):
            get_stock_prices(["AAPL"])


def test_get_stock_prices_missing_key() -> None:
    """Тест отсутствия API ключа для акций"""
    with patch.dict('os.environ', {'STOCK_API_KEY': ''}):
        with pytest.raises(ValueError, match="Не задан API ключ"):
            get_stock_prices(["AAPL"])


def test_get_currency_rates_missing_key() -> None:
    """Тест отсутствия API ключа для валют"""
    with patch.dict('os.environ', {'CURRENCY_API_KEY': ''}):
        with pytest.raises(ValueError, match="Не задан API ключ"):
            get_currency_rates(["USD"])
