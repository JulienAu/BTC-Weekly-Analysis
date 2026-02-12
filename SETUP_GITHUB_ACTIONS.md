# Setup GitHub Actions pour l'analyse BTC versionnée

## 1) Ajouter le secret OpenAI
1. Ouvre ton repo GitHub.
2. `Settings` → `Secrets and variables` → `Actions`.
3. Clique `New repository secret`.
4. Nom: `OPENAI_API_KEY`.
5. Valeur: ta clé OpenAI (`sk-...`).

## 2) Lancer une analyse manuelle
1. Ouvre l'onglet `Actions`.
2. Choisis `Update BTC analysis`.
3. Clique `Run workflow`.
4. Remplis si besoin:
   - `analysis_tag`
   - `analysis_context`
   - `openai_model`
5. Lance le workflow.

Le workflow met à jour `data/analysis-history.json` puis commit/push automatiquement.

## 3) Vérifier dans le dashboard
- Le dashboard lit directement `data/analysis-history.json`.
- Utilise le bouton `🔄 Charger la dernière analyse versionnée` pour recharger l'historique.
- Utilise le sélecteur de version pour comparer les analyses passées.

## 4) Dépannage rapide
- Erreur `OPENAI_API_KEY is missing`: vérifie le secret dans GitHub.
- Erreur format JSON: le script valide le JSON; relancer le workflow avec un autre contexte.
- Aucun commit: possible qu'aucune différence n'ait été générée.
