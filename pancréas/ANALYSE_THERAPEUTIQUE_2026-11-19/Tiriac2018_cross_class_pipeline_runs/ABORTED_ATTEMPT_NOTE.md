# Essai technique interrompu — configuration générique

## Statut

Cette première matrice a été interrompue avant son achèvement. Les quatre exécutions terminées ont été conservées comme traces techniques, mais elles ne sont pas retenues comme résultats PDAC, car l’option `--domain pdac` avait été omise et les métadonnées du pipeline indiquent `domain=generic`.

## Configuration observée

- Pipeline : `UNIVERSAL_LOG_v5.9.4.py`, SHA-256 `72fd242c4cb26e5663fa40f1b4998de60c63e2aebbae2773d0d34d904152001b`.
- Entrée : `Tiriac2018_66PDO_drug_AUC.csv`, SHA-256 `eb9fc0b9092e6dd18eb6896ae27ade6c0410cb2ed7b2129e5e9ba384e191bad4`.
- Mode : `fast`, graine 42, 26 profils AUC en flux, `Gemcitabine` ou une autre chimiothérapie comme cible, `Selumetinib` comme premier contrôle.
- Lancement : matrice prévue de 210 couples; arrêt après les premiers contrôles terminés, avant la fin du premier groupe.

## Exécutions conservées

| Cible | Contrôle | T0 (% axe pipeline) | Ambiguïté T0 signalée |
|---|---|---:|---|
| Gemcitabine | Selumetinib | 36.2505 | oui |
| 5-FU | Selumetinib | 63.5041 | oui |
| Paclitaxel | Selumetinib | 21.3475 | oui |
| SN-38 | Selumetinib | 24.6317 | oui |

Ces valeurs sont des sorties brutes de l’essai `generic`, conservées uniquement pour l’audit. Elles ne sont pas utilisées pour conclure sur la maladie ou les traitements.

## Motif de l’arrêt

Le domaine était mal spécifié pour l’objectif. Les exécutions ont été arrêtées, leurs sorties gardées, et le prochain lancement utilise le domaine explicite `pdac`, une cible fixe `Gemcitabine` et chaque autre flux numérique comme contrôle. Aucun résultat de l’essai interrompu n’est mélangé à cette nouvelle matrice.
