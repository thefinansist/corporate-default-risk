from __future__ import annotations

from html import escape
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PERCENT_KEYS = {
    "equity_ratio", "liabilities_to_assets", "net_margin", "roa", "revenue_growth",
    "payables_to_revenue", "working_capital_to_assets"
}


def _fmt(value: Any, key: str = "") -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    if key in PERCENT_KEYS:
        return f"{float(value):.1%}"
    if key == "profit_deterioration":
        return f"{int(value)} период(а)"
    return f"{float(value):,.2f}".replace(",", " ")


def _money(value: float) -> str:
    if np.isnan(value):
        return "—"
    return f"{value / 1_000_000:,.1f} млн ₽".replace(",", " ")


def write_company_outputs(result: dict[str, Any], output_dir: str | Path) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result["scorecard"].to_csv(output_dir / "scorecard.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(result["history"]).to_csv(output_dir / "financial_history.csv", index=False, encoding="utf-8-sig")

    serializable = {key: value for key, value in result.items() if key != "scorecard"}
    with (output_dir / "analysis.json").open("w", encoding="utf-8") as file:
        json.dump(serializable, file, ensure_ascii=False, indent=2, default=str)
    (output_dir / "report.html").write_text(render_html(result), encoding="utf-8")


def render_html(result: dict[str, Any]) -> str:
    score = result["score"]
    score_color = "#15803d" if score < 35 else "#ca8a04" if score < 50 else "#dc2626" if score < 80 else "#7f1d1d"
    metrics = result["metrics"]
    scorecard = result["scorecard"].copy()
    scorecard["Показательное значение"] = [
        _fmt(row["Значение"], row["indicator"]) for _, row in scorecard.iterrows()
    ]
    scorecard_rows = "".join(
        f"<tr><td>{escape(str(row['Показатель']))}</td><td>{escape(str(row['Показательное значение']))}</td>"
        f"<td>{row['Вес']:.0f}</td><td>{'—' if pd.isna(row['Баллы']) else '{:.1f}'.format(row['Баллы'])}</td>"
        f"<td><span class='status {escape(str(row['Статус']).replace(' ', '_'))}'>{escape(str(row['Статус']))}</span></td></tr>"
        for _, row in scorecard.iterrows()
    )
    flags = result["flags"]
    flag_html = "".join(
        f"<li class='{escape(flag['severity'])}'>{escape(flag['label'])}</li>" for flag in flags
    ) or "<li class='ok'>Стоп-факторы не обнаружены</li>"
    history = result["history"]
    max_revenue = max((abs(x["Выручка"]) for x in history if not np.isnan(x["Выручка"])), default=1)
    trend_rows = "".join(
        f"<tr><td>{x['Период']}</td><td>{_money(x['Выручка'])}</td><td>{_money(x['Чистая прибыль'])}</td>"
        f"<td><div class='bar' style='width:{max(2, abs(x['Выручка'])/max_revenue*100):.0f}%'></div></td></tr>"
        for x in history
    )
    z = metrics.get("altman_z_double_prime", np.nan)
    z_zone = "—" if np.isnan(z) else "благополучная" if z > 2.6 else "серая" if z >= 1.1 else "зона финансового стресса"
    return f"""<!doctype html>
<html lang='ru'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>Оценка риска — {escape(result['company'])}</title>
<style>
body{{margin:0;background:#f4f7fb;color:#172033;font-family:Inter,Arial,sans-serif}}main{{max-width:1180px;margin:0 auto;padding:32px}}
h1{{margin:0 0 6px;font-size:28px}}.sub{{color:#667085;margin-bottom:24px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}
.card{{background:white;border:1px solid #e4e7ec;border-radius:14px;padding:18px;box-shadow:0 2px 10px #1018280d}}.kpi{{font-size:28px;font-weight:750;margin-top:8px}}
.score{{color:{score_color}}}.wide{{grid-column:span 2}}section{{margin-top:18px}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{padding:10px;border-bottom:1px solid #eaecf0;text-align:left}}th{{background:#f8fafc;color:#475467}}
.status{{padding:4px 8px;border-radius:999px;font-size:12px}}.Норма{{background:#dcfce7;color:#166534}}.Внимание{{background:#fef9c3;color:#854d0e}}.Риск{{background:#fee2e2;color:#991b1b}}.Нет_данных{{background:#e5e7eb;color:#374151}}
li{{margin:8px 0}}li.high,li.critical{{color:#b42318;font-weight:650}}li.data{{color:#b54708}}li.ok{{color:#067647}}.bar{{height:8px;border-radius:4px;background:#2563eb}}
.note{{font-size:13px;color:#667085;line-height:1.5}}@media(max-width:800px){{.grid{{grid-template-columns:1fr 1fr}}.wide{{grid-column:span 2}}}}
</style></head><body><main>
<h1>Скрининг риска дефолта: {escape(result['company'])}</h1><div class='sub'>Источник: {escape(Path(result['source_file']).name)} · отчетный период: {result['latest_period']} · модель {escape(result['model_version'])}</div>
<div class='grid'>
<div class='card'><div>Индекс риска</div><div class='kpi score'>{score:.1f} / 100</div></div>
<div class='card'><div>Класс риска</div><div class='kpi'>{escape(result['grade'])}</div><div>{escape(result['risk_level'])}</div></div>
<div class='card'><div>Полнота расчета</div><div class='kpi'>{result['confidence']:.0f}%</div></div>
<div class='card'><div>Z″ Альтмана</div><div class='kpi'>{_fmt(z)}</div><div>{z_zone}</div></div>
<div class='card wide'><div>Выручка</div><div class='kpi'>{_money(metrics['revenue'])}</div><div>Изменение: {_fmt(metrics['revenue_growth'], 'revenue_growth')}</div></div>
<div class='card wide'><div>Чистая прибыль</div><div class='kpi'>{_money(metrics['net_income'])}</div><div>Чистая маржа: {_fmt(metrics['net_margin'], 'net_margin')}</div></div>
</div>
<section class='card'><h2>Рекомендация</h2><p>{escape(result['decision'])}</p><ul>{flag_html}</ul></section>
<section class='card'><h2>Динамика</h2><table><thead><tr><th>Период</th><th>Выручка</th><th>Чистая прибыль</th><th>Масштаб выручки</th></tr></thead><tbody>{trend_rows}</tbody></table></section>
<section class='card'><h2>Факторы скоринга</h2><table><thead><tr><th>Показатель</th><th>Значение</th><th>Вес</th><th>Баллы риска</th><th>Статус</th></tr></thead><tbody>{scorecard_rows}</tbody></table></section>
<section class='card note'><b>Ограничение:</b> индекс является инструментом предварительного скрининга по бухгалтерской отчетности, а не статистически откалиброванной вероятностью дефолта. Решение дополняется проверкой качества отчетности, отрасли, группы связанных лиц, судебных/налоговых событий, платежной дисциплины и актуальности периода. Z″ показан только как справочный внешний ориентир.</section>
</main></body></html>"""
