# Portfolio Intelligence v2.6 — Reports Dashboard

Version desktop PySide6 centrée sur le reporting professionnel.

## Nouveautés v2.6

- Génération simultanée du rapport Excel et du rapport PDF.
- Nouveau module `reports/pdf.py` avec synthèse patrimoniale prête à partager.
- Cartes Dashboard dédiées aux rapports : Excel, PDF, statut.
- Bouton `Ouvrir PDF` dans l’interface graphique.
- Export PDF structuré : synthèse, performance, risque, allocations, look-through, stress tests, méthodologie.
- Conservation des modules v2.5 : Analytics, Performance, Risk et Look-through.

## Installation

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -e .
```

Sous Windows, si PySide6 échoue à cause des chemins longs, place le projet dans un chemin court, par exemple :

```text
C:\dev\portfolio_v2_6
```

## Préparer les imports

Place tes fichiers ici :

```text
data/imports/transactions.csv
data/imports/valeur_nette.pdf
```

## Lancer l’interface graphique

```bash
python main.py gui
```

Puis clique sur :

```text
Analyser et générer Excel + PDF
```

Les rapports seront générés ici :

```text
data/exports/rapport_portefeuille.xlsx
data/exports/rapport_portefeuille.pdf
```

## Utilisation CLI

```bash
python main.py analyze
```

Avec chemins personnalisés :

```bash
python main.py analyze \
  --transactions "data/imports/transactions.csv" \
  --net-worth "data/imports/valeur_nette.pdf" \
  --output "data/exports/rapport_portefeuille.xlsx" \
  --pdf-output "data/exports/rapport_portefeuille.pdf"
```

## Limites

Les métriques de performance, risque et look-through restent des estimations. Le PDF est une synthèse de pilotage patrimonial ; l’Excel conserve le détail complet des données.
