# Audit d’entrée — Tiriac et al., 2018

## Source

Les tables pharmacologiques proviennent des Tables S4A (chimiothérapies) et S4B (agents ciblés) de [Tiriac et al., *Organoid profiling identifies common responders to chemotherapy in pancreatic cancer*](https://doi.org/10.1158/2159-8290.CD-18-0349). Le classeur de cohorte S1A-D est conservé pour vérifier les identifiants et la disponibilité des essais.

Les fichiers téléchargés, leurs URL et leurs SHA-256 sont inscrits dans `PIPELINE_INPUT_MANIFEST.json`. Les conditions de réutilisation des fichiers sources restent celles de leurs détenteurs; la licence du projet ne leur est pas appliquée par ce paquet.

## Contrôle de provenance et préparation

- Table S4A : 66 PDO et 5 colonnes AUC de chimiothérapie.
- Table S4B : 66 PDO et 21 colonnes AUC d’agents ciblés.
- Les noms de PDO ont été appariés exactement après retrait des espaces en début/fin; l’entrée `hF74 ` de S4B correspond à `hF74` dans S4A.
- Le classeur de cohorte confirme que `hT83` a l’essai chimiothérapie mais pas l’essai ciblé, tandis que `hT96` a l’essai ciblé mais pas l’essai chimiothérapie. Ils sont exclus du croisement sans imputation.
- 65 identifiants sont appariés avant contrôle des valeurs manquantes. Cinq PDO ayant au moins une AUC manquante (`hF81`, `hM19D`, `hT127`, `hT133`, `hT44`) sont exclus afin de conserver le même ensemble pour tous les contrôles.
- Le CSV final contient 60 PDO complets et 26 profils AUC (5 chimiothérapies, 21 agents ciblés), sans valeur manquante. L’ordre S4A est préservé; aucun axe temporel n’est fabriqué.
- La colonne catégorielle `Insensitive` est laissée de côté : elle n’est pas une mesure AUC et le seuil/codage correspondant n’est pas défini par la clé de table utilisée.

## Reproduction

Depuis la racine du projet :

```powershell
.venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-19\prepare_Tiriac2018_pipeline_data.py
```

Le script s’arrête si les identifiants, l’unicité, la complétude finale ou le minimum de 50 observations ne sont pas respectés. Aucun résultat du pipeline n’est contenu dans cet audit d’entrée.

## Limite d’usage de l’axe

Il s’agit d’une cohorte transversale d’organoïdes. Le pipeline prend chaque colonne AUC choisie comme contrôle/axe de progression selon sa configuration; cela ne crée pas un temps biologique. Un `T0` de ce fichier ne devra pas être nommé « transition tumorale » ou « seuil thérapeutique » sans validation indépendante adaptée.
