# Corporate Default Risk

[![Tests](https://github.com/thefinansist/corporate-default-risk/actions/workflows/tests.yml/badge.svg)](https://github.com/thefinansist/corporate-default-risk/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://www.python.org/)

Инструмент для предварительной оценки риска дефолта юридических лиц по бухгалтерской отчетности РСБУ. Обрабатывает один Excel-файл или портфель компаний, рассчитывает финансовые коэффициенты, присваивает объяснимый индекс риска и формирует отчеты для дальнейшего кредитного анализа.

## Возможности

- автоматическое распознавание стандартных кодов строк РСБУ;
- работа с балансом и отчетом о финансовых результатах на одном или нескольких листах;
- пакетная обработка Excel-файлов из одной директории;
- 11 факторов ликвидности, капитализации, нагрузки, рентабельности и динамики;
- индекс риска от 0 до 100 и классы A–F;
- раскрытие вклада каждого фактора и отдельных риск-сигналов;
- справочный расчет Z″ Альтмана;
- HTML-отчет по компании и CSV-сводка по портфелю;
- настраиваемые веса и пороги без изменения исходного кода.

## Установка

```bash
git clone https://github.com/thefinansist/corporate-default-risk.git
cd corporate-default-risk
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Для Windows активация окружения выполняется командой:

```powershell
.venv\Scripts\activate
```

## Использование

Один файл:

```bash
python run_analysis.py data/input/ВАШ_ФАЙЛ.xlsx --company "Название компании"
```

Портфель компаний:

```bash
python run_analysis.py /path/to/excel_folder --output results/portfolio
```

Для каждой компании создаются:

```text
results/<company>/
├── analysis.json
├── financial_history.csv
├── report.html
└── scorecard.csv
```

Общая таблица сохраняется в `results/portfolio_summary.csv`.

## Входные данные

Поддерживаются `.xlsx` и `.xlsm`. В книге должна присутствовать строка заголовка с полем `Код строки` и колонками отчетных периодов. Баланс и отчет о финансовых результатах могут находиться на разных листах.

Основные используемые строки: `1200`, `1210`, `1240`, `1250`, `1300`, `1370`, `1400`, `1500`, `1520`, `1600`, `1700`, `2110`, `2200`, `2400`.

## Настройка модели

Веса, шкалы факторов и границы классов находятся в [`config/scoring_config.json`](config/scoring_config.json). Методика расчета описана в [`methodology/METHODOLOGY.md`](methodology/METHODOLOGY.md).

## Jupyter

Ноутбук [`notebooks/credit_risk_demo.ipynb`](notebooks/credit_risk_demo.ipynb) содержит последовательность запуска для одиночной компании и пакетного анализа. Перед выполнением укажите локальный путь к Excel-файлу.

## Тесты

```bash
python -m unittest discover -s tests -v
```

## Ограничения

Индекс предназначен для предварительного финансового скрининга и не является статистически откалиброванной вероятностью дефолта. Для использования в качестве PD-модели требуется историческая выборка дефолтов, out-of-time валидация, оценка дискриминирующей способности и стабильности, а также утверждение методики управления модельным риском.

