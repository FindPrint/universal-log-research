# Journal d'exécution

## Plan v1 initial — interrompu, aucune sortie analysée

Le premier lancement utilisait 50 appels complets aux 29 estimateurs pour chacune des 16 combinaisons longueur/scénario, soit 800 appels `apply_complexity`. Après plusieurs minutes de calcul CPU, le processus a été arrêté manuellement avant d'écrire des fichiers de résultats. Aucun résultat de cette tentative n'est utilisé.

Le protocole a été amendé en v1.1 avant le lancement retenu : 50 courbes Monte-Carlo restent prévues pour évaluer les ajustements Hill, mais les 29 estimateurs ne sont sondés que sur le premier tirage de chaque combinaison (16 appels). Cette réduction ne permet pas d'affirmer la stabilité des estimateurs; elle limite le test à leur calculabilité et à une lecture descriptive ponctuelle.
