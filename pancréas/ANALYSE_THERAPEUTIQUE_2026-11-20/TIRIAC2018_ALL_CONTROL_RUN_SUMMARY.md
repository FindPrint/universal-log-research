# Tiriac 2018 PDAC PDO — résumé du passage multi-contrôles

**Pipeline :** `UNIVERSAL_LOG_v5.9.4.py`  
**Cible fixée :** Gemcitabine AUC  
**Données :** 60 PDO complets, 26 colonnes AUC  
**Contrôles :** les 25 autres colonnes numériques, chacun exécuté séparément  
**État :** 25/25 exécutions terminées sans erreur

## Résultat enregistré

Pour les 25 contrôles, le statut du pipeline est `ok`, `T0 ambiguous = True` et `Control monotone = False`. Les valeurs T0 varient selon le contrôle. Ces sorties ne constituent ni un classement de médicaments ni une mesure de seuil clinique.

Le tableau original préserve l'ordre des lignes du jeu source; les PDO sont des modèles distincts et non une trajectoire temporelle de maladie. Le jeu ne fournit pas de résultat clinique individuel associé à chaque organoïde. L'interprétation reste donc exploratoire et limitée à cette configuration.

## Reproduction et audit complet

Le paquet complet `TIRIAC2018_GEMCITABINE_ALL_CONTROLS_PDAC_AUDIT_BUNDLE.zip` comprend la préparation des données, les empreintes, la version exacte du pipeline, les commandes, journaux et exports par contrôle. Il est conservé localement sous `output/pdac_pipeline_audit_2026-11-19/`; les archives ZIP et PDF sont exclues du dépôt Git normal et doivent faire l'objet d'un paquet de publication séparé.

**Provenance :** Tiriac et al., *Cancer Discovery* (2018), DOI [10.1158/2159-8290.CD-18-0349](https://doi.org/10.1158/2159-8290.CD-18-0349). Les fichiers et données source de tiers gardent leurs licences et conditions d'origine.
