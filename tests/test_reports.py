import logging
from datetime import datetime
from pathlib import Path
from typing import Dict
from unittest.mock import patch

import pandas as pd
import pytest

from src.reports import (
    report_to_file,
    spending_by_category,
    spending_by_weekday,
    spending_by_workday,
)


# Фикстуры для тестовых данных
@pytest.fixture
def sample_transactions() -> pd.DataFrame:
    data = {
        'Дата операции': pd.to_datetime(
            ['2021-01-01', '2021-01-15', '2021-02-01', '2021-05-30', '2020-12-31']
        ),
        'Категория': ['Еда', 'Транспорт', 'Еда', 'Развлечения', 'Еда'],
        'Сумма операции': [1000, 500, 1500, 2000, 800]
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_datetime_now(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockDatetime:
        @classmethod
        def now(cls) -> datetime:
            return datetime(2023, 1, 1, 12, 0, 0)

        @classmethod
        def strftime(cls, format: str) -> str:
            return "20230101_120000"

    monkeypatch.setattr('datetime.datetime', MockDatetime)


# Тесты для декоратора report_to_file
def test_report_to_file_decorator(tmp_path: Path, mock_datetime_now: None) -> None:
    @report_to_file("test_report.json", reports_dir=tmp_path)
    def test_func() -> Dict[str, str]:
        return {"key": "value"}

    result = test_func()
    assert result == {"key": "value"}

    expected_file = tmp_path / "test_report.json"
    assert expected_file.exists()


def test_report_to_file_with_dataframe(
    tmp_path: Path, sample_transactions: pd.DataFrame, mock_datetime_now: None
) -> None:
    @report_to_file(reports_dir=tmp_path)
    def test_func() -> pd.DataFrame:
        return sample_transactions

    _ = test_func()
    expected_file = tmp_path / f"report_test_func_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    assert expected_file.exists()


def test_report_to_file_error_handling(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR)
    with patch('builtins.open', side_effect=Exception("Test error")):
        @report_to_file()
        def test_func() -> Dict[str, str]:
            return {"key": "value"}

        test_func()
        assert any("Ошибка сохранения отчета" in record.message for record in caplog.records)


# Тесты для spending_by_category
def test_spending_by_category(sample_transactions: pd.DataFrame) -> None:
    result = spending_by_category(sample_transactions, "Еда")

    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert "Дата операции" in result.columns
    assert "Сумма операции" in result.columns
    assert all(
        str(period).startswith(('2020-12', '2021-01', '2021-02'))
        for period in result['Дата операции']
    )


def test_spending_by_category_empty_result(sample_transactions: pd.DataFrame) -> None:
    result = spending_by_category(sample_transactions, "Несуществующая категория")
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_spending_by_category_error_handling(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR)
    with pytest.raises(Exception):
        spending_by_category("invalid_data", "Еда")
    assert any("Ошибка" in record.message for record in caplog.records)


# Тесты для spending_by_weekday
def test_spending_by_weekday(sample_transactions: pd.DataFrame) -> None:
    result = spending_by_weekday(sample_transactions)

    assert isinstance(result, pd.DataFrame)
    assert "День недели" in result.columns
    assert "Сумма операции" in result.columns
    assert len(result) > 0


def test_spending_by_weekday_with_different_date_formats() -> None:
    transactions = pd.DataFrame({
        'Дата операции': [
            '01.01.2021 12:00:00',
            '02.01.2021 00:00:00',
            '15.01.2021 00:00:00'
        ],
        'Сумма операции': [100, 200, 300]
    })
    transactions['Дата операции'] = pd.to_datetime(
        transactions['Дата операции'],
        format='%d.%m.%Y %H:%M:%S'
    )
    result = spending_by_weekday(transactions)
    assert isinstance(result, pd.DataFrame)
    assert not result.empty


def test_spending_by_weekday_error_handling(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR)
    with pytest.raises(Exception):
        spending_by_weekday("invalid_data")
    assert any("Ошибка в spending_by_weekday" in record.message for record in caplog.records)


# Тесты для spending_by_workday
def test_spending_by_workday(sample_transactions: pd.DataFrame) -> None:
    result = spending_by_workday(sample_transactions)

    assert isinstance(result, pd.DataFrame)
    assert "Тип дня" in result.columns
    assert "Сумма операции" in result.columns
    assert len(result) == 2  # Рабочий и Выходной


def test_spending_by_workday_with_custom_filename(
    tmp_path: Path, sample_transactions: pd.DataFrame, mock_datetime_now: None
) -> None:
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    report_file = reports_dir / "workday_spending_report.json"
    if report_file.exists():
        report_file.unlink()

    spending_by_workday(sample_transactions)
    assert report_file.exists()


def test_spending_by_workday_error_handling(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR)
    with pytest.raises(Exception):
        spending_by_workday("invalid_data")
    assert any("Ошибка в spending_by_workday" in record.message for record in caplog.records)
