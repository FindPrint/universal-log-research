# Sensibilité synthétique aux transitions — V2

Ce dossier contient un test synthétique du pipeline complet v6.0.1 sous trois amplitudes de signal, deux longueurs de série et plusieurs graines. Tous les flux numériques sont tournés comme axe de contrôle dans chaque entrée.

## Reproduction

Depuis la racine du projet, dans `.venv` :

```powershell
.\.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\TRANSITION_SENSITIVITY_V2\run_transition_sensitivity_v2.py" --prepare-only
.\.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\TRANSITION_SENSITIVITY_V2\run_transition_sensitivity_v2.py"
```

Le harnais a été exécuté sous Python 3.11.9. `ENVIRONMENT_LOCK_V2.txt` consigne l’inventaire de paquets utilisé; pour recréer l’environnement depuis la racine, utiliser `py -3.11 -m venv .venv`, puis `..venvScriptspython.exe -m pip install -r "pancréasANALYSE_THERAPEUTIQUE_2026-11-22TRANSITION_SENSITIVITY_V2ENVIRONMENT_LOCK_V2.txt"`.

La seconde commande reprend les cas enregistrés comme terminés dans `run_state.json`. Les sorties natives du pipeline sont dans `runs/`; les entrées, journaux, résumé et rapports sont conservés séparément. Le plan d’expérience gelé se trouve dans `PROTOCOLE_SENSIBILITE_TRANSITIONS_V2_FR.md`.

## Résultats V2

35/35 appels ont terminé et les huit assertions d’intégrité technique ont passé. T0 est disponible dans 15/15 appels de condition nulle; faute de règle d’alarme ou d’abstention préspécifiée, ce nombre n’est pas un taux de fausse alerte. Sur les quatre appels non nuls à axe temporel, l’erreur absolue au centre injecté de 58 % est de 3,99 à 38,15 points de pourcentage (médiane 28,00), avec peu de répétitions. Ce résultat reste descriptif et synthétique.

Quatre appels ont dépassé 300 secondes (maximum 729,6 s). Il s’agit de durées complètes par appel; aucun profil par estimateur ni cause n’a été établi. Voir `runtime_summary_v2.csv` et le rapport d’audit.

La première version du rapport est conservée dans `logs/AUDIT_RESULTATS_SENSIBILITE_V2_FR_PRE_CORRECTION.md`; l’erratum `CORRECTION_RAPPORT_V2_FR.md` documente la correction de lecture de la catégorie `null`. Les appels du pipeline n’ont pas été relancés pour cette correction.

## Portée

Les entrées sont générées. Le résultat décrit seulement les sorties de la configuration identifiée. La condition nulle ne reçoit pas de taux de fausse alerte faute de règle d’alarme préspécifiée; les écarts T0 ne sont calculés que sur l’axe temporel où le centre de la transition est défini par le générateur. Les contrôles restent distincts et ne sont pas filtrés selon la monotonie.
