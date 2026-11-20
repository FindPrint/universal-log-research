# Addendum exploratoire pré-run — sensibilité aux flux physiques fournis

**Écrit avant l'exécution secondaire :** 15 novembre 2026. Cet addendum ne modifie pas le protocole principal déjà gelé.

## Pourquoi ce contrôle

Le CSV principal contient Énergie, aimantation, susceptibilité, capacité calorifique et Binder. Le pipeline peut exploiter ces colonnes comme flux alors même qu'il prédit une cible fixe énergie. Les positions des pics χ/Cv et croisements Binder sont donc des repères, mais pas un test aveugle sur des colonnes cachées.

## Configuration secondaire fixée

- Reprendre le CSV L=64 du protocole principal, même 76 lignes triées par température.
- Créer une entrée séparée contenant seulement `Temperature` et `Energy_per_spin`.
- Conserver la cible `Energy_per_spin`, le contrôle `Temperature`, mode `fast`, Cohen-d, 12 itérations MC, triangulation `default`, L7b `light`, graine 20261115 et un worker.
- Comparer le T0, Q1–Q6, F1/F2, Voie 1/2, TLog, L7a/L7b et le coût au run riche L=64 du protocole principal.
- Conserver le CSV à deux colonnes, son hash, les journaux et les sorties maîtres dans un dossier de run distinct.

## Statut d'inférence

Ce test est une analyse de sensibilité exploratoire décidée après observation du run L=64 riche. L=64 est retenu parce que son T0 initial est le plus proche de la référence analytique parmi les grands réseaux examinés; ce choix postérieur aux résultats interdit de présenter cette comparaison comme une confirmation pré-spécifiée. Si T0 reste proche de Tc sans χ/Cv/Binder dans le CSV, cela réduit une explication par accès direct à ces flux, mais ne démontre ni universalité ni causalité. S'il se déplace, cela quantifie la dépendance de la sortie à ces colonnes.
