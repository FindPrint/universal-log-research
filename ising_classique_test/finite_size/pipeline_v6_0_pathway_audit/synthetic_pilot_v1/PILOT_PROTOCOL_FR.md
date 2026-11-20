# Pilote synthétique à vérité connue — v1

**Statut initial : protocole gelé avant exécution.** Il s'agit d'un pilote de fonctionnement de la chaîne complète, pas d'une validation confirmatoire.

## Objectif

Observer comment UNIVERSAL_LOG v6.0 traite des séries synthétiques simples dont la structure est connue, en particulier la position T0, la disponibilité des estimateurs, Q1–Q6, F1/F2, Voie 1/2, TLog, L7a et L7b. Le fichier source du pipeline est appelé sans modification.

## Configuration gelée

- Source : `universal_v6.0.0_cohen.py`; empreinte exacte dans `pilot_spec.json`.
- Mode `fast`, test Cohen-d, un seul worker, contrôle explicite `control_index`, cible fixe `target`, domaine déclaré `generic`, contrôle `single`, L7b `light`.
- Le CSV transmis contient uniquement l'axe, la cible et les flux prévus pour le cas. Aucune étiquette de cas, position d'événement ou vérité terrain n'est transmise comme argument ou colonne.
- La vérité terrain est conservée séparément sous `truth_private/truth.json`. Le lanceur `run` ne lit pas ce fichier; le script de notation ne le lit qu'après les exécutions.
- Sept cas, une exécution déterministe par cas. Les cas 01 et 02 partagent les mêmes 76 observations de cible et d'axe; le cas 02 retire les flux additionnels.

| Cas opaque | N | Structure vraie (dévoilée après exécution) |
|---|---:|---|
| case_01 | 76 | Marche de cible avec flux corrélé, copie affine exacte et bruit indépendant |
| case_02 | 76 | Même cible et axe que case_01; cible seule avec l'axe |
| case_03 | 76 | AR(1) stationnaire, sans changement de régime |
| case_04 | 76 | Dérive linéaire lisse avec bruit, sans rupture discrète |
| case_05 | 7 | Marche; stress de série très courte |
| case_06 | 15 | Marche; stress de série courte |
| case_07 | 30 | Marche; longueur intermédiaire |

## Lecture pré-déclarée

1. Consigner réussite/erreur, temps d'exécution, nombre d'estimateurs et statuts présents, comptages numériques Q1–Q6, seuils F1/F2, sortie TLog et statuts L7a/L7b, sans remplacer les sorties brutes.
2. Pour les cas avec marche, comparer T0 en pourcentage de rang à la frontière vraie, définie au milieu entre la dernière observation avant la marche et la première observation après. Erreur normalisée : `abs(T0_rank_pct / 100 - boundary_rank_fraction)`. Aucune tolérance de réussite n'est imposée après avoir vu les résultats.
3. Pour AR(1) et dérive, consigner si le pipeline renvoie une position T0. Puisqu'aucune règle indépendante d'alerte/abstention n'a été gelée, une position renvoyée n'est **pas** appelée faux positif.
4. Comparer case_01 à case_02 à titre descriptif pour voir si l'ajout de flux change les sorties quand la cible et l'axe restent identiques. Une paire ne mesure ni variabilité ni indépendance.
5. Les valeurs de TLog sont lues avec leurs composantes, statuts et sorties associées; elles ne constituent pas seules le résultat de la théorie ou une preuve.

## Limites

Il n'y a qu'une réalisation par cas et aucune estimation d'intervalle, de taux de détection, de faux positifs ou de puissance. Les longueurs N=7 et N=15 sont des stress d'estimabilité, pas des validations d'estimateurs fractals. Les choix de bruit et les graines ne couvrent pas une population de signaux. Un succès sur ces entrées ne démontre ni universalité mathématique, ni validité clinique ou biologique. Le lot confirmatoire nécessitera critères, graines réservées, réplications et règles d'abstention fixés séparément.

## Reproduction

À la racine du projet, avec le `.venv` :

```powershell
.\.venv\Scripts\python.exe .\ising_classique_test\finite_size\pipeline_v6_0_pathway_audit\synthetic_pilot_v1\run_synthetic_pilot.py prepare
.\.venv\Scripts\python.exe .\ising_classique_test\finite_size\pipeline_v6_0_pathway_audit\synthetic_pilot_v1\run_synthetic_pilot.py run
.\.venv\Scripts\python.exe .\ising_classique_test\finite_size\pipeline_v6_0_pathway_audit\synthetic_pilot_v1\score_synthetic_pilot.py
```

Les journaux et dossiers de sortie propres à chaque cas se trouvent dans `runs/`. `pilot_spec.json` et les empreintes des entrées figent le lot pré-exécution; `pilot_summary.json` conserve les valeurs extraites des sorties maîtres. Toute modification des générateurs, paramètres ou seuils doit créer une nouvelle version du pilote.
