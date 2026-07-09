from __future__ import annotations

import argparse
from pathlib import Path

from portfolio_intelligence.imports.net_worth_pdf import load_net_worth
from portfolio_intelligence.imports.trade_republic import load_transactions, summarize_transactions
from portfolio_intelligence.performance.metrics import build_dashboard_metrics
from portfolio_intelligence.reports.excel import write_report
from portfolio_intelligence.reports.pdf import write_pdf_report
from portfolio_intelligence.utils.paths import DEFAULT_REPORT, DEFAULT_PDF_REPORT, EXPORTS_DIR, IMPORTS_DIR, autodetect_file, ensure_data_dirs


def _resolve_inputs(transactions: str | None, net_worth: str | None) -> tuple[Path, Path]:
    ensure_data_dirs()
    tx_path = Path(transactions) if transactions else autodetect_file(IMPORTS_DIR, ".csv", ("transaction", "exportation", "trade"))
    nw_path = Path(net_worth) if net_worth else autodetect_file(IMPORTS_DIR, ".pdf", ("valeur", "net", "patrimoine", "releve"))
    if tx_path is None:
        raise FileNotFoundError("Aucun fichier CSV trouvé dans data/imports.")
    if nw_path is None:
        raise FileNotFoundError("Aucun fichier PDF trouvé dans data/imports.")
    return tx_path, nw_path


def analyze_command(args: argparse.Namespace) -> int:
    tx_path, nw_path = _resolve_inputs(args.transactions, args.net_worth)
    output = Path(args.output) if args.output else DEFAULT_REPORT
    output.parent.mkdir(parents=True, exist_ok=True)
    transactions = load_transactions(tx_path)
    tx_summary = summarize_transactions(transactions)
    net_worth = load_net_worth(nw_path)
    metrics = build_dashboard_metrics(transactions, tx_summary, net_worth)
    report = write_report(output, transactions, tx_summary, net_worth, metrics)
    pdf_output = Path(args.pdf_output) if getattr(args, "pdf_output", None) else DEFAULT_PDF_REPORT
    pdf_report = write_pdf_report(pdf_output, transactions, tx_summary, net_worth, metrics)
    print(f"Rapport Excel généré : {report.resolve()}")
    print(f"Rapport PDF généré : {pdf_report.resolve()}")
    print(f"Valeur détectée : {metrics.portfolio_value:,.2f} EUR".replace(",", " "))
    return 0


def gui_command(args: argparse.Namespace) -> int:
    from portfolio_intelligence.gui.app import main as gui_main
    return gui_main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="portfolio-intelligence")
    sub = parser.add_subparsers(dest="command")

    analyze = sub.add_parser("analyze", help="Importe les fichiers et génère un rapport Excel.")
    analyze.add_argument("--transactions", default=None, help="Chemin du CSV de transactions.")
    analyze.add_argument("--net-worth", default=None, help="Chemin du PDF de valeur nette.")
    analyze.add_argument("--output", default=str(DEFAULT_REPORT), help="Chemin du rapport Excel de sortie.")
    analyze.add_argument("--pdf-output", default=str(DEFAULT_PDF_REPORT), help="Chemin du rapport PDF de sortie.")
    analyze.set_defaults(func=analyze_command)

    gui = sub.add_parser("gui", help="Lance le Dashboard Desktop PySide6.")
    gui.set_defaults(func=gui_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return int(args.func(args))
