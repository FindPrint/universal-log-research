# Revue de code — UNIVERSAL_LOG v5.9.0f

## Périmètre et provenance

- Fichier examiné : `<PROJECT_ROOT>\universal_x5f_log_x5f_L7a_x5f_L7b_x5f_v5.9.0f_0_n0z8.py`.
- Référence locale : `UNIVERSAL_LOG_v5.8.py` dans le même dossier. Ce fichier v5.8 contient aussi une modification expérimentale antérieure à cette revue : résolution du paysage configurable, défaut conservé à 120.
- Empreintes SHA-256, tailles et commandes : [source_provenance.json](source_provenance.json).
- Diff complet conservé dans [diff_v5_8_to_v5_9.unified.diff](diff_v5_8_to_v5_9.unified.diff).
- La v5.9 compile avec le Python du `.venv`. Aucun des deux fichiers source utilisateur n’a été modifié.
- Le dossier n’est pas un dépôt Git; les comparaisons reposent sur les deux fichiers présents à la date de revue.

## Vérifié dans le code

- Les deux fichiers exposent les mêmes **29 noms d’estimateurs** et la même partition `DIMENSION_FOR_TLOG` (21 sorties dimensionnelles réparties entre quatre classes).
- L’AST de `level_coherence_universal` est identique : le code L7a n’a pas changé dans cette comparaison.
- La v5.9 ajoute L7b en deux modes : `light` (stabilités multi-horizon, dispersion du walk-forward, désaccord sémantique) et `full` (quatre ré-exécutions : autre graine, première partie à 80 %, cible mélangée, logarithme de la cible si positive).
- La v5.9 ne définit plus `D_KIND_REGISTRY` ni `ESTIMATOR_D_KIND`. Elle ne produit plus `T_log_by_d_kind`, ni les exports de taxonomie ni les avertissements de mélange sémantique de la v5.8. La sortie TLog historique par estimateur et classe reste présente. C’est une perte fonctionnelle par rapport au centre TLog/29 estimateurs décrit dans ce dossier.
- Le commentaire de `VERSION` affirme encore `# -> "v5.8.0"`; l’expression donne effectivement `v5.9.0`. C’est une incohérence documentaire, pas un résultat du pipeline.

## Seuils L7b : règles présentes, calibration non établie ici

Le code applique, entre autres, les frontières suivantes : stabilité d’horizon `0.80` et `0.50`; écart-type du seuil walk-forward `10` et `20`; changement de seuil de `5` points pour la graine et `10` pour la fenêtre; signal mélangé à `50 %` et `80 %` de `Delta`; variation de `20` points pour le test log. Ce sont les **seuils d’implémentation** de la v5.9. Je ne les considère pas calibrés ou validés par le test Ising; les verdicts L7b ne seront donc pas interprétés comme une preuve statistique.

## Tests directs des fonctions L7b

Des entrées synthétiques ont été passées à `level_robustness_L7b_from_summaries`. Elles vérifient des cas de données manquantes et de signe, pas une performance prédictive réelle.

| Cas fourni | Sortie observée | Lecture prudente |
|---|---|---|
| Le résumé de ré-exécution existe, mais `T0_pct` est absent | Le check graine est `FAIL` | Une absence de mesure est traitée comme un échec, plutôt que `INDETERMINE`. Même risque pour le check fenêtre. |
| `Delta_ref=None`, `Delta_melange=1`, T0 et statut présents | Le check mélange est `PASS`; verdict global `ROBUSTE` si les autres checks passent | Il affirme une réduction relative sans référence numérique disponible. C’est un cas à corriger avant de s’appuyer sur le verdict. |
| `Delta_ref=-2`, `Delta_melange=-1` (la valeur absolue est divisée par deux) | Le check mélange est `FAIL` | La logique compare des valeurs signées alors que le texte décrit un effondrement relatif. Or `Delta` est construit comme `d_div-d_sat` et peut être négatif. |

Ces trois sorties ont été reproduites par appel direct à la fonction. Elles ne sont pas déduites du texte de commentaire. Un correctif devrait renvoyer `INDETERMINE` lorsque la référence manque et définir explicitement si l’effet de mélange compare une quantité signée ou sa magnitude.

## Essai d’intégration du cœur

Un premier appel complet de `run_pipeline` et `compute_holographic_tension_state` a réussi sur l’entrée archivée `L=16,T=2.0`, avec 29 sorties d’estimateur. La copie de test contient 24 lignes de paysage, comme prévu, mais les métadonnées retournées par v5.9 annoncent encore 120. Les exports de campagne conservent les deux faits (`source_metadata=120`, nombre observé de lignes=24) et marquent cette incohérence; ils ne réécrivent pas silencieusement le résultat source.

L’essai est conservé dans [smoke_result.json](expanded_runs/smoke_test/smoke_result.json), avec le journal console, les caractéristiques et l’empreinte du CSV d’entrée. Ce contrôle valide seulement l’intégration du cœur et ne constitue pas une campagne de robustesse L7b.

## Limites de la vérification

- Compilation syntaxique, appels directs des helpers L7b et un appel complet du cœur `run_pipeline` effectués.
- Pas encore de ré-exécution complète de `run_full_unified_pipeline` avec L7b `light` ou `full`; les fichiers temporaires de `full` restent à vérifier.
- Le test Ising évalue le cœur `run_pipeline`; il ne valide pas l’usage prédictif L7a/L7b sur une cible temporelle.
- Pour l’essai multi-flux ci-joint, une copie de travail de la v5.9 recevra uniquement un réglage expérimental à 24 positions de paysage. Le fichier source v5.9 gardera son défaut de 120; la copie et sa différence seront conservées et identifiées.

## Hypothèse à tester ensuite

La v5.9 conserve-t-elle les sorties numériques du cœur v5.8 sur les mêmes CSV et réglages, en ajoutant seulement la couche L7b, malgré la perte du `d_kind` natif? C’est une hypothèse de non-régression; la comparaison identique des 20 entrées précédentes la testera. L’absence de taxonomie, déjà vérifiée dans le code, ne dépend pas de ce résultat.
