from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd

from src.reports import spending_by_category, spending_by_weekday, spending_by_workday
from src.services import investment_bank, profitable_cashback_categories
from src.utils import load_transactions
from src.views import events_page, home_page

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


def main() -> None:
    """Основная функция для демонстрации всех функциональностей."""
    try:
        # =============================================
        # БЛОК 1: ЗАГРУЗКА И ПРОВЕРКА ДАННЫХ
        # =============================================
        transactions_file = DATA_DIR / "operations.xlsx"
        print(f"\n=== ЗАГРУЗКА ДАННЫХ ===")
        print(f"Путь к файлу: {transactions_file}")
        print(f"Файл существует: {transactions_file.exists()}")

        transactions = load_transactions(transactions_file)

        if transactions.empty:
            logger.error("Файл операций пуст или не содержит корректных данных")
            return

        print("\n=== ИНФОРМАЦИЯ О ДАННЫХ ===")
        print(f"Всего транзакций: {len(transactions)}")
        print("\nПервые 3 строки:")
        print(transactions[['Дата операции', 'Категория', 'Сумма операции']].head(3))

        # =============================================
        # БЛОК 2: ПРЕОБРАЗОВАНИЕ ДАННЫХ (ИСПРАВЛЕНО)
        # =============================================
        print("\n=== ПРЕОБРАЗОВАНИЕ ДАННЫХ ===")
        transactions_list: List[Dict[str, Any]] = []
        error_count = 0

        for idx, row in transactions.iterrows():
            try:
                # Преобразуем дату (уже в правильном формате из load_transactions)
                op_date = pd.to_datetime(row['Дата операции'])

                transactions_list.append({
                    "Дата операции": op_date.strftime("%Y-%m-%d"),
                    "Категория": str(row.get('Категория', 'Не указана')),
                    "Кэшбэк": float(row.get('Кэшбэк', 0)),
                    "Сумма операции": float(row['Сумма операции']),
                    "Описание": str(row.get('Описание', '')),
                    "Номер карты": str(row.get('Номер карты', '')),
                })
            except Exception as e:
                error_count += 1
                logger.warning(f"Ошибка в строке {idx}: {str(e)}")
                continue

        print(f"\nУспешно обработано: {len(transactions_list)}/{len(transactions)}")
        print(f"Ошибок обработки: {error_count}")

        if not transactions_list:
            logger.error("Нет корректных данных для анализа")
            return

        # =============================================
        # БЛОК 3: ОСНОВНОЙ АНАЛИЗ
        # =============================================
        start_date = pd.to_datetime("01.01.2018", dayfirst=True)  # Начальная дата
        end_date = pd.to_datetime("31.12.2021", dayfirst=True)  # Конечная дата

        # Пример вызова одной функции для проверки
        test_category = "Супермаркеты"
        if test_category in transactions['Категория'].unique():
            print(f"\nТестируем отчет для категории: '{test_category}'")
            test_report = spending_by_category(transactions, test_category)
            print("\nРезультат теста:")
            print(test_report)
        else:
            print(f"\nКатегория '{test_category}' не найдена!")
            print("Доступные категории:", transactions['Категория'].unique()[:5])

        # =============================================
        # БЛОК 4: ОСНОВНОЙ АНАЛИЗ (ОСТАЛОСЬ БЕЗ ИЗМЕНЕНИЙ)
        # =============================================
        print("\n=== ОСНОВНОЙ АНАЛИЗ ===")
        current_date = datetime.now()
        date_str = current_date.strftime("%Y-%m-%d %H:%M:%S")
        date_only_str = current_date.strftime("%Y-%m-%d")

        home_data = home_page(date_str)
        print("\nHome Page Data:")
        print(json.dumps(home_data, indent=2, ensure_ascii=False))

        events_data = events_page(transactions, date_only_str)
        print("\nEvents Page Data:")
        print(json.dumps(events_data, indent=2, ensure_ascii=False))

        cashback = profitable_cashback_categories(transactions_list, 2021, 12)
        print("\nProfitable Cashback Categories:")
        print(json.dumps(cashback, indent=2, ensure_ascii=False))

        savings = investment_bank("2021-12", transactions_list, 50)
        print(f"\nInvestment Savings: {savings:.2f}")

        category_spending = spending_by_category(transactions, test_category)
        print("\nSpending by Category:")
        print(category_spending)

        weekday_spending = spending_by_weekday(transactions)
        print("\nSpending by Weekday:")
        print(weekday_spending)

        workday_spending = spending_by_workday(transactions)
        print("\nSpending by Workday/Weekend:")
        print(workday_spending)


    except Exception as e:

        logger.error("Ошибка в main: %s", str(e), exc_info=True)

if __name__ == "__main__":
        main()
