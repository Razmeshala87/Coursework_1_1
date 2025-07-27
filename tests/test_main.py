import os
import sys
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pytest

# Настройка sys.path перед импортом локального модуля
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import main


@pytest.fixture
def mock_transactions_data() -> pd.DataFrame:
    return pd.DataFrame({
        'Дата операции': ['2021-12-01', '2021-12-02', '2021-12-03'],
        'Категория': ['Супермаркеты', 'Рестораны', 'Транспорт'],
        'Сумма операции': [1000, 2000, 500],
        'Кэшбэк': [50, 100, 10],
        'Описание': ['Покупка', 'Ужин', 'Такси'],
        'Номер карты': ['1234', '5678', '9012']
    })


@pytest.fixture
def mock_empty_transactions() -> pd.DataFrame:
    return pd.DataFrame()


def test_main_executes_without_errors(mock_transactions_data: pd.DataFrame, tmp_path: Path) -> None:
    """Проверяем, что основная функция выполняется без ошибок"""
    test_file = tmp_path / "operations.xlsx"
    mock_transactions_data.to_excel(test_file, index=False)

    with patch('src.main.DATA_DIR', tmp_path):
        main()


def test_main_handles_empty_file(mock_empty_transactions: pd.DataFrame, tmp_path: Path) -> None:
    """Проверяем обработку пустого файла"""
    test_file = tmp_path / "operations.xlsx"
    mock_empty_transactions.to_excel(test_file, index=False)

    with patch('src.main.DATA_DIR', tmp_path):
        main()


def test_main_handles_missing_file() -> None:
    """Проверяем обработку отсутствующего файла"""
    with patch('src.main.DATA_DIR', Path("/nonexistent/path")):
        main()


def test_main_handles_invalid_data(mock_transactions_data: pd.DataFrame, tmp_path: Path) -> None:
    """Проверяем обработку некорректных данных"""
    bad_row = pd.DataFrame({
        'Дата операции': ['invalid_date'],
        'Категория': [None],
        'Сумма операции': ['not_a_number'],
        'Кэшбэк': [None],
        'Описание': [None],
        'Номер карты': [None]
    })
    test_data = pd.concat([mock_transactions_data, bad_row])

    test_file = tmp_path / "operations.xlsx"
    test_data.to_excel(test_file, index=False)

    with patch('src.main.DATA_DIR', tmp_path):
        main()


def test_main_handles_missing_category(mock_transactions_data: pd.DataFrame, tmp_path: Path) -> None:
    """Проверяем обработку отсутствующей категории"""
    test_data = mock_transactions_data[mock_transactions_data['Категория'] != 'Супермаркеты']
    test_file = tmp_path / "operations.xlsx"
    test_data.to_excel(test_file, index=False)

    with patch('src.main.DATA_DIR', tmp_path):
        main()


def test_main_performs_analysis(mock_transactions_data: pd.DataFrame, tmp_path: Path) -> None:
    """Проверяем выполнение анализа"""
    test_file = tmp_path / "operations.xlsx"
    mock_transactions_data.to_excel(test_file, index=False)

    with patch('src.main.DATA_DIR', tmp_path):
        main()


def test_main_handles_exceptions() -> None:
    """Проверяем обработку исключений"""
    with patch('src.main.load_transactions', side_effect=Exception("Test error")):
        main()
