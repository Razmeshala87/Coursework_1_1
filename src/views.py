from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from src.utils import get_currency_rates, get_greeting, get_stock_prices, load_transactions

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).parent.parent / "data"


def home_page(date_str: str) -> Dict[str, Any]:
    """Генерирует данные для главной страницы."""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        greeting = get_greeting(date)

        with open(Path(__file__).parent.parent / "user_settings.json", encoding="utf-8") as f:
            settings = json.load(f)

        currency_rates = get_currency_rates(settings["user_currencies"])
        stock_prices = get_stock_prices(settings["user_stocks"])
        transactions = load_transactions(DATA_DIR / "operations.xlsx")

        if not isinstance(transactions, pd.DataFrame):
            raise ValueError("Транзакции должны быть в формате DataFrame")

        required_columns = {"Дата операции", "Номер карты", "Сумма операции", "Кэшбэк", "Категория", "Описание"}
        if not required_columns.issubset(transactions.columns):
            missing = required_columns - set(transactions.columns)
            raise ValueError(f"Отсутствуют обязательные колонки: {missing}")

        transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"])
        start_date = pd.to_datetime("2018-01-01")
        end_date = pd.to_datetime("2021-12-31")
        filtered = transactions[
            (transactions["Дата операции"] >= start_date) &
            (transactions["Дата операции"] <= end_date)
            ].copy()

        cards_data = []
        if "Номер карты" in filtered.columns:
            for card in filtered["Номер карты"].dropna().unique():
                card_str = str(card)
                last_digits = card_str[-4:] if len(card_str) > 4 else card_str
                card_trans = filtered[filtered["Номер карты"] == card]
                total_spent = card_trans["Сумма операции"].sum()
                cashback = card_trans["Кэшбэк"].sum()
                cards_data.append(
                    {
                        "last_digits": last_digits,
                        "total_spent": round(float(total_spent), 2),
                        "cashback": round(float(cashback), 2),
                    }
                )

        top_trans_list = []
        if not filtered.empty:
            top_transactions = filtered.nlargest(5, "Сумма операции")
            top_trans_list = [
                {
                    "date": row["Дата операции"].strftime("%d.%m.%Y"),
                    "amount": round(row["Сумма операции"], 2),
                    "category": row["Категория"],
                    "description": row["Описание"],
                }
                for _, row in top_transactions.iterrows()
            ]

            if transactions.empty:
                logger.warning("Нет данных о транзакциях")
                return {
                    "greeting": greeting,
                    "cards": [],
                    "top_transactions": [],
                    "currency_rates": currency_rates,
                    "stock_prices": stock_prices,
                    "warning": "Нет данных о транзакциях"
                }

        return {
            "greeting": greeting,
            "cards": cards_data,
            "top_transactions": top_trans_list,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices,
        }
    except Exception as e:
        logger.error("Ошибка генерации данных главной страницы: %s", str(e))
        raise


def events_page(transactions: pd.DataFrame, date_str: str, date_range: str = "M") -> Dict[str, Any]:
    """Генерирует данные для страницы событий."""
    try:

        if date_range == "ALL":
            start_date = pd.to_datetime("2018-01-01")  # Фиксированная начальная дата
            end_date = pd.to_datetime("2021-12-31")  # Фиксированная конечная дата
        else:
            # Для других режимов используем последний год данных
            start_date = pd.to_datetime("2021-01-01") if date_range == "Y" else \
                pd.to_datetime("2021-12-01") if date_range == "M" else \
                pd.to_datetime("2021-12-25")  # Пример для недели
            end_date = pd.to_datetime("2021-12-31")

        filtered = transactions[
            (transactions["Дата операции"] >= start_date) &
            (transactions["Дата операции"] <= end_date)
            ].copy()

        transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"])
        filtered = transactions[transactions["Дата операции"] >= start_date].copy()

        expenses_data = {
            "total_amount": 0,
            "main": [],
            "transfers_and_cash": [{"category": "Наличные", "amount": 0}, {"category": "Переводы", "amount": 0}],
        }

        if not filtered.empty:
            expenses = filtered[filtered["Сумма операции"] > 0]
            if not expenses.empty:
                expenses_by_category = expenses.groupby("Категория")["Сумма операции"].sum()
                main_expenses = expenses_by_category.nlargest(7).reset_index()
                other_expenses = expenses_by_category.sum() - main_expenses["Сумма операции"].sum()

                expenses_data["total_amount"] = round(float(expenses_by_category.sum()))

                main_categories = [
                    {"category": str(row["Категория"]), "amount": round(float(row["Сумма операции"]))}
                    for _, row in main_expenses.iterrows()
                ]

                if other_expenses > 0:
                    main_categories.append({"category": "Остальное", "amount": round(float(other_expenses))})

                expenses_data["main"] = main_categories

        income_data = {"total_amount": 0, "main": []}
        if not filtered.empty:
            income = filtered[filtered["Сумма операции"] < 0]
            if not income.empty:
                income_by_category = income.groupby("Категория")["Сумма операции"].sum().abs()
                income_data["total_amount"] = round(float(income_by_category.sum()))
                income_data["main"] = [
                    {"category": str(cat), "amount": round(float(amt))} for cat, amt in income_by_category.items()
                ]

        with open(Path(__file__).parent.parent / "user_settings.json", encoding="utf-8") as f:
            settings = json.load(f)

        return {
            "expenses": expenses_data,
            "income": income_data,
            "currency_rates": get_currency_rates(settings["user_currencies"]),
            "stock_prices": get_stock_prices(settings["user_stocks"]),
        }
    except Exception as e:
        logger.error("Ошибка генерации данных страницы событий: %s", str(e))
        raise
