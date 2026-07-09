from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

try:
    import pdfplumber
except Exception:  # pragma: no cover
    pdfplumber = None

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None


@dataclass(frozen=True)
class NetWorthSummary:
    total_value: float | None
    account_value: float | None
    cash_value: float | None
    raw_text_excerpt: str


def _extract_text(path: Path) -> str:
    if pdfplumber is not None:
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    if PdfReader is not None:
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise RuntimeError("Installe pdfplumber ou pypdf pour lire le PDF.")


def _parse_euro_number(value: str) -> float:
    # Format FR : 4 182,39 ou 4182,39.
    return float(value.replace(" ", "").replace("\u00a0", "").replace(".", "").replace(",", "."))


def _find_amount_after_label(text: str, label: str) -> float | None:
    pattern = rf"{re.escape(label)}\s+([0-9][0-9\s\u00a0\.]*,[0-9]{{2}})"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return _parse_euro_number(match.group(1)) if match else None


def load_net_worth(path: str | Path) -> NetWorthSummary:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF introuvable : {path}")

    text = _extract_text(path)

    # Extraction stricte du TOTAL pour éviter de récupérer le numéro de compte,
    # le code postal ou d'autres identifiants numériques présents dans le PDF.
    total = _find_amount_after_label(text, "TOTAL")
    account = _find_amount_after_label(text, "Compte-Titres")
    cash = _find_amount_after_label(text, "Compte courant") or _find_amount_after_label(text, "Espèces")

    if total is None:
        raise ValueError("Impossible de trouver la ligne TOTAL ... EUR dans le PDF de valeur nette.")

    return NetWorthSummary(total, account, cash, text[:1000])
