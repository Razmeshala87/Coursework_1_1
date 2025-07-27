import pytest
from unittest.mock import patch, mock_open
import json
from datetime import datetime
import pandas as pd
import logging

# Импортируем тестируемые функции
from src.views import home_page, events_page


@pytest.fixture
def mock_settings():
    return {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "GOOGL"]
    }


@pytest.fixture
def mock_transactions():
    data = {
        "Дата операции": pd.to_datetime(["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04"]),
        "Номер карты": ["1234567890123456", "1234567890123456", "9876543210987654", None],
        "Сумма операции": [1000.50, 2000.75, 3000.25, -500.00],
        "Кэшбэк": [10.05, 20.07, 30.02, 0],
        "Категория": ["Еда", "Транспорт", "Развлечения", "Зарплата"],
        "Описание": ["Супермаркет", "Такси", "Кино", "Зарплата"]
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_empty_transactions():
    return pd.DataFrame(columns=[
        "Дата операции", "Номер карты", "Сумма операции",
        "Кэшбэк", "Категория", "Описание"
    ])


@pytest.fixture
def mock_currency_rates():
    return {"USD": 75.50, "EUR": 85.25}


@pytest.fixture
def mock_stock_prices():
    return {"AAPL": 150.25, "GOOGL": 2750.50}


def test_home_page_success(mock_settings, mock_transactions, mock_currency_rates, mock_stock_prices):
    """Тест успешного выполнения home_page"""
    date_str = "2021-01-01 12:00:00"

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_settings))), \
            patch("src.views.get_currency_rates", return_value=mock_currency_rates), \
            patch("src.views.get_stock_prices", return_value=mock_stock_prices), \
            patch("src.views.load_transactions", return_value=mock_transactions):
        result = home_page(date_str)

        # Проверяем основные ключи в ответе
        assert "greeting" in result
        assert "cards" in result
        assert "top_transactions" in result
        assert "currency_rates" in result
        assert "stock_prices" in result

        # Проверяем данные карт
        assert len(result["cards"]) == 2  # Две уникальные карты
        assert result["cards"][0]["last_digits"] == "3456"
        assert result["cards"][0]["total_spent"] == 3001.25  # 1000.50 + 2000.75

        # Проверяем топ транзакций (все транзакции, включая отрицательные)
        assert len(result["top_transactions"]) == 4
        # Проверяем, что транзакции отсортированы по убыванию суммы
        amounts = [t["amount"] for t in result["top_transactions"]]
        assert amounts == sorted(amounts, reverse=True)

        # Проверяем курсы валют и акций
        assert result["currency_rates"] == mock_currency_rates
        assert result["stock_prices"] == mock_stock_prices


def test_events_page_all_range(mock_settings, mock_transactions, mock_currency_rates, mock_stock_prices):
    """Тест events_page с диапазоном ALL"""
    date_str = "2021-01-01 12:00:00"

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_settings))), \
            patch("src.views.get_currency_rates", return_value=mock_currency_rates), \
            patch("src.views.get_stock_prices", return_value=mock_stock_prices):
        result = events_page(mock_transactions, date_str, "ALL")

        assert "expenses" in result
        assert "income" in result
        assert "currency_rates" in result
        assert "stock_prices" in result

        # Проверяем расходы (сумма всех положительных операций)
        expected_expenses = 1000.50 + 2000.75 + 3000.25
        assert result["expenses"]["total_amount"] == round(expected_expenses)

        # Проверяем доходы (сумма всех отрицательных операций по модулю)
        expected_income = 500.00
        assert result["income"]["total_amount"] == round(expected_income)


# Остальные тесты остаются без изменений


def test_events_page_empty_transactions(mock_settings, mock_empty_transactions, mock_currency_rates, mock_stock_prices):
    """Тест events_page с пустыми транзакциями"""
    date_str = "2021-01-01 12:00:00"

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_settings))), \
            patch("src.views.get_currency_rates", return_value=mock_currency_rates), \
            patch("src.views.get_stock_prices", return_value=mock_stock_prices):
        result = events_page(mock_empty_transactions, date_str)

        assert result["expenses"]["total_amount"] == 0
        assert result["expenses"]["main"] == []
        assert result["income"]["total_amount"] == 0
        assert result["income"]["main"] == []


def test_events_page_invalid_date_range(mock_settings, mock_transactions):
    """Тест events_page с неверным диапазоном дат"""
    date_str = "2021-01-01 12:00:00"

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_settings))), \
            patch("src.views.get_currency_rates", return_value={}), \
            patch("src.views.get_stock_prices", return_value={}):
        result = events_page(mock_transactions, date_str, "INVALID")

        # Проверяем, что данные все равно возвращаются
        assert "expenses" in result
        assert "income" in result


def test_events_page_logging_error(mock_settings, mock_transactions):
    """Тест обработки ошибок в events_page"""
    date_str = "2021-01-01 12:00:00"

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_settings))), \
            patch("src.views.get_currency_rates", side_effect=Exception("Test error")), \
            patch("logging.Logger.error") as mock_logger:
        with pytest.raises(Exception):
            events_page(mock_transactions, date_str)

        # Проверяем, что ошибка была залогирована
        assert mock_logger.called


def test_home_page_logging_error(mock_settings):
    """Тест обработки ошибок в home_page"""
    date_str = "2021-01-01 12:00:00"

    with patch("builtins.open", side_effect=Exception("Test error")), \
            patch("logging.Logger.error") as mock_logger:
        with pytest.raises(Exception):
            home_page(date_str)

        # Проверяем, что ошибка была залогирована
        assert mock_logger.called