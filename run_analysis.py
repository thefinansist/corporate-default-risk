from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from credit_risk import analyze_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Скрининг риска дефолта юридических лиц по отчетности РСБУ")
    parser.add_argument("input", help="Excel-файл или папка с Excel-файлами")
    parser.add_argument("--output", default=str(PROJECT_DIR / "results"), help="Папка результатов")
    parser.add_argument("--config", default=str(PROJECT_DIR / "config" / "scoring_config.json"))
    parser.add_argument("--company", default=None, help="Название компании для одиночного файла")
    args = parser.parse_args()

    portfolio = analyze_path(args.input, args.output, args.config, args.company)
    print("\nАнализ завершен:\n")
    print(portfolio[["Компания", "Период", "Индекс риска", "Класс", "Уровень риска", "Полнота, %"]].to_string(index=False))
    print(f"\nРезультаты: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()

