# UNIVERSAL_LOG — état V12

**Version de recherche en cours :** V12, 22 novembre 2026. Ce projet étudie un pipeline complet d’analyse de flux ordonnés; TLog est une composante de la théorie, pas toute la théorie. L’analyse dépend aussi de la préparation des données, des axes et contrôles, de la sélection/exclusion des flux, des interactions, des estimateurs, des règles de seuil et des diagnostics.

## Trois questions séparées

1. **Tâche visée :** les modèles prédictifs sont évalués sur des blocs hors-échantillon et comparés à des témoins pertinents.
2. **Comportement du pipeline :** v6.0.1 est essayé sous rotations d’axes; chaque sortie reste liée au CSV, aux transformations et aux paramètres qui l’ont produite.
3. **Mesure et instrumentation :** ordre, lots, transformations, capteurs, bruit et données manquantes sont examinés comme explications concurrentes du signal.

Un seuil du pipeline peut refléter le système de mesure. Il faut comparer flux d’instrument, contrôle et cible avant d’attribuer un résultat au phénomène étudié. Les mots « hypothèse », « observation », « résultat robuste », « interprétation » et « conclusion de domaine » ont des statuts distincts.
Le protocole commun qui sépare phénomène, mesure/collecte et préparation/calcul est décrit dans `PROTOCOLE_TRIAGE_SEUILS_ET_ORIGINE_V1_FR.md`; il distingue aussi l’analyse descriptive de la prédiction.

## Travaux récents

- **AI4I 2020 — maintenance prédictive :** classifieurs conventionnels testés sur trois blocs chronologiques; jeu synthétique obtenu depuis Kaggle puis comparé octet pour octet à UCI. Les scores ne valident pas UNIVERSAL_LOG.
- **AI4I — rotation v6.0.1 :** 12/12 contrôles numériques exécutés sur 100 moyennes de blocs; 29 estimateurs détectés par appel, 11 flux analysés après exclusion du contrôle, zéro erreur. L’axe demandé contrôle=cible déclenche le garde-fou v6.0.1 et substitue `UDI` comme cible réelle; il est isolé du groupe à cible constante.
- **Sorties complètes AI4I :** le rapport multi-couches expose les six matrices Q, les cinq seuils F1/F2/T0, les médianes TLog par classe, Δ, L1/L7, diagnostics de bruit et empreinte instrumentale. Dans ces 12 sorties, le code marque Q3 comme identique à Q1 et L7b comme fragile; ce sont des états du pipeline, pas des validations du domaine.
- **Bike Sharing — mobilité urbaine :** estimation de `cnt` sur deux blocs chronologiques futurs de 4 345 enregistrements chacun, pas 4 345 heures continues. L'audit postérieur trouve 165 créneaux sans ligne dans l'étendue complète; leur cause n'est pas documentée et rien n'a été imputé. V1/V2/V3 conservent les comparateurs et codages successifs. V3 encode les codes catégoriels en one-hot. La météo mesurée à l’heure cible fait de ceci une estimation rétrospective, pas une prévision opérationnelle météo à l’avance.
- **Bike Sharing — rotation v6.0.1 :** 16 contrôles numériques dans 100 blocs temporels; 5 axes terminés, `holiday` en cours au dernier état. Les T0 des cinq axes terminés s'étendent de 18,4 % à 90,4 %; trois contrôles sont non monotones et marqués ambigus. Ces sorties sont provisoires et dépendent de l'axe; onze contrôles restent à traiter. `casual` et `registered` restent des flux analysés, mais sont interdits comme prédicteurs car leur somme vaut exactement `cnt`.
- **Bike Sharing — chaîne de mesure :** le Readme attribue les informations météo à Freemeteo, mais aucun modèle de capteur, étalonnage, incertitude ni journal de disponibilité des stations n'est fourni. Dans le fichier, `hum=1` apparaît 270 fois et `windspeed=0` 2 180 fois. Ce sont des concentrations observées à investiguer, pas une preuve de saturation, d'artefact ou de seuil instrumental.
- **Air Quality UCI — instrumentation :** l'audit a retiré du décompte 114 lignes terminales vides et observé 9 357 lignes horodatées, alors que la page UCI annonce 9 358. Le code manquant `-200` affecte fortement `NMHC(GT)`: seulement 827 lignes complètes communes restent entre le 10 mars et le 1er mai 2004. Une entrée 100 bins conserve les 13 flux, les `NaN` sans imputation, un axe temps dérivé et la fraction manquante globale. Les 15 contrôles sont prévus, mais aucun appel pipeline Air Quality n'a encore été lancé. Le contrôle `NMHC(GT)` n'a que 12 bins valides et devrait être déclaré insuffisant par le garde-fou v6.0.1. Un benchmark de lecture de référence est préspécifié séparément; couverture seule vérifiée (3 plis, 3 145/947, 4 092/1 240, 5 332/2 012 train/test), aucun modèle ajusté.
- **Profilage :** un cas apparié a rendu les mêmes sorties analytiques avec rendu graphique désactivé et un temps inférieur; ce seul cas ne garantit pas l’accélération pour tous les jeux.
- **Archives :** l’audit comparatif V4–V11 n’a rien supprimé; V4 et la V6 initiale ont des membres différents/absents du contenu V11. Le plan delta ne remplace pas l’historique.

## Reproduction

Utiliser le `.venv` et les protocoles propres à chaque benchmark. Les scripts de téléchargement inscrivent les sources, licences, tailles et SHA-256. Les plans pipeline contiennent l’empreinte de v6.0.1, des entrées et du protocole. Les journaux/résultats par appel restent dans `runs/` dans l’archive locale complète.

Le rapport AI4I et les résultats prédictifs Bike sont des observations sur ces jeux seulement. Ils ne démontrent ni universalité, ni causalité, ni utilité médicale. Aucun traitement du cancer du pancréas n’est validé par ces expériences.

## État des archives et licences

Le livre blanc complet V12 est construit à partir du PDF V11 par ajout incrémental. Le ZIP de projet demeure une archive distincte et n’est jamais intégré au PDF. Le snapshot V11 reste le point d’ancrage du delta; les ZIP historiques V4–V10 demeurent conservés séparément. Les données AI4I et Bike Sharing gardent leurs licences CC BY 4.0 et leurs attributions UCI respectives.
