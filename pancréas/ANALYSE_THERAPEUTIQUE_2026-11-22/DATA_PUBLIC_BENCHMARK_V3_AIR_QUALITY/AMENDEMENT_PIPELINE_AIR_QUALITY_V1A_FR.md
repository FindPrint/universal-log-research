# Amendement post-audit — entrée multi-flux Air Quality V1a

**Moment :** après réception et audit du CSV, avant le premier appel UNIVERSAL_LOG. Cet amendement est exploratoire et ne remplace pas le protocole V1.

## Pourquoi l'entrée change

Le CSV a 9 357 enregistrements datés et ordonnés, contre 9 358 instances annoncées sur la page UCI; l'import tabulaire comporte aussi 114 lignes terminales entièrement vides, retirées du décompte des observations. Le code `-200` documenté est masqué en `NaN`. La suppression de toutes les lignes contenant au moins un `-200` ne garderait que 827 enregistrements entre le 10 mars et le 1er mai 2004, principalement parce que `NMHC(GT)` manque sur la majorité de l'année. Une telle restriction modifierait fortement la période représentée.

Le pipeline v6.0.1 contient explicitement des chemins de traitement où les flux analytiques conservent leurs lignes manquantes comme `NaN` sans imputation, tandis que les points où le contrôle est manquant sont retirés pour cet appel. La campagne utilisera donc tout l'intervalle temporel et préservera les cellules manquantes, plutôt que de fabriquer des mesures ou de réduire silencieusement la période à des cas complets.

## Entrée gelée proposée

- 100 blocs consécutifs de tailles proches, selon l'ordre horaire source confirmé; moyenne par flux en ignorant `NaN`; un bloc entièrement manquant reste `NaN`.
- Les 13 flux numériques de la source sont conservés. Chaque flux est proposé une fois comme contrôle, y compris la cible demandée `CO(GT)`.
- Deux flux dérivés sont ajoutés et identifiés comme tels : `time_index_hours` (position horaire moyenne dans le bloc) et `missing_fraction_numeric` (fraction des cellules numériques originales codées `-200` dans ce bloc).
- Le contrôle sélectionné reste exclu des flux analysés. Si l'axe `NMHC(GT)` n'a que 12 blocs valides, v6.0.1 devrait refuser son seuil parce que son minimum fast-mode est 50; cette réponse sera consignée comme soutien insuffisant, pas comme seuil détecté ni comme erreur du domaine.
- Si `CO(GT)` demandé en cible est aussi contrôle, toute substitution de cible imposée par le garde-fou sera conservée telle quelle et isolée des autres axes.

## Lecture permise

Cette version répond à la question « que fait le pipeline avec les flux d'origine, en présence des absences telles qu'elles sont enregistrées, et avec un indicateur de disponibilité? ». Elle ne répond pas encore à « pourquoi `NMHC(GT)` est absent », ne prouve pas une panne de capteur, et ne sépare pas seule la dérive physique de la dérive instrumentale. Les résultats seront comparés aux dates, aux flux de référence, aux flux capteurs et à `missing_fraction_numeric`; aucun alignement ne sera déclaré causal.

Le choix de 100 blocs est cohérent avec les rotations Bike et AI4I précédentes, mais demeure une résolution de calcul. Sa sensibilité n'est pas établie. Les sorties brutes du CSV restent locales en attendant clarification des conditions de partage UCI.
