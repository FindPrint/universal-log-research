# Revue de l'avis de l'autre IA — 15 novembre 2026

Le texte examiné est l'avis joint par l'utilisateur (`Texte collé.txt`), archivé byte-pour-byte dans `REFERENCES/avis_autre_IA_texte_brut.txt`, empreinte SHA-256 `0fca2b84f147811721c6ee2daf3496f606ae7ea64c9a5ab7ed4859a67095dc0e`. Il est traité comme une analyse à vérifier, pas comme une instruction de modification du code.

## Évaluation des affirmations

| Affirmation de l'avis | État après vérification | Motif / lecture retenue |
|---|---|---|
| T0=2,27 aux grandes tailles et dans le test L64 à deux colonnes. | **Résultat confirmé, portée limitée.** | Les sorties L=32, 48 et 64 donnent T0=2,27; l'addendum L64 avec Temperature + Energy donne aussi 2,27. La grille va par pas de 0,01. L'addendum est post hoc et exécuté une fois. |
| Le test à deux colonnes « prouve que le pipeline ne triche pas » avec χ/Cv/Binder. | **Conclusion non démontrée.** | Le retrait de ces colonnes élimine une voie d'accès directe à ces flux dans cette exécution. Il ne constitue ni une réplication aveugle préenregistrée ni un test indépendant : énergie et température gardent le signal, et le run a été sélectionné après examen des principaux résultats. |
| L7b est FRAGILE pour six tailles sur sept. | **Résultat confirmé pour L7b-light de cette campagne.** | Les six statuts fragiles sont observés; le mode utilisé est `light`, qui évalue stabilité d'horizon, variabilité walk-forward de T0 et cohérence interne. Il ne teste pas les reruns de graine, fenêtre, mélange et échelle réservés à `full`. |
| L7b devient FRAGILE parce que Levina–Bickel manque. | **Lien causal non soutenu; la dépendance n'existe pas dans le code L7b-light.** | Le code de `level_robustness_L7b_light` ne lit pas la valeur Levina–Bickel. Dans L=24, horizon min=0,75 et `t0_std=19,031` échouent aux règles light; la cohérence passe. À L=32/48/64, la stabilité d'horizon passe, mais le contrôle walk-forward échoue. À L=8, la cohérence interne échoue aussi; L=12 passe les trois vérifications. |
| Levina–Bickel absent à cause de l'embedding ou de k face aux 76 points; c'est probablement un bug. | **L'absence est reproduite; le diagnostic ne confirme pas un bug général.** | Pour L=8–64, les appels standalone sur les 76 énergies sont finis (environ 1,81–1,89), alors que le paysage local contient 0/120 valeurs finies à toutes les tailles. Le profil `fast` est bien `estimator_profile=all`. La reconstitution du chemin de fenêtres donne, à chaque taille, 20/120 entrées sous le garde-fou de 40 points; les 100 autres passent ce garde-fou, mais toutes ont moins de 12 dimensions locales valides (maximum 8), seuil de retour du code. Cela relie l'absence au support local de cette configuration. Une décision sur une fenêtre plus large ou une estimation globale modifierait la définition analysée; elle doit être évaluée séparément, avec ses effets sur T0 et la couverture, avant tout changement du pipeline. |
| Un banc synthétique devrait couvrir marches, sigmoïdes, dynamique AR(1), oscillations, nuls, redondance et séries courtes. | **Bonne proposition, à opérationnaliser.** | Les scénarios sont repris dans `PROTOCOLE_BANC_ESSAI_SYNTHETIQUE_V1.md`, avec vérité terrain cachée au pipeline, séparation pilote/confirmation, seeds réservées et métriques déclarées avant exécution. Une bifurcation ou un processus AR(1) n'est pas une preuve de criticité universelle; l'événement à détecter doit être défini par son générateur. |
| Tester N=7 à 15 points pour préparer le scRNA-seq. | **Utile comme stress test de calculabilité.** | Sur peu de points, le premier objectif est le statut d'estimabilité, la traçabilité et l'abstention. Pour des données cellulaires, le nombre de cellules ne remplace pas le nombre de réplicats biologiques. Une série synthétique courte ne valide pas une conclusion biologique. |
| Le cas contrôle=cible est « tautologique ». | **Avertissement pertinent, généralisation excessive.** | La configuration a terminé, renvoie L7b ROBUSTE et une conversion ambiguë; elle n'est pas interprétée comme Tc. Certaines comparaisons peuvent être auto-référentielles, mais l'admissibilité dépend de la question d'analyse. Le contrat l'autorise et exige le marquage diagonal. |

## Détail observé de L7b-light

| Taille/configuration | Stabilité horizon | `t0_std` walk-forward | Cohérence interne | Verdict |
|---|---|---|---|---|
| L=8 | FAIL (minimum 0,75) | FAIL (19,552) | FAIL (direction cible ≠ direction régime; pénalité 0,20) | FRAGILE |
| L=12 | PASS (minimum 1,00) | PASS (9,740) | PASS | ROBUSTE |
| L=24 | FAIL (minimum 0,75) | FAIL (19,031) | PASS | FRAGILE |
| L=32 | PASS (minimum 0,833) | FAIL (19,031) | PASS | FRAGILE |
| L=48 | PASS (minimum 0,917) | FAIL (21,508) | PASS | FRAGILE |
| L=64 | PASS (minimum 1,00) | FAIL (22,127) | PASS | FRAGILE |

Les seuils (`stabilité >= 0,80`; walk-forward `t0_std <= 10`) sont les règles codées de L7b-light. Leur présence dans le code est un fait; leur pertinence scientifique universelle n'est pas démontrée par cet audit.

## Décision de suite

1. Garder v6.0 et les sorties antérieures gelées.
2. Ajouter un contrat de configuration qui autorise contrôle=cible et explicite les rôles et dépendances des colonnes.
3. Construire un banc synthétique à vérité connue; séparer données pilotes et graines confirmatoires.
4. Faire un diagnostic ciblé des fenêtres Levina avant toute correction de code.
5. Évaluer L7b-light et L7b-full séparément, sans attribuer leur sortie au trio Voie 2.

Ces décisions sont un plan de travail. Elles ne sont pas les résultats d'un nouveau test de performance du pipeline.
