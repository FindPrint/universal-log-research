# Reproduction Ising archivée — neuf axes de contrôle

Ce dossier contient une copie des entrées et du moteur historique v2 trouvés
dans les archives. Le CSV a 200 lignes; les empreintes des fichiers sont dans
`historical_protocol.json`. Le générateur fourni n'avait pas de graine fixe,
donc une nouvelle génération ne garantit pas le même CSV. Pour reproduire les
résultats enregistrés, utilisez le CSV archivé tel quel.

L'essai `run_all_controls_fixed_fast.py` traite successivement chaque colonne
numérique comme axe de contrôle, avec les mêmes paramètres rapides
(Cohen-d, fenêtre 80, optimisation automatique désactivée). Le contrôle
sélectionné n'est pas envoyé comme flux analytique sur la voie automatique.
Les axes non monotones restent inclus. Les nouvelles sorties vont dans
`rerun_fixed_fast/`, séparées des sorties archivées.

Les seuils du résultat sont des positions de rang dans cette analyse. Ce
balayage ne prédit pas une transition physique et ne remplace pas une
validation à tailles multiples.
