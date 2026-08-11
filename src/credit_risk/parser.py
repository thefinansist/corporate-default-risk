from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, Iterable, Optional

import numpy as np
import pandas as pd


YEAR_RE = re.compile(r"(?:19|20)\d{2}")
CODE_RE = re.compile(r"(?<!\d)(\d{4})(?!\d)")


@dataclass
class FinancialStatements:
    company: str
    source_file: str
    periods: list[int]
    values: Dict[str, Dict[int, float]]
    source_rows: Dict[str, str]
    warnings: list[str]

    def value(self, code: str, period: Optional[int] = None) -> float:
        if period is None:
            period = self.periods[-1]
        return float(self.values.get(str(code), {}).get(int(period), np.nan))


def _extract_year(value: object) -> Optional[int]:
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp,)):
        return int(value.year)
    if isinstance(value, (int, np.integer)) and 1900 <= int(value) <= 2100:
        return int(value)
    if isinstance(value, float) and value.is_integer() and 1900 <= int(value) <= 2100:
        return int(value)
    match = YEAR_RE.search(str(value))
    return int(match.group(0)) if match else None


def _extract_code(value: object) -> Optional[str]:
    if pd.isna(value):
        return None
    if isinstance(value, (int, np.integer)) and 1000 <= int(value) <= 9999:
        return str(int(value))
    if isinstance(value, float) and value.is_integer() and 1000 <= int(value) <= 9999:
        return str(int(value))
    match = CODE_RE.search(str(value).strip())
    return match.group(1) if match else None


def _to_number(value: object) -> float:
    if pd.isna(value) or value == "":
        return np.nan
    if isinstance(value, (int, float, np.number)):
        return float(value)
    text = str(value).strip().replace("\u00a0", "").replace(" ", "")
    text = text.replace("(", "-").replace(")", "")
    if text in {"-", "—", "–"}:
        return 0.0
    if text.count(",") == 1 and text.count(".") == 0:
        left, right = text.split(",")
        text = left + ("." + right if len(right) <= 2 else right)
    else:
        text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return np.nan


def _find_header(raw: pd.DataFrame) -> tuple[int, int, dict[int, int]]:
    best: Optional[tuple[int, int, dict[int, int], int]] = None
    for row_idx in range(min(len(raw), 80)):
        row = raw.iloc[row_idx]
        code_candidates = [
            col_idx
            for col_idx, value in enumerate(row)
            if "код" in str(value).lower() and "стр" in str(value).lower()
        ]
        period_cols = {
            col_idx: year
            for col_idx, value in enumerate(row)
            if (year := _extract_year(value)) is not None
        }
        if code_candidates and period_cols:
            candidate = (row_idx, code_candidates[0], period_cols, len(period_cols))
            if best is None or candidate[3] > best[3]:
                best = candidate
    if best is None:
        raise ValueError("Не найдена строка заголовка с 'Код строки' и периодами")
    return best[0], best[1], best[2]


def _parse_sheet(raw: pd.DataFrame, sheet_name: str) -> tuple[dict, dict, list[int]]:
    header_row, code_col, period_cols = _find_header(raw)
    values: dict[str, dict[int, float]] = {}
    source_rows: dict[str, str] = {}
    label_col = max(0, code_col - 1)

    for row_idx in range(header_row + 1, len(raw)):
        code = _extract_code(raw.iat[row_idx, code_col])
        if code is None:
            continue
        label = str(raw.iat[row_idx, label_col]).strip()
        values.setdefault(code, {})
        source_rows[code] = f"{sheet_name}: {label}"
        for col_idx, year in period_cols.items():
            number = _to_number(raw.iat[row_idx, col_idx])
            if not np.isnan(number):
                values[code][year] = number
    if not values:
        raise ValueError("В листе не найдены строки отчетности с четырехзначными кодами")
    return values, source_rows, sorted(set(period_cols.values()))


def parse_workbook(path: str | Path, company_name: Optional[str] = None) -> FinancialStatements:
    path = Path(path)
    workbook = pd.ExcelFile(path, engine="openpyxl")
    merged_values: dict[str, dict[int, float]] = {}
    sources: dict[str, str] = {}
    warnings: list[str] = []
    periods: set[int] = set()

    for sheet_name in workbook.sheet_names:
        raw = pd.read_excel(workbook, sheet_name=sheet_name, header=None, dtype=object)
        try:
            values, source_rows, sheet_periods = _parse_sheet(raw, sheet_name)
        except ValueError as exc:
            warnings.append(f"Лист '{sheet_name}' пропущен: {exc}")
            continue
        for code, by_period in values.items():
            merged_values.setdefault(code, {}).update(by_period)
        sources.update(source_rows)
        periods.update(sheet_periods)

    if not merged_values:
        raise ValueError(f"В файле {path.name} не найдена распознаваемая бухгалтерская отчетность")
    usable_periods = sorted(
        period for period in periods if any(period in by_period for by_period in merged_values.values())
    )
    if len(usable_periods) < 2:
        warnings.append("Доступен только один период: динамические показатели не рассчитаны")
    return FinancialStatements(
        company=company_name or path.stem,
        source_file=str(path.resolve()),
        periods=usable_periods,
        values=merged_values,
        source_rows=sources,
        warnings=warnings,
    )


def discover_excel_files(path: str | Path) -> Iterable[Path]:
    path = Path(path)
    if path.is_file():
        yield path
        return
    for pattern in ("*.xlsx", "*.xlsm"):
        yield from sorted(p for p in path.glob(pattern) if not p.name.startswith("~$"))

