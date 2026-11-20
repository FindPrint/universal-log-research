# Protocole pilote verrouillé — Nature Communications 2025

## Statut avant exécution

Ce jeu est un **pilote exploratoire hors seuil confirmatoire** : l’article rapporte des résultats AUC pour 46 modèles PDO, sous le seuil `N >= 50` retenu pour les réplications principales. Les 46 modèles restent 46; aucune cellule, mesure technique ou répétition n’est convertie en observation supplémentaire. Un résultat de ce pilote ne comptera pas comme réplication externe validante.

## Source et forme attendue

- Article : *Pathogenic germline variants in Chinese pancreatic adenocarcinoma patients*, Nature Communications (2025), DOI [10.1038/s41467-025-57520-3](https://doi.org/10.1038/s41467-025-57520-3).
- Fichier public : `NatureComm2025_Supplementary_Data10.xlsx`, onglet `All Drugs AUC`.
- Structure vérifiée avant calcul : 63 médicaments en lignes, 46 colonnes PDO, plus une colonne de catégorie non numérique.
- Les valeurs AUC publiées sont transposées en 46 lignes × 63 colonnes médicaments. Valeurs inchangées; l’identifiant PDO est conservé comme texte. La catégorie descriptive est exclue des flux numériques.

## Configuration pré-déclarée

- Cible fixe : `Gemcitabine`, conservée comme ancre pour rendre le pilote comparable au balayage Tiriac précédent.
- Contrôles : chacune des 62 autres colonnes médicament, une fois chacune.
- Tous les autres flux numériques du CSV restent présents à chaque appel; seul le contrôle sélectionné par appel change.
- Ordre des PDO : ordre des colonnes dans la source publié, sans tri.
- Aucun remplissage, aucune imputation, aucun ré-échantillonnage, aucun calcul de pseudo-temps, aucune transformation des AUC.
- Pipeline : `UNIVERSAL_LOG_v5.9.4.py`, `.venv`, domaine `pdac`, mode `fast`, seed 42, L7b-light, graphiques désactivés dans le pipeline; sorties numériques conservées.
- Quatre appels pipeline au maximum simultanément; un worker interne par appel.

## Portée de l’interprétation

Le tableau est une cohorte transversale de PDO; l’ordre des modèles n’est pas une chronologie. Les T₀ et diagnostics du pipeline seront rapportés comme sorties calculées le long de cet ordre source, pas comme transition temporelle, seuil clinique ou preuve d’efficacité. Le N inférieur au seuil exclut tout statut de validation confirmatoire. Aucun résultat de laboratoire ex vivo ne constitue en lui-même une recommandation de traitement pour un patient.

## Limites de disponibilité

Le tableau complet des AUC est public. Le fichier source public ne contient pas de correspondance complète modèle-par-modèle entre les AUC et les critères cliniques. Le pilote n’évaluera donc pas la prédiction de réponse clinique.
