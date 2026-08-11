from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Optional

import numpy as np
import pandas as pd

from .metrics import calculate_metrics
from .parser import discover_excel_files, parse_workbook
from .reporting import write_company_outputs
from .scoring import load_config, score_company


def _slug(text: str) -> str:
    value = re.sub(r"[^\w.-]+", "_", text.strip(), flags=re.UNICODE).strip("_")
    return value or "company"


def analyze_path(
    input_path: str | Path,
    output_dir: str | Path,
    config_path: str | Path,
    company_name: Optional[str] = None,
) -> pd.DataFrame:
    config = load_config(config_path)
    output_dir = Path(output_dir)
    files = list(discover_excel_files(input_path))
    if not files:
        raise FileNotFoundError(f"Excel-файлы не найдены: {input_path}")
    portfolio_rows: list[dict[str, Any]] = []

    for file_path in files:
        fs = parse_workbook(file_path, company_name if len(files) == 1 else None)
        metrics = calculate_metrics(fs)
        scored = score_company(metrics, config)
        history = [
            {
                "Период": year,
                "Активы": fs.value("1600", year),
                "Капитал": fs.value("1300", year),
                "Выручка": fs.value("2110", year),
                "Чистая прибыль": fs.value("2400", year),
            }
            for year in fs.periods
        ]
        result = {
            "company": fs.company,
            "source_file": fs.source_file,
            "latest_period": fs.periods[-1],
            "periods": fs.periods,
            "model_version": config["version"],
            "metrics": metrics,
            "history": history,
            "warnings": fs.warnings,
            **scored,
        }
        company_dir = output_dir / _slug(fs.company)
        write_company_outputs(result, company_dir)
        portfolio_rows.append(
            {
                "Компания": fs.company,
                "Файл": file_path.name,
                "Период": fs.periods[-1],
                "Индекс риска": scored["score"],
                "Класс": scored["grade"],
                "Уровень риска": scored["risk_level"],
                "Полнота, %": scored["confidence"],
                "Выручка": metrics["revenue"],
                "Чистая прибыль": metrics["net_income"],
                "Текущая ликвидность": metrics["current_ratio"],
                "Доля капитала": metrics["equity_ratio"],
                "Z-два штриха": metrics["altman_z_double_prime"],
                "Флаги": "; ".join(flag["label"] for flag in scored["flags"]),
                "Рекомендация": scored["decision"],
            }
        )
    portfolio = pd.DataFrame(portfolio_rows).sort_values("Индекс риска", ascending=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    portfolio.to_csv(output_dir / "portfolio_summary.csv", index=False, encoding="utf-8-sig")
    return portfolio

