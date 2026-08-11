from __future__ import annotations

import math
import numpy as np

from .parser import FinancialStatements


def safe_div(numerator: float, denominator: float) -> float:
    if np.isnan(numerator) or np.isnan(denominator) or abs(denominator) < 1e-12:
        return np.nan
    return float(numerator / denominator)


def calculate_metrics(fs: FinancialStatements) -> dict[str, float]:
    latest = fs.periods[-1]
    previous = fs.periods[-2] if len(fs.periods) >= 2 else None
    current_assets = fs.value("1200", latest)
    inventory = fs.value("1210", latest)
    cash = fs.value("1250", latest)
    short_investments = fs.value("1240", latest)
    current_liabilities = fs.value("1500", latest)
    total_assets = fs.value("1600", latest)
    equity = fs.value("1300", latest)
    long_liabilities = fs.value("1400", latest)
    total_liabilities = long_liabilities + current_liabilities
    revenue = fs.value("2110", latest)
    net_income = fs.value("2400", latest)
    operating_profit = fs.value("2200", latest)
    retained_earnings = fs.value("1370", latest)
    payables = fs.value("1520", latest)

    prev_assets = fs.value("1600", previous) if previous else np.nan
    avg_assets = np.nanmean([total_assets, prev_assets]) if previous else total_assets
    prev_revenue = fs.value("2110", previous) if previous else np.nan

    profit_series = [fs.value("2400", year) for year in fs.periods]
    deterioration = 0
    for older, newer in zip(reversed(profit_series[:-1]), reversed(profit_series[1:])):
        if np.isnan(older) or np.isnan(newer) or newer >= older:
            break
        deterioration += 1

    metrics = {
        "current_ratio": safe_div(current_assets, current_liabilities),
        "quick_ratio": safe_div(current_assets - inventory, current_liabilities),
        "cash_ratio": safe_div(cash + short_investments, current_liabilities),
        "equity_ratio": safe_div(equity, total_assets),
        "liabilities_to_assets": safe_div(total_liabilities, total_assets),
        "net_margin": safe_div(net_income, revenue),
        "roa": safe_div(net_income, avg_assets),
        "revenue_growth": safe_div(revenue - prev_revenue, abs(prev_revenue)),
        "payables_to_revenue": safe_div(payables, revenue),
        "working_capital_to_assets": safe_div(current_assets - current_liabilities, total_assets),
        "profit_deterioration": float(deterioration),
        "revenue": revenue,
        "net_income": net_income,
        "operating_profit": operating_profit,
        "total_assets": total_assets,
        "equity": equity,
        "total_liabilities": total_liabilities,
        "payables": payables,
        "working_capital": current_assets - current_liabilities,
        "balance_difference": total_assets - fs.value("1700", latest),
    }
    x1 = safe_div(current_assets - current_liabilities, total_assets)
    x2 = safe_div(retained_earnings, total_assets)
    x3 = safe_div(operating_profit, total_assets)
    x4 = safe_div(equity, total_liabilities)
    components = [x1, x2, x3, x4]
    metrics["altman_z_double_prime"] = (
        6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4
        if all(not math.isnan(x) for x in components)
        else np.nan
    )
    return metrics

