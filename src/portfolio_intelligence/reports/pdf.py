from __future__ import annotations

from pathlib import Path
from datetime import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from portfolio_intelligence.analytics import build_analytics
from portfolio_intelligence.risk.engine import build_risk
from portfolio_intelligence.performance.dashboard import build_performance
from portfolio_intelligence.lookthrough import build_lookthrough


def _fmt(value) -> str:
    if isinstance(value, float):
        if abs(value) <= 1:
            return f"{value * 100:.2f}%"
        return f"{value:,.2f}".replace(",", " ")
    return str(value)


def _table_from_df(df: pd.DataFrame, max_rows: int = 12) -> Table:
    if df is None or df.empty:
        data = [["Information"], ["Aucune donnée disponible"]]
    else:
        view = df.head(max_rows).copy()
        data = [list(view.columns)]
        for _, row in view.iterrows():
            data.append([_fmt(v) for v in row.tolist()])
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def _heading(story, text: str, styles) -> None:
    story.append(Paragraph(text, styles["Heading2"]))
    story.append(Spacer(1, 0.25 * cm))


def write_pdf_report(
    output: str | Path,
    transactions: pd.DataFrame,
    tx_summary,
    net_worth,
    metrics,
) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    analytics = build_analytics(transactions, net_worth)
    performance = build_performance(transactions, net_worth, metrics)
    risk = build_risk(transactions, net_worth, metrics)
    lookthrough = build_lookthrough(transactions, net_worth)

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Muted",
            parent=styles["Normal"],
            textColor=colors.HexColor("#475569"),
            fontSize=9,
            leading=12,
        )
    )

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.2 * cm,
    )
    story = []

    story.append(Paragraph("Portfolio Intelligence v2.6", styles["Title"]))
    story.append(Paragraph("Rapport patrimonial professionnel", styles["Heading2"]))
    story.append(
        Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')} — données Trade Republic importées depuis le CSV et le PDF de valeur nette.",
            styles["Muted"],
        )
    )
    story.append(Spacer(1, 0.6 * cm))

    summary = pd.DataFrame(
        [
            ["Valeur portefeuille", f"{metrics.portfolio_value:,.2f} €".replace(",", " ")],
            ["Capital investi estimé", f"{metrics.invested_estimate:,.2f} €".replace(",", " ")],
            ["Plus-value estimée", f"{metrics.pnl_estimate:,.2f} €".replace(",", " ")],
            ["Performance estimée", f"{metrics.pnl_percent:.2f}%"],
            ["Transactions", metrics.transaction_count],
            ["Positions estimées", metrics.position_count_estimate],
            ["Période", f"{metrics.first_date} → {metrics.last_date}"],
        ],
        columns=["Indicateur", "Valeur"],
    )
    _heading(story, "Synthèse", styles)
    story.append(_table_from_df(summary, max_rows=20))
    story.append(Spacer(1, 0.5 * cm))

    _heading(story, "Performance", styles)
    story.append(_table_from_df(performance.summary, max_rows=14))
    story.append(Spacer(1, 0.5 * cm))

    _heading(story, "Risque", styles)
    story.append(_table_from_df(risk.summary, max_rows=14))
    story.append(Spacer(1, 0.5 * cm))

    _heading(story, "Alertes de risque", styles)
    story.append(_table_from_df(risk.alerts, max_rows=10))
    story.append(PageBreak())

    _heading(story, "Allocation par classe d'actifs", styles)
    story.append(_table_from_df(analytics.class_allocation, max_rows=12))
    story.append(Spacer(1, 0.5 * cm))

    _heading(story, "Allocation sectorielle", styles)
    story.append(_table_from_df(analytics.sector_allocation, max_rows=12))
    story.append(Spacer(1, 0.5 * cm))

    _heading(story, "Allocation géographique", styles)
    story.append(_table_from_df(analytics.geography_allocation, max_rows=12))
    story.append(PageBreak())

    _heading(story, "Look-through : top sociétés consolidées", styles)
    story.append(_table_from_df(lookthrough.company_exposure, max_rows=20))
    story.append(Spacer(1, 0.5 * cm))

    _heading(story, "Concentrations cachées", styles)
    story.append(_table_from_df(lookthrough.hidden_concentration, max_rows=20))
    story.append(PageBreak())

    _heading(story, "Stress tests", styles)
    story.append(_table_from_df(risk.stress_tests, max_rows=12))
    story.append(Spacer(1, 0.5 * cm))

    _heading(story, "Méthodologie", styles)
    story.append(
        Paragraph(
            "Les métriques de risque, performance et look-through sont des estimations destinées au suivi patrimonial. "
            "Elles ne constituent pas un conseil en investissement. Les expositions ETF sont modélisées localement et devront être remplacées par les holdings officiels pour une précision institutionnelle complète.",
            styles["Normal"],
        )
    )

    doc.build(story)
    return output
