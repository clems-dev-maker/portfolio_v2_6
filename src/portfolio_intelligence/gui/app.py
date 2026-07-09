from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QAction, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QUrl

from portfolio_intelligence.analytics import build_analytics, top_label
from portfolio_intelligence.risk.engine import build_risk, risk_value
from portfolio_intelligence.performance.dashboard import build_performance, perf_value
from portfolio_intelligence.lookthrough import build_lookthrough, lookthrough_value
from portfolio_intelligence.imports.net_worth_pdf import load_net_worth
from portfolio_intelligence.imports.trade_republic import load_transactions, summarize_transactions
from portfolio_intelligence.performance.metrics import build_dashboard_metrics
from portfolio_intelligence.reports.excel import write_report
from portfolio_intelligence.reports.pdf import write_pdf_report
from portfolio_intelligence.utils.paths import DEFAULT_REPORT, DEFAULT_PDF_REPORT, IMPORTS_DIR, autodetect_file, ensure_data_dirs


class KpiCard(QFrame):
    def __init__(self, title: str, value: str = "—") -> None:
        super().__init__()
        self.setObjectName("KpiCard")
        layout = QVBoxLayout(self)
        self.title = QLabel(title)
        self.title.setObjectName("KpiTitle")
        self.value = QLabel(value)
        self.value.setObjectName("KpiValue")
        self.value.setWordWrap(True)
        layout.addWidget(self.title)
        layout.addWidget(self.value)

    def set_value(self, value: str) -> None:
        self.value.setText(value)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        ensure_data_dirs()
        self.setWindowTitle("Portfolio Intelligence v2.6 — Reports Dashboard")
        self.resize(1280, 820)
        self.transactions_path: Path | None = autodetect_file(IMPORTS_DIR, ".csv", ("transaction", "exportation", "trade"))
        self.net_worth_path: Path | None = autodetect_file(IMPORTS_DIR, ".pdf", ("valeur", "net", "patrimoine", "releve"))
        self.report_path = DEFAULT_REPORT
        self.pdf_report_path = DEFAULT_PDF_REPORT
        self._build_ui()
        self._apply_theme()
        self._update_file_labels()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        main = QHBoxLayout(root)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(245)
        side = QVBoxLayout(sidebar)
        title = QLabel("Portfolio\nIntelligence")
        title.setObjectName("AppTitle")
        side.addWidget(title)
        side.addSpacing(16)
        for label, active in [("Dashboard", True), ("Analytics", True), ("Performance", True), ("Risque", True), ("Look-through", True), ("Rapports", True)]:
            btn = QPushButton(label)
            btn.setObjectName("NavButton")
            btn.setEnabled(active)
            side.addWidget(btn)
        side.addStretch()
        self.status_label = QLabel("Prêt")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)
        side.addWidget(self.status_label)
        main.addWidget(sidebar)

        content = QVBoxLayout()
        header = QLabel("Reports Dashboard")
        header.setObjectName("PageTitle")
        content.addWidget(header)

        file_bar = QFrame()
        file_bar.setObjectName("Panel")
        file_layout = QGridLayout(file_bar)
        self.csv_label = QLabel()
        self.pdf_label = QLabel()
        self.csv_label.setWordWrap(True)
        self.pdf_label.setWordWrap(True)
        csv_btn = QPushButton("Importer CSV")
        csv_btn.clicked.connect(self.choose_csv)
        pdf_btn = QPushButton("Importer PDF")
        pdf_btn.clicked.connect(self.choose_pdf)
        run_btn = QPushButton("Analyser et générer Excel + PDF")
        run_btn.setObjectName("PrimaryButton")
        run_btn.clicked.connect(self.analyze)
        open_btn = QPushButton("Ouvrir Excel")
        open_btn.clicked.connect(self.open_report)
        open_pdf_btn = QPushButton("Ouvrir PDF")
        open_pdf_btn.clicked.connect(self.open_pdf_report)
        file_layout.addWidget(QLabel("Transactions"), 0, 0)
        file_layout.addWidget(self.csv_label, 0, 1)
        file_layout.addWidget(csv_btn, 0, 2)
        file_layout.addWidget(QLabel("Valeur nette"), 1, 0)
        file_layout.addWidget(self.pdf_label, 1, 1)
        file_layout.addWidget(pdf_btn, 1, 2)
        file_layout.addWidget(run_btn, 2, 1)
        file_layout.addWidget(open_btn, 2, 2)
        file_layout.addWidget(open_pdf_btn, 3, 2)
        content.addWidget(file_bar)

        kpis = QGridLayout()
        self.card_value = KpiCard("Valeur portefeuille")
        self.card_invested = KpiCard("Capital investi estimé")
        self.card_pnl = KpiCard("Plus-value estimée")
        self.card_tx = KpiCard("Transactions")
        self.card_positions = KpiCard("Positions estimées")
        self.card_period = KpiCard("Période")
        self.card_asset_class = KpiCard("Classe dominante")
        self.card_sector = KpiCard("Secteur dominant")
        self.card_geo = KpiCard("Zone dominante")
        self.card_perf_total = KpiCard("Performance totale estimée")
        self.card_cagr = KpiCard("CAGR estimé")
        self.card_xirr = KpiCard("XIRR estimé")
        self.card_best_month = KpiCard("Meilleur mois estimé")
        self.card_company = KpiCard("Société réelle dominante")
        self.card_theme = KpiCard("Thème réel dominant")
        self.card_hidden = KpiCard("Concentration cachée")
        self.card_vol = KpiCard("Volatilité estimée")
        self.card_var = KpiCard("VaR 95% mensuelle")
        self.card_hhi = KpiCard("Concentration HHI")
        self.card_sharpe = KpiCard("Sharpe estimé")
        self.card_drawdown = KpiCard("Drawdown estimé")
        self.card_top10 = KpiCard("Top 10 positions")
        self.card_excel = KpiCard("Rapport Excel")
        self.card_pdf = KpiCard("Rapport PDF")
        self.card_report_status = KpiCard("Statut rapports")
        for i, card in enumerate([
            self.card_value,
            self.card_invested,
            self.card_pnl,
            self.card_tx,
            self.card_positions,
            self.card_period,
            self.card_asset_class,
            self.card_sector,
            self.card_geo,
            self.card_perf_total,
            self.card_cagr,
            self.card_xirr,
            self.card_best_month,
            self.card_company,
            self.card_theme,
            self.card_hidden,
            self.card_vol,
            self.card_var,
            self.card_hhi,
            self.card_sharpe,
            self.card_drawdown,
            self.card_top10,
            self.card_excel,
            self.card_pdf,
            self.card_report_status,
        ]):
            kpis.addWidget(card, i // 3, i % 3)
        content.addLayout(kpis)

        tables = QHBoxLayout()
        self.class_table = self._make_table("Allocation classes d'actifs")
        self.sector_table = self._make_table("Allocation sectorielle")
        self.geo_table = self._make_table("Allocation géographique")
        tables.addWidget(self.class_table)
        tables.addWidget(self.sector_table)
        tables.addWidget(self.geo_table)
        content.addLayout(tables)

        lt_tables = QHBoxLayout()
        self.company_table = self._make_table("Top sociétés réelles")
        self.lt_sector_table = self._make_table("Secteurs réels")
        self.theme_table = self._make_table("Thèmes réels")
        lt_tables.addWidget(self.company_table)
        lt_tables.addWidget(self.lt_sector_table)
        lt_tables.addWidget(self.theme_table)
        content.addLayout(lt_tables)

        perf_tables = QHBoxLayout()
        self.monthly_perf_table = self._make_table("Performance mensuelle")
        self.annual_perf_table = self._make_table("Performance annuelle")
        self.attribution_table = self._make_table("Attribution")
        perf_tables.addWidget(self.monthly_perf_table)
        perf_tables.addWidget(self.annual_perf_table)
        perf_tables.addWidget(self.attribution_table)
        content.addLayout(perf_tables)

        risk_tables = QHBoxLayout()
        self.risk_table = self._make_table("Contribution risque")
        self.stress_table = self._make_table("Stress tests")
        self.alert_table = self._make_table("Alertes")
        risk_tables.addWidget(self.risk_table)
        risk_tables.addWidget(self.stress_table)
        risk_tables.addWidget(self.alert_table)
        content.addLayout(risk_tables)

        info = QLabel(
            "v2.6 ajoute un Reports Dashboard : génération simultanée Excel + PDF, synthèse professionnelle, KPI, performance, risque, allocations et look-through prêts à partager. "
            "Le PDF reste un rapport de synthèse ; l’Excel conserve le détail complet des données."
        )
        info.setObjectName("InfoText")
        info.setWordWrap(True)
        content.addWidget(info)
        content.addStretch()
        main.addLayout(content)

        menu = self.menuBar().addMenu("Fichier")
        action_analyze = QAction("Analyser", self)
        action_analyze.triggered.connect(self.analyze)
        menu.addAction(action_analyze)

    def _make_table(self, title: str) -> QTableWidget:
        table = QTableWidget(0, 3)
        table.setObjectName("DataTable")
        table.setHorizontalHeaderLabels([title, "Montant", "Poids"])
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        return table

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #0f172a; color: #e5e7eb; font-family: Segoe UI, Arial; }
            #Sidebar { background: #111827; border-right: 1px solid #334155; }
            #AppTitle { font-size: 24px; font-weight: 700; color: #f8fafc; }
            #PageTitle { font-size: 30px; font-weight: 700; color: #f8fafc; margin-bottom: 12px; }
            #Panel, #KpiCard { background: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 12px; }
            #KpiTitle { color: #94a3b8; font-size: 13px; }
            #KpiValue { color: #f8fafc; font-size: 21px; font-weight: 700; }
            QPushButton { background: #334155; color: #f8fafc; border: none; border-radius: 8px; padding: 10px 14px; }
            QPushButton:hover { background: #475569; }
            QPushButton:disabled { color: #64748b; background: #1f2937; }
            #PrimaryButton { background: #2563eb; font-weight: 700; }
            #PrimaryButton:hover { background: #1d4ed8; }
            #NavButton { text-align: left; }
            #StatusLabel, #InfoText { color: #cbd5e1; }
            QMenuBar { background: #0f172a; color: #e5e7eb; }
            QMenu { background: #1e293b; color: #e5e7eb; }
            QTableWidget { background: #111827; alternate-background-color: #172033; color: #e5e7eb; gridline-color: #334155; border: 1px solid #334155; border-radius: 10px; }
            QHeaderView::section { background: #1e293b; color: #f8fafc; padding: 6px; border: 1px solid #334155; }
            """
        )

    def _update_file_labels(self) -> None:
        self.csv_label.setText(str(self.transactions_path) if self.transactions_path else "Aucun CSV détecté")
        self.pdf_label.setText(str(self.net_worth_path) if self.net_worth_path else "Aucun PDF détecté")

    def choose_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choisir le CSV", str(IMPORTS_DIR), "CSV (*.csv)")
        if path:
            self.transactions_path = Path(path)
            self._update_file_labels()

    def choose_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choisir le PDF", str(IMPORTS_DIR), "PDF (*.pdf)")
        if path:
            self.net_worth_path = Path(path)
            self._update_file_labels()

    def _fill_table(self, table: QTableWidget, frame, label_col: str) -> None:
        rows = min(len(frame), 8)
        table.setRowCount(rows)
        for i in range(rows):
            row = frame.iloc[i]
            table.setItem(i, 0, QTableWidgetItem(str(row[label_col])))
            table.setItem(i, 1, QTableWidgetItem(f"{row['amount']:,.2f} €".replace(",", " ")))
            table.setItem(i, 2, QTableWidgetItem(f"{row['weight'] * 100:.1f}%"))
        table.resizeColumnsToContents()

    def _fill_generic_table(self, table: QTableWidget, frame, columns: list[str], formats: list[str]) -> None:
        rows = min(len(frame), 8)
        table.setRowCount(rows)
        table.setHorizontalHeaderLabels(columns)
        for i in range(rows):
            row = frame.iloc[i]
            for j, col in enumerate(columns):
                value = row.get(col, "—") if hasattr(row, "get") else "—"
                fmt = formats[j] if j < len(formats) else "str"
                if isinstance(value, (float, int)):
                    if fmt == "pct":
                        text = f"{value * 100:.1f}%"
                    elif fmt == "eur":
                        text = f"{value:,.0f} €".replace(",", " ")
                    else:
                        text = f"{value:,.2f}".replace(",", " ")
                else:
                    text = str(value)
                table.setItem(i, j, QTableWidgetItem(text))
        table.resizeColumnsToContents()

    def analyze(self) -> None:
        try:
            if self.transactions_path is None:
                raise FileNotFoundError("Aucun fichier CSV sélectionné.")
            if self.net_worth_path is None:
                raise FileNotFoundError("Aucun fichier PDF sélectionné.")
            transactions = load_transactions(self.transactions_path)
            tx_summary = summarize_transactions(transactions)
            net_worth = load_net_worth(self.net_worth_path)
            metrics = build_dashboard_metrics(transactions, tx_summary, net_worth)
            analytics = build_analytics(transactions, net_worth)
            performance = build_performance(transactions, net_worth, metrics)
            lookthrough = build_lookthrough(transactions, net_worth)
            risk = build_risk(transactions, net_worth, metrics)
            report = write_report(self.report_path, transactions, tx_summary, net_worth, metrics)
            pdf_report = write_pdf_report(self.pdf_report_path, transactions, tx_summary, net_worth, metrics)
            self.card_value.set_value(f"{metrics.portfolio_value:,.2f} €".replace(",", " "))
            self.card_invested.set_value(f"{metrics.invested_estimate:,.2f} €".replace(",", " "))
            self.card_pnl.set_value(f"{metrics.pnl_estimate:,.2f} € / {metrics.pnl_percent:.2f}%".replace(",", " "))
            self.card_tx.set_value(str(metrics.transaction_count))
            self.card_positions.set_value(str(metrics.position_count_estimate))
            self.card_period.set_value(f"{metrics.first_date or '—'} → {metrics.last_date or '—'}")
            self.card_asset_class.set_value(top_label(analytics.class_allocation, "Classe d'actifs"))
            self.card_sector.set_value(top_label(analytics.sector_allocation, "Secteur"))
            self.card_geo.set_value(top_label(analytics.geography_allocation, "Zone"))
            self.card_perf_total.set_value(f"{perf_value(performance.summary, 'Performance totale estimée') * 100:.1f}%")
            self.card_cagr.set_value(f"{perf_value(performance.summary, 'CAGR estimé') * 100:.1f}%")
            self.card_xirr.set_value(f"{perf_value(performance.summary, 'XIRR estimé') * 100:.1f}%")
            self.card_best_month.set_value(f"{perf_value(performance.summary, 'Meilleur mois estimé') * 100:.1f}%")
            self.card_company.set_value(lookthrough_value(lookthrough.company_exposure, "Société"))
            self.card_theme.set_value(lookthrough_value(lookthrough.theme_exposure, "Thème"))
            self.card_hidden.set_value(lookthrough_value(lookthrough.hidden_concentration, "Société"))
            self.card_vol.set_value(f"{risk_value(risk.summary, 'Volatilité annualisée estimée') * 100:.1f}%")
            self.card_var.set_value(f"{risk_value(risk.summary, 'VaR 95% mensuelle'):,.0f} €".replace(",", " "))
            self.card_hhi.set_value(f"{risk_value(risk.summary, 'HHI concentration'):,.0f}".replace(",", " "))
            self.card_sharpe.set_value(f"{risk_value(risk.summary, 'Sharpe estimé'):.2f}")
            self.card_drawdown.set_value(f"{risk_value(risk.summary, 'Drawdown maximal estimé') * 100:.1f}%")
            self.card_top10.set_value(f"{risk_value(risk.summary, 'Top 10 positions') * 100:.1f}%")
            self.card_excel.set_value(str(report.name))
            self.card_pdf.set_value(str(pdf_report.name))
            self.card_report_status.set_value("Excel + PDF générés")
            self._fill_table(self.class_table, analytics.class_allocation, "Classe d'actifs")
            self._fill_table(self.sector_table, analytics.sector_allocation, "Secteur")
            self._fill_table(self.geo_table, analytics.geography_allocation, "Zone")
            self._fill_table(self.company_table, lookthrough.company_exposure, "Société")
            self._fill_table(self.lt_sector_table, lookthrough.sector_exposure, "Secteur réel")
            self._fill_table(self.theme_table, lookthrough.theme_exposure, "Thème")
            self._fill_generic_table(self.monthly_perf_table, performance.monthly_returns.tail(8), ["month", "estimated_return", "cumulative_return"], ["str", "pct", "pct"])
            self._fill_generic_table(self.annual_perf_table, performance.annual_returns, ["year", "annual_return", "ending_value"], ["str", "pct", "eur"])
            self._fill_generic_table(self.attribution_table, performance.attribution.head(8), ["name", "net_contribution", "weight"], ["str", "eur", "pct"])
            self._fill_generic_table(self.risk_table, risk.risk_by_position, ["name", "risk_contribution_pct", "risk_volatility"], ["str", "pct", "pct"])
            self._fill_generic_table(self.stress_table, risk.stress_tests, ["Scénario", "Impact %", "Impact €"], ["str", "pct", "eur"])
            self._fill_generic_table(self.alert_table, risk.alerts, ["Niveau", "Alerte", "Valeur"], ["str", "str", "pct"])
            self.status_label.setText(f"Rapports générés : {report} et {pdf_report}")
            QMessageBox.information(self, "Analyse terminée", f"Rapport Excel généré :\n{report}\n\nRapport PDF généré :\n{pdf_report}")
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", str(exc))
            self.status_label.setText(f"Erreur : {exc}")

    def open_report(self) -> None:
        if self.report_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.report_path.resolve())))
        else:
            QMessageBox.warning(self, "Rapport introuvable", "Génère d'abord le rapport Excel.")

    def open_pdf_report(self) -> None:
        if self.pdf_report_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.pdf_report_path.resolve())))
        else:
            QMessageBox.warning(self, "Rapport PDF introuvable", "Génère d'abord le rapport PDF.")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Portfolio Intelligence")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

