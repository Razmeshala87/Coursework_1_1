from __future__ import annotations

import json
import logging
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

import pandas as pd

T = TypeVar("T")

logger = logging.getLogger(__name__)


def report_to_file(
    filename: Optional[str] = None,
    reports_dir: Optional[Path] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Декоратор для сохранения результатов отчета в файл."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            result = func(*args, **kwargs)

            # Создаем имя файла
            report_name = filename or f"report_{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # Используем переданную директорию или дефолтную
            dir_path = reports_dir or (Path(__file__).parent.parent / "reports")
            dir_path.mkdir(exist_ok=True)

            # Полный путь к файлу
            report_path = dir_path / report_name

            # Сохраняем результат
            try:
                with open(report_path, "w", encoding="utf-8") as f:
                    if isinstance(result, pd.DataFrame):
                        df = result.copy()
                        if "Дата операции" in df.columns:
                            df["Дата операции"] = df["Дата операции"].astype(str)
                        json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
                    else:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                logger.info(f"Отчет сохранен в {report_path}")
            except Exception as e:
                logger.error(f"Ошибка сохранения отчета: {str(e)}")

            return result

        return wrapper

    return decorator


@report_to_file()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    try:
        print(f"\nАнализ категории '{category}':")
        print("Доступные категории:", transactions['Категория'].unique())

        ref_date = pd.to_datetime("2021-12-31")
        start_date = pd.to_datetime("2018-01-01")

        print(f"Период анализа: {start_date} - {ref_date}")

        # Явная конвертация дат
        transactions['Дата операции'] = pd.to_datetime(transactions['Дата операции'])
        filtered = transactions[
            (transactions['Категория'] == category) &
            (transactions['Дата операции'] >= start_date) &
            (transactions['Дата операции'] <= ref_date)
            ]

        print(f"Найдено {len(filtered)} транзакций")

        if filtered.empty:
            return pd.DataFrame(columns=['Дата операции', 'Сумма операции'])

        result = filtered.groupby(
            filtered['Дата операции'].dt.to_period("M")
        )['Сумма операции'].sum().reset_index()

        return result

    except Exception as e:
        logger.error("Ошибка: %s", str(e), exc_info=True)
        raise


@report_to_file()
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    """Рассчитывает средние траты по дням недели за период 2018-2021."""
    try:
        ref_date = pd.to_datetime("2021-12-31")
        start_date = pd.to_datetime("2018-01-01")

        # Пробуем разные форматы дат
        try:
            op_date = pd.to_datetime(transactions["Дата операции"], format="%Y-%m-%d")
        except ValueError:
            op_date = pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S")

        filtered = transactions[
            (transactions["Дата операции"] >= start_date) &
            (transactions["Дата операции"] <= ref_date)
        ].copy()

        filtered.loc[:, "День недели"] = op_date.dt.day_name()
        return filtered.groupby("День недели")["Сумма операции"].mean().reset_index()
    except Exception as e:
        logger.error("Ошибка в spending_by_weekday: %s", str(e))
        raise


@report_to_file("workday_spending_report.json")
def spending_by_workday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    """Рассчитывает средние траты в рабочие и выходные дни за период 2018-2021."""
    try:
        ref_date = pd.to_datetime("2021-12-31")
        start_date = pd.to_datetime("2018-01-01")

        # Пробуем разные форматы дат
        try:
            op_date = pd.to_datetime(transactions["Дата операции"], format="%Y-%m-%d")
        except ValueError:
            op_date = pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S")

        filtered = transactions[
            (transactions["Дата операции"] >= start_date) &
            (transactions["Дата операции"] <= ref_date)
        ].copy()

        filtered.loc[:, "Тип дня"] = op_date.dt.dayofweek.apply(
            lambda x: "Выходной" if x >= 5 else "Рабочий"
        )

        return filtered.groupby("Тип дня")["Сумма операции"].mean().reset_index()
    except Exception as e:
        logger.error("Ошибка в spending_by_workday: %s", str(e))
        raise
