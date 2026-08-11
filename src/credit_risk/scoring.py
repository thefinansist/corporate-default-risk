from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def _risk_factor(value: float, direction: str, bands: list[list[float]]) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return np.nan
    if direction == "higher_better":
        for threshold, factor in bands:
            if value >= threshold:
                return float(factor)
    elif direction == "lower_better":
        for threshold, factor in bands:
            if value <= threshold:
                return float(factor)
    raise ValueError(f"Некорректные пороги или direction={direction}")


def score_company(metrics: dict[str, float], config: dict[str, Any]) -> dict[str, Any]:
    rows = []
    total_points = 0.0
    available_weight = 0.0
    total_weight = sum(float(rule["weight"]) for rule in config["indicators"].values())

    for key, rule in config["indicators"].items():
        value = metrics.get(key, np.nan)
        factor = _risk_factor(value, rule["direction"], rule["bands"])
        if np.isnan(factor):
            points = np.nan
            status = "Нет данных"
        else:
            points = float(rule["weight"]) * factor
            total_points += points
            available_weight += float(rule["weight"])
            status = "Норма" if factor <= 0.25 else "Внимание" if factor <= 0.60 else "Риск"
        rows.append(
            {
                "indicator": key,
                "Показатель": rule["label"],
                "Значение": value,
                "Вес": float(rule["weight"]),
                "Фактор риска": factor,
                "Баллы": points,
                "Статус": status,
                "Формула": rule["explanation"],
            }
        )

    score = min(100.0, 100.0 * total_points / available_weight) if available_weight else np.nan
    grade_rule = next(item for item in config["grade_bands"] if score <= item["max_score"])
    confidence = 100.0 * available_weight / total_weight if total_weight else 0.0

    flags = []
    flag_defs = config["flags"]
    if metrics.get("equity", np.nan) < 0:
        flags.append({"code": "negative_equity", **flag_defs["negative_equity"]})
    if metrics.get("net_income", np.nan) < 0:
        flags.append({"code": "negative_net_income", **flag_defs["negative_net_income"]})
    if metrics.get("current_ratio", np.nan) < 0.8:
        flags.append({"code": "current_ratio_below_0_8", **flag_defs["current_ratio_below_0_8"]})
    if metrics.get("revenue_growth", np.nan) < -0.30:
        flags.append({"code": "revenue_drop_over_30pct", **flag_defs["revenue_drop_over_30pct"]})
    if metrics.get("payables_to_revenue", np.nan) > 1.0:
        flags.append({"code": "payables_above_revenue", **flag_defs["payables_above_revenue"]})
    assets = metrics.get("total_assets", np.nan)
    balance_diff = metrics.get("balance_difference", np.nan)
    if not np.isnan(assets) and not np.isnan(balance_diff) and abs(balance_diff) > max(1.0, abs(assets) * 0.001):
        flags.append({"code": "balance_not_tied", **flag_defs["balance_not_tied"]})

    return {
        "score": round(score, 1),
        "grade": grade_rule["grade"],
        "risk_level": grade_rule["risk_level"],
        "decision": grade_rule["decision"],
        "confidence": round(confidence, 1),
        "flags": flags,
        "scorecard": pd.DataFrame(rows),
    }

