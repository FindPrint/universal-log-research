# Journal d’audit : décisions, hypothèses et preuves

Ce registre consigne les choix de protocole et leur justification vérifiable. Il distingue les hypothèses des observations et des interprétations; il ne transforme pas les résultats exploratoires en validation universelle.

## Faits de provenance

- Le code fourni v5.9.0 a été conservé sans modification : SHA-256 4f80f6a7d0809e802cbc9ec30c0bed552c1c8a95eb58687fd78e4ffd8e808260.
- La v5.9.1 est une version dérivée et reproductible, documentée par audit_release/build_v5_9_1_auditfix.py, v5.9.0_to_v5.9.1_auditfix.diff et v5.9.1_patch_provenance.json.
- L’environnement de contrôle était Python 3.11.9 dans .venv; l’environnement n’est pas inclus dans le ZIP. Les versions des paquets sont consignées dans audit_release/requirements-lock.txt.

## Hypothèses expérimentales et résultats

| Identifiant | Hypothèse testée | Observation archivée | Portée |
|---|---|---|---|
| H1 | Les observables thermodynamiques MCMC concordent avec les références finies archivées. | 178/180 écarts standardisés combinés sont dans ±2; maximum 2,338. Pics de χ sur la grille : L16 2,40; L32 2,34; L48 2,30. U4(Tc) : 0,6114; 0,6106; 0,6081. | Description de campagnes/grille finies; ±2 est descriptif, pas un critère de succès. |
| H2 | Le contrôle choisi peut infléchir la sortie. | Parmi 15 contrastes : 12 labels divergence, 2 saturation, 1 criticality. À Tc, l’aimantation varie selon L; les quatre autres axes donnent divergence. | Association sous réglages testés; pas une preuve causale ou d’indépendance des flux. |
| H3 | Le choix des flux peut changer les statistiques du pipeline. | À L16,Tc, dcrit moyen sur cinq chaînes : all_fluxes 3,415±0,095; famille paramètre d’ordre 3,444±0,137; sans bruit 3,415±0,087; aimantation absolue seule 2,866±0,183. Les 20 labels de ces comparaisons restent divergence. | Ablation limitée à cette cellule et à ces flux. |
| H4 | Le label actuel discrimine Tc des températures voisines. | 36/36 configurations thermiques avec MC_Update et flux communs sont classées divergence. | Échec de spécificité pour cette configuration; aucun détecteur critique validé. |
| H5 | Les médianes brutes des 29 estimateurs changent entre v5.8 et v5.9 sur les entrées appariées. | 580/580 paires sur 20 CSV sont exactement égales (écart max 0). | Non-régression bornée aux mesures brutes sur ce lot; n’atteste pas la parité des exports ou de la taxonomie. |

## Choix qui ne sont pas des résultats

- La grille thermique utilise un pas de 0,02 et ajoute Tc analytique. Elle localise un maximum de grille, pas un optimum continu.
- L’étude MCMC retient L=16, 32, 48, cinq chaînes dans l’ablation ciblée, et 8 000 mises à jour mesurées par trajectoire. Ce sont des paramètres de protocole, non des valeurs universelles.
- La règle de lecture ±2 pour les écarts standardisés est descriptive. Elle n’a pas servi à proclamer une réussite globale.
- Les seuils L7b (5, 10, 20, 0,50, 0,80 et diagnostic d’échelle) sont des choix du code non calibrés sur un corpus indépendant. La v5.9.1 corrige des cas de données manquantes et de signe, mais conserve ces seuils.
- Le scan de paysage de l’étude a été dérivé à 24 positions pour correspondre aux entrées enregistrées; la source v5.9 annonçait 120. L’incohérence source 120 / observations 24 reste explicitement enregistrée dans les métadonnées historiques.
- Les flux corrélation de voisins et énergie sont algébriquement redondants (corr = -E/2); |m|, m² et m⁴ sont également fortement dépendants. Ils ne valent pas des réplications indépendantes.

## Vérifications effectuées pour v5.9.1

Le résultat détaillé est audit_release/v5.9.1_validation.json : 11 contrôles ciblés passent, dont partition taxonomique 21 dimensions-proxy / 8 signatures, égalité des médianes et de D_vector sur une entrée réelle, export de 29 estimateurs, CLI --help, et 10 cas synthétiques L7b.

La commande --help du fichier fourni v5.9.0 a levé ValueError: unsupported format character 'm' dans argparse, déclenché par 80% dans un texte d’aide. La copie dérivée remplace ce libellé et le contrôle CLI passe. Cela ne prouve pas que tous les parcours de la CLI sont corrects.

## Limites et décisions ouvertes

- Aucun test ciblé ne remplace un audit d’intégration complet du mode L7b (run_full_unified_pipeline, light et full) ni une calibration des seuils.
- La détection TLog n’a pas démontré de localisation fiable de Tc dans les pilotes archivés; les nombres géométriques sont des sorties du pipeline, pas des observables thermodynamiques établies.
- Le pilote quantique fini signale un mouvement des marqueurs physiques vers g=1 avec N, mais TLog dcrit autour de 0,96 ne localise pas gc dans ce jeu de données.
- Une campagne indépendante, des contrôles négatifs mieux équilibrés, davantage de tailles et une calibration pré-enregistrée sont nécessaires avant toute affirmation de généralité.
- Le propriétaire a confirmé MIT pour le code et CC BY 4.0 pour les documents/résultats. Le texte canonique CC BY 4.0 a été archivé depuis la page officielle Creative Commons le 14 novembre 2026; les fichiers de licence sont inclus à la racine.
