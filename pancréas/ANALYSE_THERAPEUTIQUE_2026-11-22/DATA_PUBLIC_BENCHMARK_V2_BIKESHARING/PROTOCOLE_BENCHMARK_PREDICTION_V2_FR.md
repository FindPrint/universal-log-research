# Amendement de benchmark prédictif V2 — Bike Sharing

**Statut :** amendement secondaire, ajouté après l’exécution du benchmark V1. Il ne remplace pas V1 et n’est pas un résultat confirmatoire préenregistré.

## Pourquoi cet amendement

La V1 comparait les modèles à la moyenne globale d’apprentissage. Comme le jeu a des cycles heure/jour, une moyenne globale est un comparateur faible pour une série temporelle. Une moyenne de demande apprise sur les seuls couples `weekday × hr` du bloc d’apprentissage constitue un témoin plus pertinent. Son ajout a été décidé après inspection des métriques V1; ce caractère postérieur est conservé dans le journal et dans la lecture des résultats.

## Plan inchangé

- Cible : `cnt`; mêmes deux tests chronologiques V1 (apprentissage 0–50 %, test 50–75 %; puis apprentissage 0–75 %, test 75–100 %).
- Mêmes douze prédicteurs calendrier et météo observée; `instant`, `casual` et `registered` restent exclus.
- Aucun paramètre d’arbre n’est sélectionné selon les performances de test. Même graine et mêmes réglages que V1.
- Comparateurs : moyenne globale d’apprentissage, moyenne d’apprentissage par `weekday × hr`, Ridge, forêt aléatoire et HistGradientBoosting.
- Métriques : MAE, RMSE, R².

La moyenne `weekday × hr` est estimée uniquement avec la partition d’apprentissage de chaque pli. Aucun résultat cible du bloc test ne contribue à ce modèle de référence.

## Portée

V2 ajoute une comparaison de robustesse plus adaptée à la périodicité observée, mais son amendement après les résultats V1 limite sa valeur confirmatoire. Les deux versions restent publiées. Le benchmark demeure une estimation rétrospective conditionnée à la météo mesurée à l’heure cible, et non une prévision météo à l’avance.
