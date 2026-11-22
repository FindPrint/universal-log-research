# Audit structure source — UCI Air Quality V1

Fichier brut : 9,357 enregistrements datés et `13` flux numériques, SHA-256 `13277ae5d8581e80b7be09d47c7d3d06fe9b8e957078f2cf6e859f955e62f996`. L'UCI annonce 9 358 instances; ce CSV contient 9 357 lignes non vides et 114 lignes finales entièrement vides après import tabulaire.

## Horodatages

- Lignes entièrement vides dans le tableau importé, exclues du décompte des enregistrements : 114.
- Échecs de lecture d'horodatage parmi les enregistrements non vides : 0.
- Horodatage croissant dans l'ordre du fichier : True.
- Horodatages répétés parmi les enregistrements non vides : 0.
- Période du fichier : 2004-03-10 18:00:00 à 2005-04-04 14:00:00; la page UCI indique « March 2004 to February 2005 ».
- Lignes entièrement exploitables sur tous les flux numériques après masquage de `-200` : 827.
- Intervalle couvert par les lignes complètes communes : 2004-03-10 18:00:00 à 2004-05-01 00:00:00.

## Flux numériques et valeurs sentinelles

| Flux | `-200` | Valides | Distinctes valides | Min valide | Max valide |
|---|---:|---:|---:|---:|---:|
| `CO(GT)` | 1683 | 7674 | 96 | 0.1 | 11.9 |
| `PT08.S1(CO)` | 366 | 8991 | 1041 | 647.0 | 2040.0 |
| `NMHC(GT)` | 8443 | 914 | 429 | 7.0 | 1189.0 |
| `C6H6(GT)` | 366 | 8991 | 407 | 0.1 | 63.7 |
| `PT08.S2(NMHC)` | 366 | 8991 | 1245 | 383.0 | 2214.0 |
| `NOx(GT)` | 1639 | 7718 | 925 | 2.0 | 1479.0 |
| `PT08.S3(NOx)` | 366 | 8991 | 1221 | 322.0 | 2683.0 |
| `NO2(GT)` | 1642 | 7715 | 283 | 2.0 | 340.0 |
| `PT08.S4(NO2)` | 366 | 8991 | 1603 | 551.0 | 2775.0 |
| `PT08.S5(O3)` | 366 | 8991 | 1743 | 221.0 | 2523.0 |
| `T` | 366 | 8991 | 436 | -1.9 | 44.6 |
| `RH` | 366 | 8991 | 753 | 9.2 | 88.7 |
| `AH` | 366 | 8991 | 6683 | 0.1847 | 2.231 |

## Capacité de couverture par temps

Nombre de 100 bins calendaires vides par flux après exclusion descriptive de `-200` (aucune valeur n'est remplacée) :

- `CO(GT)` : 4/100
- `PT08.S1(CO)` : 0/100
- `NMHC(GT)` : 88/100
- `C6H6(GT)` : 0/100
- `PT08.S2(NMHC)` : 0/100
- `NOx(GT)` : 4/100
- `PT08.S3(NOx)` : 0/100
- `NO2(GT)` : 4/100
- `PT08.S4(NO2)` : 0/100
- `PT08.S5(O3)` : 0/100
- `T` : 0/100
- `RH` : 0/100
- `AH` : 0/100

Nombre de lignes complètes communes par mois (après masquage du sentinelle) :

- 2004-03 : 377
- 2004-04 : 449
- 2004-05 : 1

Aucun remplissage ni filtrage n'a été appliqué. Si des flux ont des périodes de validité différentes, une comparaison multivariée sur des points de support différents pourrait confondre l'effet de l'axe avec celui des données disponibles. Cette décision exige un protocole explicite avant l'appel pipeline.

## Limite et suite

Le code `-200` est traité comme donnée manquante conformément à la documentation UCI. Les bornes et fréquences observées restent des constats; elles ne prouvent pas une panne ni une saturation instrumentale. Le plan de rotation complète est reporté jusqu'à ce qu'une représentation commune des flux puisse être justifiée sans imputation arbitraire.
