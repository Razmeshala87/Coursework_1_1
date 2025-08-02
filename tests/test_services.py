from typing import Generator
from unittest.mock import Mock, patch

import pytest

from src.services import (investment_bank, person_transfers_search, phone_number_search,
                          profitable_cashback_categories, simple_search)

# Тестовые данные
TEST_TRANSACTIONS = [
    {
        "Дата операции": "2021-01-15",
        "Категория": "Супермаркеты",
        "Сумма операции": 1000.50,
        "Кэшбэк": 50.25,
        "Описание": "Покупка в Пятерочке"
    },
    {
        "Дата операции": "2021-01-20",
        "Категория": "Рестораны",
        "Сумма операции": 2000.75,
        "Кэшбэк": 100.50,
        "Описание": "Ужин в ресторане"
    },
    {
        "Дата операции": "2021-02-10",
        "Категория": "Супермаркеты",
        "Сумма операции": 1500.00,
        "Кэшбэк": 75.00,
        "Описание": "Покупка в Магните"
    },
    {
        "Дата операции": "2021-01-05",
        "Категория": "Переводы",
        "Сумма операции": 5000.00,
        "Описание": "Перевод Иванову А.А. +7 999 123-45-67"
    },
    {
        "Дата операции": "2021-01-25",
        "Категория": "Транспорт",
        "Сумма операции": 500.00,
        "Описание": "Такси домой"
    },
    {
        "Дата операции": "2021-01-30",
        "Категория": "Переводы",
        "Сумма операции": 3000.00,
        "Описание": "Перевод Петрову С.И."
    }
]


@pytest.fixture
def mock_logger() -> Generator[Mock, None, None]:
    with patch("src.services.logger") as mock:
        yield mock


def test_profitable_cashback_categories_success() -> None:
    """Тест успешного расчета кэшбэка по категориям"""
    result = profitable_cashback_categories(TEST_TRANSACTIONS, 2021, 1)

    assert isinstance(result, dict)
    assert len(result) == 2
    assert result["Супермаркеты"] == 50.25
    assert result["Рестораны"] == 100.50


def test_profitable_cashback_categories_invalid_year(mock_logger: Mock) -> None:
    """Тест обработки неверного года"""
    result = profitable_cashback_categories(TEST_TRANSACTIONS, 2022, 1)
    assert result == profitable_cashback_categories(TEST_TRANSACTIONS, 2021, 1)
    mock_logger.warning.assert_called_once()


def test_profitable_cashback_categories_invalid_month() -> None:
    """Тест обработки неверного месяца"""
    result = profitable_cashback_categories(TEST_TRANSACTIONS, 2021, 13)

    assert result == profitable_cashback_categories(TEST_TRANSACTIONS, 2021, 12)


def test_profitable_cashback_categories_invalid_transaction(mock_logger: Mock) -> None:
    """Тест обработки некорректных транзакций"""
    bad_transactions = TEST_TRANSACTIONS + [{"invalid": "data"}]
    result = profitable_cashback_categories(bad_transactions, 2021, 1)
    assert len(result) == 2
    mock_logger.warning.assert_called()


def test_investment_bank_success() -> None:
    """Тест успешного расчета сбережений"""
    result = investment_bank("2021-01", TEST_TRANSACTIONS, 100)
    assert isinstance(result, float)
    assert result == 198.75


def test_investment_bank_invalid_month() -> None:
    """Тест обработки неверного формата месяца"""
    with pytest.raises(ValueError):
        investment_bank("2021-13", TEST_TRANSACTIONS, 100)


def test_investment_bank_invalid_limit() -> None:
    """Тест обработки неверного лимита"""
    with pytest.raises(ValueError):
        investment_bank("2021-01", TEST_TRANSACTIONS, -100)


def test_investment_bank_no_transactions() -> None:
    """Тест обработки отсутствия транзакций"""
    result = investment_bank("2021-03", TEST_TRANSACTIONS, 100)
    assert result == 0.0


def test_simple_search_success() -> None:
    """Тест успешного поиска транзакций"""
    result = simple_search("Пятерочке", TEST_TRANSACTIONS)

    assert len(result) == 1
    assert result[0]["Категория"] == "Супермаркеты"


def test_simple_search_case_insensitive() -> None:
    """Тест поиска без учета регистра"""
    result = simple_search("пятерочке", TEST_TRANSACTIONS)
    assert len(result) == 1


def test_simple_search_case_sensitive() -> None:
    """Тест поиска с учетом регистра"""
    result = simple_search("пятерочке", TEST_TRANSACTIONS, case_sensitive=True)
    assert len(result) == 0


def test_simple_search_empty_query() -> None:
    """Тест поиска с пустым запросом"""
    result = simple_search("", TEST_TRANSACTIONS)
    assert len(result) == 0


def test_phone_number_search_success() -> None:
    """Тест поиска транзакций с номерами телефонов"""
    result = phone_number_search(TEST_TRANSACTIONS)

    assert len(result) == 1
    assert "+7 999 123-45-67" in result[0]["Описание"]


def test_phone_number_search_custom_pattern() -> None:
    """Тест поиска с пользовательским шаблоном"""
    custom_pattern = r"Петрову"
    result = phone_number_search(TEST_TRANSACTIONS, custom_pattern)
    assert len(result) == 1


def test_person_transfers_search_success() -> None:
    """Тест поиска переводов физлицам"""
    result = person_transfers_search(TEST_TRANSACTIONS)

    assert len(result) == 2
    assert all(t["Категория"] == "Переводы" for t in result)


def test_person_transfers_search_custom_pattern() -> None:
    """Тест поиска с пользовательским шаблоном имени"""
    custom_pattern = r"Иванову"
    result = person_transfers_search(TEST_TRANSACTIONS, custom_pattern)
    assert len(result) == 1
    assert "Иванову" in result[0]["Описание"]


def test_person_transfers_search_no_matches() -> None:
    """Тест поиска без совпадений"""
    result = person_transfers_search(TEST_TRANSACTIONS, "Неттакогоимени")
    assert len(result) == 0
