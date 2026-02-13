# BTC Scenarios Tracker

Dashboard automatisé d'analyse Bitcoin avec scénarios versionnés, données live, et changelog hebdomadaire.

## Architecture

```
btc-scenarios-tracker/
├── .github/workflows/
│   └── btc-analysis.yml      # GitHub Action (weekly + manual)
├── scripts/
│   ├── generate_analysis.py   # Script d'analyse via Claude API
│   └── requirements.txt
├── data/
│   ├── index.json             # Index de toutes les analyses
│   └── analyses/              # Un JSON par analyse (YYYY-MM-DD.json)
├── docs/
│   ├── index.html             # Dashboard (GitHub Pages)
│   └── data/                  # Copie des données pour Pages
└── README.md
```

## Comment ça marche

1. **Chaque dimanche à 18h UTC**, un GitHub Action se lance automatiquement
2. Le script Python appelle l'**API Claude** (Sonnet) avec **web search** activé
3. Claude recherche les dernières données marché, analyses institutionnelles, signaux on-chain
4. Il produit un **JSON structuré** avec les 3 scénarios, le contexte macro, et un changelog
5. Le JSON est **committé** dans le repo (versioning Git natif)
6. Le dashboard est **déployé** sur GitHub Pages automatiquement

## Setup (5 minutes)

### 1. Créer le repo GitHub

```bash
cd btc-scenarios-tracker
git init
git add .
git commit -m "initial: BTC scenarios tracker setup"
git branch -M main
git remote add origin https://github.com/TON_USERNAME/btc-scenarios-tracker.git
git push -u origin main
```

### 2. Ajouter la clé API Anthropic

1. Va sur https://console.anthropic.com → API Keys → Create Key
2. Sur GitHub : **Settings → Secrets and variables → Actions → New repository secret**
3. Nom : `ANTHROPIC_API_KEY` — Valeur : ta clé `sk-ant-...`

### 3. Activer GitHub Pages

1. **Settings → Pages**
2. Source : **GitHub Actions**
3. C'est tout — le workflow s'en charge

### 4. Lancer la première analyse

1. **Actions → Generate BTC Analysis → Run workflow**
2. Attends ~2 minutes
3. Va sur `https://TON_USERNAME.github.io/btc-scenarios-tracker/`

## Utilisation

### Analyse automatique

Le workflow tourne chaque **dimanche à 18h UTC**. Tu n'as rien à faire.

### Analyse manuelle

**Actions → Generate BTC Analysis → Run workflow → Run workflow**

Utile quand il se passe quelque chose de majeur sur le marché et que tu veux un snapshot immédiat.

### Consulter le dashboard

Va sur `https://TON_USERNAME.github.io/btc-scenarios-tracker/`

- **Vue d'ensemble** : KPIs, graphiques, cartes scénarios
- **Changelog** : diff automatique entre la dernière analyse et la précédente
- **Évolution** : graphiques montrant le prix, F&G, drawdown à travers toutes les analyses
- **Institutionnels** : dernières vues de JPMorgan, Goldman, etc.
- **Historique** : toutes les versions avec navigation

### Exécution locale

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python scripts/generate_analysis.py
```

Puis ouvre `docs/index.html` dans un navigateur.

## Coûts

- **GitHub Actions** : gratuit (2000 min/mois sur repos publics)
- **GitHub Pages** : gratuit
- **API Claude** : ~0.10–0.30$ par analyse (Sonnet + 15 web searches)
- **Total annuel** : ~$5–15 pour des analyses hebdomadaires

## Personnalisation

### Changer la fréquence

Dans `.github/workflows/btc-analysis.yml`, modifie le cron :

```yaml
schedule:
  - cron: '0 18 * * 0'   # Dimanche 18h UTC
  # - cron: '0 18 * * 3' # Mercredi aussi (2x/semaine)
```

### Changer le modèle Claude

Dans `scripts/generate_analysis.py`, ligne `model=` :

```python
model="claude-sonnet-4-20250514"      # Bon rapport qualité/prix (défaut)
model="claude-opus-4-20250514"        # Plus approfondi, ~3x le coût
model="claude-haiku-4-5-20251001"     # Plus rapide, ~5x moins cher
```
