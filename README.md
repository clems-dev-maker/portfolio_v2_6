# 📊 Portfolio Intelligence v2.6 — Reports Dashboard

Application desktop développée avec **Python** et **PySide6**, dédiée à l'analyse et au reporting de portefeuille.

La version v2.6 est centrée sur la génération de rapports professionnels aux formats **Excel** et **PDF**.

---

## ✨ Nouveautés v2.6

- Génération simultanée du rapport Excel et du rapport PDF
- Nouveau module `reports/pdf.py` dédié à la génération du rapport PDF
- Synthèse patrimoniale prête à partager
- Cartes Dashboard dédiées aux rapports : Excel, PDF et statut
- Bouton `Ouvrir PDF` intégré à l'interface graphique
- Export PDF structuré comprenant :
  - Synthèse
  - Performance
  - Risque
  - Allocations
  - Look-through
  - Stress tests
  - Méthodologie
- Conservation des modules de la version v2.5 :
  - Analytics
  - Performance
  - Risk
  - Look-through

---

## 🛠️ Technologies utilisées

- Python
- PySide6
- Excel
- PDF
- Analyse de portefeuille
- Reporting patrimonial

---

## 📦 Installation

### 1. Créer un environnement virtuel

```bash
python -m venv .venv
2. Activer l'environnement virtuel
Windows
.venv\Scripts\activate
Linux / macOS
source .venv/bin/activate
3. Mettre à jour les outils Python
python -m pip install --upgrade pip setuptools wheel
4. Installer les dépendances
pip install -r requirements.txt
5. Installer le projet en mode développement
pip install -e .
⚠️ Problème potentiel avec PySide6 sous Windows

Si PySide6 échoue à cause des chemins longs, place le projet dans un chemin court.

Exemple :

C:\dev\portfolio_v2_6
📥 Préparer les fichiers d'import

Place les fichiers nécessaires dans le dossier :

data/imports/

Les fichiers attendus sont :

data/imports/transactions.csv
data/imports/valeur_nette.pdf
🖥️ Lancer l'interface graphique

Depuis la racine du projet :

python main.py gui

Dans l'interface graphique, clique ensuite sur :

Analyser et générer Excel + PDF

Les rapports seront générés automatiquement dans :

data/exports/rapport_portefeuille.xlsx
data/exports/rapport_portefeuille.pdf
💻 Utilisation en ligne de commande

Le projet peut également être utilisé depuis la ligne de commande.

Analyse standard
python main.py analyze
Analyse avec chemins personnalisés
python main.py analyze \
  --transactions "data/imports/transactions.csv" \
  --net-worth "data/imports/valeur_nette.pdf" \
  --output "data/exports/rapport_portefeuille.xlsx" \
  --pdf-output "data/exports/rapport_portefeuille.pdf"
📂 Structure du projet
portfolio_v2_6/
│
├── data/
│   ├── imports/
│   │   ├── transactions.csv
│   │   └── valeur_nette.pdf
│   │
│   └── exports/
│       ├── rapport_portefeuille.xlsx
│       └── rapport_portefeuille.pdf
│
├── src/
│   └── portfolio_intelligence/
│       ├── analytics/
│       ├── performance/
│       ├── risk/
│       ├── lookthrough/
│       └── reports/
│           └── pdf.py
│
├── tests/
│
├── main.py
├── pyproject.toml
├── requirements.txt
├── .gitignore
└── README.md
📊 Reporting

La version v2.6 permet de générer deux formats de rapport complémentaires.

📗 Rapport Excel

Le rapport Excel conserve le détail complet des données et des analyses.

Fichier généré :

data/exports/rapport_portefeuille.xlsx
📄 Rapport PDF

Le rapport PDF fournit une synthèse structurée destinée au pilotage patrimonial et au partage.

Il comprend notamment :

Synthèse patrimoniale
Performance
Risque
Allocations
Look-through
Stress tests
Méthodologie

Fichier généré :

data/exports/rapport_portefeuille.pdf
⚠️ Limites

Les métriques de performance, de risque et de look-through restent des estimations.

Le rapport PDF constitue une synthèse de pilotage patrimonial.

Le rapport Excel conserve le détail complet des données.

Les résultats doivent donc être interprétés comme des outils d'analyse et de reporting et non comme des données financières certifiées.

👨‍💻 Auteur

Clément Cathala

GitHub : https://github.com/clems-dev-maker

📄 Licence

Projet distribué sous licence MIT.
