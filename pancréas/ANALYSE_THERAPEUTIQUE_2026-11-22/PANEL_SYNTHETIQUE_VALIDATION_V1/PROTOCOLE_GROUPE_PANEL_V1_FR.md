# Protocole gelé — intégration synthétique d’un panel longitudinal

**Version :** 1.0  
**Statut :** essai logiciel synthétique, sans données cliniques  
**Cœur testé :** UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py  
**Harnais :** run_grouped_panel_validation.py

## 1. Question testée

Peut-on conserver les frontières de trajectoires en exécutant le pipeline complet indépendamment par patient, puis tourner chaque colonne numérique de mesure en contrôle, sans modifier le cœur v6.0.1?

Le test ne cherche pas à montrer que T0 ou TLog localise la transition synthétique connue. Il évalue l’assemblage du panel, l’admission des séries, la transmission des colonnes et la présence des sorties du pipeline.

## 2. Hypothèse d’ingénierie

Si le harnais sépare d’abord les groupes, trie les prélèvements selon le temps interne au groupe, puis fait un appel distinct au cœur pour chaque patient et contrôle, alors :

1. aucune différence ou fenêtre d’analyse du cœur ne doit traverser une frontière de patient;
2. le nombre d’admissions est déterminé par les valeurs valides de chaque patient, et non par le nombre total de lignes du panel;
3. chaque contrôle numérique demandé doit être exécuté, y compris le contrôle non monotone;
4. le contrôle choisi ne doit pas paraître parmi les flux analysés de son run;
5. la structure conserve la déclaration des 29 estimateurs, la sortie du noyau complet, les groupes Q disponibles et la couche TLog fournie par l’entrée complète v6.0.1.

Cette hypothèse concerne le câblage logiciel seulement.

## 3. Construction synthétique

Le générateur crée trois identifiants catégoriels synthétiques, chacun avec 64 visites. Les cinq colonnes numériques sont :

| Colonne | Construction | Rôle dans le test |
|---|---|---|
| week_from_start | indices de 0 à 63 | ordre interne et contrôle candidat |
| signal_primary | logistique centrée vers 58 % de la trajectoire, bruitée | signal synthétique et cible numérique fixe |
| marker_correlated | mélange de la transition et du temps, plus bruit | flux lié au signal |
| marker_oscillatory | sinusoïde, composante de transition et bruit | contrôle non monotone candidat |
| noise_independent | bruit blanc généré avec graine fixe | flux sans signal construit |

Les paramètres et graines sont inscrits dans le script et le manifeste. Ils sont choisis pour produire plusieurs formes de flux testables, pas estimés à partir de données biologiques. Les identifiants patient/prélèvement et la classe de génération sont catégoriels et ne sont pas des contrôles.

Tous les contrôles numériques sont tournés une fois par patient : 3 patients × 5 contrôles = 15 appels complets prévus. Le contrôle reste distinct du rôle d’ordre des lignes : le harnais trie par week_from_start, puis remet le CSV d’un patient à l’appel v6.0.1.

## 4. Configuration retenue et limites

- Cœur inchangé : v6.0.1; empreinte inscrite au résultat.
- Mode fast; minimum observé dans le cœur : 50 valeurs valides par run.
- Contrôle fixe demandé pour les niveaux qui consomment une cible : signal_primary.
- Rotation de contrôles : toutes les colonnes numériques, y compris la cible; lorsque contrôle et cible coïncident, le repli explicite v6.0.1 doit être visible et ce run n’est pas comparable aux autres pour les niveaux dépendant de la cible.
- Le nombre de scénarios des niveaux prédictifs auxiliaires est ramené à 8 et les workers à 1. Ce choix de budget réduit l’effort de calcul; aucun résultat prédictif n’est évalué dans cet essai.
- Validation harmonique désactivée; L7b en mode light.
- Aucun bootstrap patient n’est calculé. Trois trajectoires synthétiques ne justifient pas un intervalle inférentiel.
- Aucun CSV clinique n’est chargé.

Ces décisions sont des choix de protocole, pas des résultats observés.

## 5. Contrôle négatif de cohorte courte

Une seconde entrée contient trois patients de 32 visites (96 lignes au total). Le harnais doit séparer les groupes avant le garde d’admission : les 15 couples patient/contrôle s’abstiennent, et le moteur de pipeline n’est jamais appelé. Le fait que 96 dépasse 50 ne rend pas les trajectoires admissibles.

En complément, verify_short_core_gate.py appelle directement l’entrée complète v6.0.1 sur une trajectoire individuelle de 32 visites. Le résultat attendu est l’exception explicite Série trop courte, 32 points valides, au moins 50 requis. Cette exécution vérifie le garde réel du cœur; le test des trois groupes vérifie que le wrapper s’abstient avant de le solliciter.

## 6. Critères de réussite techniques préétablis

La validation V1 passe seulement si les assertions suivantes sont vraies :

1. le mélange de l’ordre global des lignes, suivi du tri interne patient/temps, restitue le même panel normalisé;
2. le cas court s’abstient pour les 15 couples et l’instrumentation confirme zéro appel au moteur;
3. les 15 couples prévus couvrent chaque patient et chaque colonne numérique comme contrôle;
4. le contrôle du run n’est pas présent dans la liste des flux analysés;
5. les 29 noms d’estimateurs sont présents dans la carte de classes du résultat;
6. le contrôle diagonal avec la cible est signalé explicitement;
7. les trois runs avec le contrôle oscillatoire sont produits, sans filtrage pour non-monotonie.
8. l’appel direct v6.0.1 d’une série individuelle de 32 lignes lève l’exception prévue au garde de longueur.

Un run en erreur rend la couverture incomplète et empêche le statut global passed.

## 7. Résultats à rapporter

Le résultat de chaque run est conservé avec ses sorties complètes. Le résumé par patient/contrôle reprend le statut de l’axe, la monotonie, T0 disponible, les médianes TLog par classe, les groupes de scores Q émis, les flux analysés et la cible utilisée. Les valeurs ne sont pas poolées en une trajectoire de cohorte.

## 8. Portée d’un succès

Un succès n’établit pas que T0 repère la transition synthétique, que les sorties sont statistiquement exactes, que la théorie est validée, ni que l’analyse convient à une cohorte PDAC. Il montrerait seulement que cette architecture de séparation et d’appels a satisfait les critères de câblage choisis sous cette configuration. La validité de seuil, l’incertitude entre patients, les règles d’agrégation et l’usage de données réelles restent des questions à tester séparément.
