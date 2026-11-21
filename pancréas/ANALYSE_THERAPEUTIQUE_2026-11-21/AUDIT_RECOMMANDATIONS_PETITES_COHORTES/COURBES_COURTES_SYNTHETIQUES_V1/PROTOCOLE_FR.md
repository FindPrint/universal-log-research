# Banc synthétique de courbes dose-réponse courtes — v1.1

**Statut :** pilote descriptif pré-déclaré, exécuté hors du pipeline complet. Le plan v1 initial a été interrompu avant la production de sorties; voir `ATTEMPT_LOG.md`. La présente version réduit le coût en ne sondant les estimateurs qu'une fois par longueur/scénario.  
**Date :** 21 novembre 2026.  
**Pipeline évalué :** UNIVERSAL_LOG v6.0.0, source inchangée, empreinte enregistrée dans les sorties.

## Question

Que deviennent les 29 estimateurs du pipeline lorsqu'on leur transmet uniquement la série d'activité mesurée le long d'une courbe dose-réponse de 7 à 10 concentrations? Une courbe logistique à quatre paramètres peut-elle retrouver son IC50 génératrice dans ces mêmes conditions?

Ce pilote ne modifie pas le seuil de longueur du pipeline et ne calcule ni T0 ni TLog. La fonction `apply_complexity` est appelée directement avec `min_len=N` afin de caractériser les estimateurs sur les petits vecteurs. C'est une sonde interne des estimateurs, pas un run complet cible/contrôle.

## Plan gelé

- Longueurs : `N = 7, 8, 9, 10` doses logarithmiques entre `10^-9` et `10^-4` M.
- 50 réalisations Monte-Carlo déterministes par scénario et longueur, graines issues de `20261121`, pour évaluer l'ajustement Hill conventionnel.
- Scénarios : sigmoïde forte (viabilité 100→20 %, pente de Hill 1,5, bruit SD 3 points); sigmoïde faible (100→70 %, pente 0,8, bruit SD 10 points); absence d'effet (moyenne 100 %, bruit SD 5); réponse sans tendance (moyenne 50 %, bruit SD 20).
- Chaque réalisation contient une seule observation par dose. Les doses ne sont pas rééchantillonnées comme des unités échangeables et aucun bootstrap n'est effectué.
- Référence conventionnelle : ajustement exploratoire d'une courbe Hill 4 paramètres avec `scipy.optimize.curve_fit`; paramètres bornés et statut d'ajustement/covariance conservés. Pour les cas nuls, aucune IC50 vraie n'est définie.
- Pour chaque combinaison longueur/scénario, la première série de la séquence RNG est transmise une fois à la fonction réelle `apply_complexity`, avec `estimator_profile='all'` et seuil local abaissé à N. Ainsi, 16 vecteurs au total sondent les 29 estimateurs. Les étiquettes génératrices et les doses ne sont pas utilisées par cette fonction.

## Mesures pré-déclarées

1. Pour chacun des 16 sondages : état fini/non fini et valeur de chaque estimateur. Un sondage par combinaison ne permet pas d'estimer la stabilité ou une distribution d'incertitude.
2. Pour les deux groupes sigmoïdes : erreur absolue `|log10(IC50 ajustée) − log10(IC50 vraie)|`, succès de convergence, covariance finie et IC50 ajustée dans la plage de doses observée.
3. Pour les groupes nuls : proportion d'ajustements convergés et d'IC50 ajustées dans la plage, sans appeler ces fréquences des faux positifs de T0.
4. Temps total, empreintes de fichiers, versions Python/scientifiques et sorties par réalisation.

## Limites et règle d'interprétation

- Les 50 répétitions simulées quantifient la variabilité de l'ajustement conventionnel sous ce générateur; elles ne sont pas des réplicats expérimentaux et ne prouvent pas la performance biologique.
- Les courbes sont monotones par construction dans les scénarios sigmoïdes. Les données manquantes, effets non monotones, réplications par puits, effets de plaque et hétérogénéité entre modèles ne sont pas testés ici.
- Un estimateur fini n'est pas, à lui seul, un estimateur exact, identifiable ou adapté à une courbe pharmacologique.
- Puisque le seuil du run complet demeure 50 points, `T0`, les six questions, F1/F2, voies 1/2, L7a/L7b et la formule TLog ne sont pas évalués ici. On ne complète pas artificiellement les courbes par interpolation.
- Les résultats ne calibrent pas un seuil « 95 % » et ne justifient pas un mode court confirmé. Toute modification du pipeline demanderait un protocole confirmatoire indépendant, notamment des données groupées par expérience et par modèle.

## Reproduction

Depuis la racine du projet, avec le `.venv` :

```powershell
.\.venv\Scripts\python.exe .\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-21\AUDIT_RECOMMANDATIONS_PETITES_COHORTES\COURBES_COURTES_SYNTHETIQUES_V1\run_short_curve_pilot.py
```

Le script écrit les courbes synthétiques, les résultats Hill pour chaque courbe, les 464 sorties d'estimateurs des 16 sondages, les résumés CSV/JSON et un manifeste SHA-256 dans `outputs/`.
