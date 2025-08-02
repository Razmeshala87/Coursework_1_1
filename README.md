# Анализатор банковских транзакций

Проект предоставляет инструменты для анализа банковских транзакций, включая категоризацию расходов, расчет кэшбэка, генерацию отчетов и визуализацию данных.

## Основные функции

- **Загрузка и обработка данных**: Чтение транзакций из Excel-файлов, валидация и преобразование данных.
- **Анализ расходов**:
  - По категориям (`spending_by_category`).
  - По дням недели (`spending_by_weekday`).
  - По рабочим/выходным дням (`spending_by_workday`).
- **Финансовые сервисы**:
  - Расчет кэшбэка (`profitable_cashback_categories`).
  - Округление транзакций для сбережений (`investment_bank`).
  - Поиск транзакций по описанию, номерам телефонов, переводам физлицам.
- **Отчеты**: Автоматическое сохранение отчетов в JSON с декоратором `@report_to_file`.
- **Визуализация**: Генерация данных для главной страницы (`home_page`) и страницы событий (`events_page`).

## Технологии

- Python 3.9+
- Библиотеки:
  - `pandas` для обработки данных.
  - `pytest` для тестирования.
  - `requests` для работы с API (курсы валют, цены акций).
  - `python-dotenv` для управления переменными окружения.


## 🚀 Запуск проекта

1. **Установка зависимостей**:
   ```bash
   pip install pandas pytest requests python-dotenv

2. **Настройка переменных окружения**:
  - Создайте файл .env на основе .env.example и укажите API-ключи:
  - CURRENCY_API_KEY=ваш_ключ
  - STOCK_API_KEY=ваш_ключ

3. **Запуск основного скрипта**:
  - python src/main.py

## Примеры использования

1. **Анализ категорий**

from src.reports import spending_by_category
df = load_transactions("data/operations.xlsx")
report = spending_by_category(df, "Супермаркеты")

2. **Расчет кэшбэка**

from src.services import profitable_cashback_categories
cashback = profitable_cashback_categories(transactions_list, year=2021, month=12)

## Лицензия

MIT License. Для коммерческого использования обратитесь к автору.