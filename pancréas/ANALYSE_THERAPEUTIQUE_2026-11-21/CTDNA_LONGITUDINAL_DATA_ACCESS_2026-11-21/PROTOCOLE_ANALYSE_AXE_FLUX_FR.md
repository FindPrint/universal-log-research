# Protocole préliminaire — ctDNA longitudinal × UNIVERSAL_LOG

**Version :** 1.0 — gel documentaire avant accès aux données  
**Usage :** analyse exploratoire de données sérielles; aucun résultat clinique ou choix thérapeutique.

## 1. Question de travail

Décrire comment les sorties de l'ensemble du pipeline UNIVERSAL_LOG varient le long des mesures ctDNA et des autres flux numériques, puis comparer les observations à la réponse radiologique rapportée. Le TLog n'est pas traité comme toute la théorie : conserver les 29 estimateurs, les six groupes de questions, F1/F2 et les sorties TLog disponibles dans la version retenue.

## 2. Contrat d'entrée requis

Une ligne représente un **prélèvement**, avec au minimum :

| Champ | Rôle | Règle |
|---|---|---|
| `patient_key` | identifiant pseudonyme de groupe | catégorie; jamais convertie en axe numérique |
| `sample_key` | identifiant pseudonyme de prélèvement | catégorie; pas un flux biologique |
| `week_from_treatment_start` | temps relatif mesuré | unité en semaines et règle de calcul documentées |
| `ctdna_maf_percent` | flux biologique | échelle et seuil de détection documentés |
| `ctdna_status` | statut de détection | catégorie séparée; pas d'imputation en zéro sans justification source |
| `response_restaging` | issue clinique | catégorie PD / non-PD selon la définition publiée |

Inclure également, si fournis et documentés : quantité de cfDNA, CA19-9, volume tumoral, SLD, régime et ligne de traitement, dates relatives de restadification, PFS/OS avec indicateur d'événement/censure, limites de détection et motifs de valeurs manquantes. Ne pas inventer les colonnes absentes.

## 3. Vérification de structure avant le pipeline

1. Archiver les fichiers sources, licences/conditions, dictionnaire, empreintes SHA-256 et version de l'article.
2. Compter séparément patients, prélèvements, trajectoires complètes, prélèvements par patient et valeurs valides de chaque colonne.
3. Vérifier les unités et l'ordre temporel à l'intérieur de chaque patient; signaler dates ambiguës, ex æquo et mesures manquantes.
4. Confirmer que les mesures de réponse ne sont pas introduites dans le pipeline comme flux prédicteurs lorsqu'elles constituent l'issue comparée.
5. Tester l'admission d'une série avec le minimum v6.0.1 inchangé : moins de 50 valeurs valides dans le contrôle donne une abstention, pas un seuil forcé.

## 4. Règle de rôle contrôle × flux

Après validation du schéma, faire tourner **chaque colonne de mesure numérique admissible** comme contrôle candidat. Pour un passage donné, exclure la colonne sélectionnée de tous les flux analysés et des alias/composites. Garder les contrôles non monotones et consigner leur diagnostic de monotonie; la non-monotonie n'est pas une raison automatique de rejet. Laisser les catégories en catégories. Documenter toute exclusion de colonne et son motif.

`week_from_treatment_start` est le candidat d'axe temporel principal si l'horodatage relatif est cohérent. Les valeurs de temps répétées entre patients et les frontières des trajectoires exigent une représentation adaptée. Ne pas concaténer plusieurs patients comme s'il s'agissait d'une seule trajectoire continue.

## 5. Gestion des patients répétés

Le nombre de prélèvements peut dépasser 50 alors que le nombre de patients complets reste inférieur à 50. Il faut distinguer les unités de mesure des unités indépendantes dans chaque tableau et graphique.

- Si le cœur v6.0.1 n'accepte qu'une série simple sans frontières de patient, exécuter les séries séparément et garder l'abstention si elles sont trop courtes.
- Pour l'analyse de cohorte, ne lancer un mode groupé qu'après un test démontrant que les frontières patients sont préservées. Toute incertitude et rééchantillonnage doivent se faire au niveau patient, jamais en tirant des prélèvements indépendants au sein d'une même trajectoire.
- Si aucun mode groupé n'est disponible, consigner cette limite et ne rapporter qu'une analyse descriptive admissible; ne pas présenter les lignes répétées comme des patients indépendants.

## 6. Contrôles de sensibilité

Conserver les horodatages attachés à leurs prélèvements. Vérifier la stabilité à la permutation des **lignes du fichier** sans changer patient, temps ni valeurs associées; ce test mesure seulement une éventuelle dépendance à l'ordre de stockage. Toute permutation statistique doit respecter les blocs patients et le protocole de permutation doit être précisé. Ne jamais inverser les temps biologiques comme si cela représentait une nouvelle expérience observée.

Comparer les sorties par patient, par groupe clinique et par flux disponible; rendre visibles valeurs manquantes, nombres d'estimateurs finis et abstentions. Un `T0` interne n'est pas assimilé au seuil clinique publié ni à un changement de traitement.

## 7. Résultat, interprétation, hypothèse

Étiqueter séparément :

- **Résultat observé :** fichier, configuration, sorties et métriques réellement calculées.
- **Interprétation limitée :** ce que la structure et les contrôles permettent d'inférer, avec les limites d'échantillonnage et de répétition.
- **Hypothèse :** motif à retester dans une cohorte indépendante ou un jeu expérimental distinct.

Le seuil de 57,9 % rapporté dans l'étude est un benchmark du même jeu de découverte; aucune comparaison sur ces mêmes sujets ne constitue une validation indépendante. Toute hypothèse de bénéfice thérapeutique doit être examinée par les méthodes cliniques appropriées et des données externes.
