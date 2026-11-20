# Audit thérapeutique PDAC — correction PRISM et grille multi-contrôles

**Date de calcul :** 2026-11-16  |  **Version :** v1  |  **Statut :** analyse préclinique exploratoire

## Résumé exécutif

Le criblage précédent a inversé le sens d’interprétation de l’axe KRAS : les scores Chronos les plus négatifs correspondent à une dépendance plus forte; l’ancien code les avait étiquetés « faible » après `qcut` et avait ensuite interprété le signe de Spearman dans le sens opposé. Les tables ci-jointes recalculent les associations avec un score `-Chronos` (valeur élevée = dépendance forte).

Le jeu PRISM 24Q2 contient **6,790 flux de réponse médicamenteuse**. Le filtre strict `OncotreePrimaryDisease == Pancreatic Adenocarcinoma` donne **64 modèles** dans Model.csv, **41** présents dans la matrice PRISM et **38** avec les contrôles CRISPR nécessaires. Tous les flux médicamenteux ont été mis en regard de **13 axes de dépendance**; seuls KRAS est l’axe préspécifié de référence, tandis que les 12 autres proviennent d’une sélection antérieure et restent exploratoires.

Pour KRAS seul, **1** flux franchit q<0,05 dans la famille de 6 790 composés : AS-77 (REP.PRIMARY; n=30; ρ=−0,724; q=0,0413; q dans REP.PRIMARY=0,0321). Mais son q global après correction sur les 13 contrôles × 6 790 flux est 0,246; il ne franchit donc pas ce contrôle familial plus large. PAVINETANT franchit q=0,0358 dans son écran REP.1M avec le signe opposé (ρ=+0,638), ce qui souligne l’hétérogénéité. Aucun médicament n’est validé comme piste par cette analyse.

## Résultats ancrés

| Analyse préspécifiée | n | Spearman ρ (dépendance KRAS, LFC) | q BH (tous flux KRAS) | Δ moyenne LFC (tiers dépendant − tiers faible) |
|---|---:|---:|---:|---:|
| MRTX1133, dose indiquée dans métadonnées 2.5 µM | 36 | -0.468 | 0.5925 | -1.039 |
| OLAPARIB (REP.PRIMARY; 2.5 µM) | 30 | 0.1208 | 0.9693 | 0.01121 |
| IRINOTECAN (REP.PRIMARY; 2.5 µM) | 27 | -0.1777 | 0.9442 | -0.3178 |
| GEMCITABINE-ELAIDATE (REP.PRIMARY; 2.5 µM) | 27 | 0.04212 | 0.9895 | 0.02207 |
| TRAMETINIB (REP.PRIMARY; 2.5 µM) | 30 | -0.2307 | 0.8828 | -0.735 |
| GEMCITABINE (REP.PRIMARY; 2.5 µM) | 27 | -0.1374 | 0.9687 | -0.2314 |
| 5-FLUOROURACIL (REP.PRIMARY; 2.5 µM) | 27 | 0.006105 | 0.9986 | 0.05455 |
| SELUMETINIB (REP.PRIMARY; 2.5 µM) | 30 | -0.06919 | 0.9789 | -0.1315 |
| PACLITAXEL (REP.PRIMARY; 2.5 µM) | 29 | -0.1719 | 0.9435 | -0.1242 |
| AS-77 (REP.PRIMARY; 2.5 µM) | 30 | -0.7241 | 0.0413 | -0.7098 |
| OXALIPLATIN (REP.PRIMARY; 2.5 µM) | 27 | -0.02808 | 0.9978 | -0.08767 |
| OXALIPLATIN (REP.PRIMARY; 2.5 µM) | 27 | 0.406 | 0.7873 | 0.8892 |

Lecture du signe : **ρ négatif** signifie que les modèles plus dépendants de KRAS ont une LFC plus basse, donc une réduction de viabilité plus marquée sous ce composé. Le calcul porte sur des lignées cellulaires et une mesure à dose fixe, pas sur des patients.

## Signal AS-77 : interprétation et vérification ciblée

L’annotation du catalogue associe AS-77 à KCNA3, KCNA5 et KCNN4. Des travaux indépendants en PDAC rapportent une expression accrue de KCNN4 et une baisse de croissance/motilité après inhibition génétique; cela motive une hypothèse sur les canaux, mais ne valide pas AS-77. Dans nos données, le suivi post hoc par dépendance CRISPR n’appuie pas un mécanisme KCNN4 : KCNN4 ρ=0,202 (p=0,285), KCNA3 ρ=−0,100 (p=0,599), KCNA5 ρ=−0,142 (p=0,454), chacun n=30. Ces p sont post hoc et non corrigées; le suivi est exploratoire et non indépendant.

## Contrôles × flux médicamenteux

Le fichier `pdac_prism_control_by_drug_fluxes.csv` contient les tests pour chaque paire entre les 13 contrôles CRISPR listés dans le manifeste et les 6790 flux PRISM. Les colonnes donnent les valeurs p, trois familles de q BH, le signe de l’association et l’écart descriptif entre tiers. Les contrôles autres que KRAS ont été choisis dans une analyse DepMap antérieure; leurs tests ne sont pas une validation indépendante.

## Ce que le pipeline peut conclure sur ces données

Je n’ai pas produit de T0 ni de TLog à partir de cette matrice. La version v6.0.0 fixe `min_len=50` en mode fast; le chevauchement utile est de 38 modèles. Surtout, l’ordre des lignées dans la table n’est pas un axe de temps, de dose ou de progression. L’ordonner artificiellement par un score ou réduire le minimum changerait la question et pourrait fabriquer un seuil. Le fichier d’entrée est conservé pour une future analyse lorsque nous disposerons d’une vraie série ordonnée adaptée.

La contribution raisonnable du pipeline ici est d’expliciter les axes de contrôle, de garder toutes les colonnes de flux PRISM et de tracer les choix. L’analyse des relations médicament–dépendance est faite avec Spearman et correction de multiplicité, outils adaptés à ce jeu transversal. Ces résultats pourront ensuite servir à construire une vraie question séquentielle ou à prioriser un essai de validation.

## Erreur historique et correction

Dans `prism_screen.py`, les valeurs Chronos étaient passées directement à `pd.qcut` avec étiquettes `faible, moyen, fort`. Comme les scores les plus négatifs indiquent la dépendance la plus forte, les groupes « faible » et « fort » étaient inversés. De plus, le code classait un Spearman négatif comme une sensibilité accrue des modèles « KRAS-fort », alors que le score brut Chronos est l’opposé de la dépendance. Le classement ancien ne doit donc pas être utilisé pour sélectionner un médicament. Les nouveaux CSV emploient `-Chronos` et écrivent la définition explicitement.

## Limites qui restent

- Données PRISM de criblage cellulaire publiques, release 24Q2; une réponse à dose unique ne reproduit ni pharmacocinétique, ni stroma, ni immunité, ni tolérance.
- Petit nombre de modèles PDAC et nombreuses comparaisons; les valeurs q corrigent le nombre de tests mais ne transforment pas une corrélation en causalité.
- `Model.csv` ne contient pas de statut de mutation KRAS; le criblage ne peut pas distinguer G12D, G12V, G12R ou KRAS sauvage. La sensibilité à MRTX1133 doit être analysée par génotype avant toute interprétation mécanistique.
- Les 12 contrôles additionnels ont été retenus après une analyse antérieure, d’où un biais de sélection possible.
- DepMap 26Q3 est disponible depuis le 5 octobre 2026 et corrige des problèmes de correction des effets de librairie CRISPR. Les données courantes locales sont 24Q4; la mise à jour est requise pour confirmation. L’accès direct au téléchargement 26Q3 a présenté une page de vérification Cloudflare lors de cet audit; aucune tentative de contournement n’a été faite.
- Au 2026-11-16, la FDA a approuvé le daraxonrasib (RASONQUE) pour certains adultes avec PDAC métastatique après au moins une ligne systémique; RASolute 302 a rapporté une médiane de survie globale de 13,2 contre 6,7 mois. Cela constitue une option thérapeutique clinique, pas une preuve de guérison. Le PRISM 24Q2 est antérieur et ne teste pas ce médicament; la priorité suivante est l’étude des réponses et résistances aux inhibiteurs de RAS avec données contemporaines.
- Aucun résultat de cet audit ne constitue un conseil thérapeutique. L’objectif est de créer une piste à valider expérimentalement et cliniquement.
- Sources de méthode et de contexte : DepMap PRISM (https://depmap.org/repurposing/); scores Chronos (https://forum.depmap.org/t/ceres-score-correlation-with-cell-proliferation/626); release 26Q3 (https://forum.depmap.org/t/announcing-the-26q3-release/4692); KCNN4 en PDAC (https://pmc.ncbi.nlm.nih.gov/articles/PMC8888650/); FDA daraxonrasib (https://www.fda.gov/drugs/cancer-approvals/fda-approves-daraxonrasib-metastatic-pancreatic-adenocarcinoma).

## Fichiers reproductibles

- `analyze_pdac_prism_multicontrol.py` — calcul intégral.
- `pdac_prism_control_by_drug_fluxes.csv` — matrice complète contrôles × médicaments.
- `pdac_prism_KRAS_corrected_all_compounds.csv` et `pdac_prism_KRAS_known_treatments.csv` — sortie principale.
- `AS77_channel_target_posthoc.csv` — vérification ciblée post hoc du mécanisme de canal.
- `pdac_prism_pipeline_input_cross_sectional.csv` — matrice filtrée avec tous les contrôles et flux pour audit; non utilisée pour inférer un seuil.
- `analysis_manifest.json` — empreintes SHA-256, versions, filtres, méthode, limites et inventaire des sorties.
- `Repurposing_Public_24Q2_Readme.txt` — README source copié pour documenter l’essai et la direction des mesures.
- `krasscore_selected_drug_response.png`, `krasscore_top15_descriptive.png` — graphiques descriptifs.

## Reproduction

Depuis la racine du projet, exécuter :

```powershell
.\.venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-16\analyze_pdac_prism_multicontrol.py
```

---

