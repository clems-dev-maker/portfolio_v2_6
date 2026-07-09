from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
IMPORTS_DIR = ROOT / "data" / "imports"
EXPORTS_DIR = ROOT / "data" / "exports"
DEFAULT_REPORT = EXPORTS_DIR / "rapport_portefeuille.xlsx"
DEFAULT_PDF_REPORT = EXPORTS_DIR / "rapport_portefeuille.pdf"


def ensure_data_dirs() -> None:
    IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def autodetect_file(directory: Path, suffix: str, keywords: tuple[str, ...]) -> Path | None:
    if not directory.exists():
        return None
    candidates = sorted(directory.glob(f"*{suffix}"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        return None
    for file in candidates:
        lower = file.name.lower()
        if any(k in lower for k in keywords):
            return file
    return candidates[0]
