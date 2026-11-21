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

## Addendum — 2026-11-21 : faisabilité des données PDAC MRTX1133/MUC1-C

**Question examinée :** les matrices GEO publiques repérées permettent-elles de tester, avec le pipeline v6.0.0 complet, la réponse à MRTX1133 associé à une intervention sur MUC1-C?

- **Hypothèse de littérature :** une étude préclinique rapporte une activité d’un ADC anti-MUC1-C dans certains modèles PDAC résistants à l’inhibiteur KRAS G12D, avec une réponse à la combinaison qui dépend du modèle. Cela constitue une hypothèse à tester, pas un résultat de UNIVERSAL_LOG ni une preuve clinique. L’article indique que les autres données brutes sont accessibles sur demande raisonnable; aucune demande externe n’a été envoyée.
- **GSE269985 :** 30 bibliothèques RNA-seq; cinq modèles avec trois bibliothèques parentales et trois de résistance acquise par modèle. Comptages individuels dans 30 fichiers; l’ordre des modèles ne définit pas le temps.
- **GSE269313 :** 17 spécimens snRNA-seq, 9 sous MRTX1133 et 8 véhicule, prélèvements à des jours différents. Ce sont des observations transversales; les cellules ne sont pas des réplicats animaux. Les identifiants KPC_3421L/KPC_3421S sont gardés distincts comme spécimens et leur indépendance n’est pas présumée.
- **GSE293756 :** 6 bibliothèques d’un seul modèle AsPC-1/MR à shRNA MUC1 inductible, trois DOX+ et trois DOX−/DMSO. La matrice mesure l’expression; elle ne contient pas de tableau de réponse à l’ADC.
- **Code contrôlé :** `pancréas/universal_v6.0.0_cohen - Copie.py.txt`, SHA-256 `bb8bbdba4eb1f8c55b49748274ae8fbfef8a43f6c1b890964f18ba77960c0773`. La configuration rapide courante exige 50 points valides.
- **Décision d’analyse :** aucun lancement biologique du pipeline, T0 ou TLog. Les trois séries sont sous le seuil courant et ne sont pas une série ordonnée unique de réponse thérapeutique. Aucun balayage de contrôles n’a donc été compté comme test réussi ou résultat nul. Cette décision de compatibilité des données n’est pas une conclusion sur l’efficacité d’un traitement.
- Le script, l’inventaire, le manifeste source et le rapport sont publiés dans `pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/MRTX1133_MUC1C_AUDIT/`. Les fichiers GEO bruts restent exclus du dépôt; seules les URL et empreintes sont conservées.

## H6 — 2026-11-21 : adéquation des RNA-seq publics MUC1-C/MRTX1133

**Hypothèse exploratoire :** les réponses ARN de MUC1 et de marqueurs NFκB/interféron/EMT aux perturbations de MUC1, à MRTX1133 et à la résistance acquise sont-elles cohérentes entre modèles, et les flux permettent-ils un run du pipeline v6.0.0?

**Choix de protocole :** analyse descriptive Python de quatre séries publiques, 15 gènes et trois moyennes de panel déclarés dans le rapport, sans fusion inter-étude. Pour les comptages, transformation log2(CPM+1); pour la matrice GEO décrite RPKM, log2(RPKM+1). Contrastes et test de porte d’entrée consignés par échantillon. Il s’agit d’une réanalyse exploratoire, pas de la reproduction du workflow publié TCC/ComBat-seq/edgeR : R/Rscript n’était pas disponible.

**Observation :** 78 bibliothèques, 13 contrastes et 234 lignes de caractéristiques. MUC1 ARN diminue dans trois contrastes shRNA et dans les cinq comparaisons résistance/parental, mais varie selon les lignées après MRTX1133. Ces observations ne mesurent ni la protéine MUC1-C ni la réponse à un ADC. Sur 234 flux candidats, 218 complets ont été transmis à la fonction `apply_complexity` réelle et tous ont rendu 0/29 estimateur fini avec n=6, inférieur au minimum configuré de 50; 16 flux incomplets ont été omis.

**Conclusion permise :** les données analysées donnent une description exploratoire de l’expression des marqueurs et révèlent une incompatibilité de longueur pour la porte d’entrée v6.0.0. Elles ne constituent pas un run biologique complet target/contrôle, ne calculent aucun T0/TLog et ne valident ni n’invalident l’ensemble de la théorie/pipeline. Elles ne démontrent pas l’efficacité thérapeutique de l’ADC.

**Limites et suite :** n=3 par bras, matrice et protocole hétérogènes, 9/234 contrastes de caractéristique présentent une variance exactement nulle dans au moins un bras, tests exploratoires, absence de bras ADC et de réponse mesurée. Suite pertinente : obtenir une matrice d’efficacité directement mesurée sur plusieurs modèles et interventions; pré-spécifier axe, flux et contrôle; appliquer le pipeline complet sans convertir les réplicats en axe temporel ni contourner le minimum. Rapport, code, résultats et empreintes sont dans `pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/MRTX1133_MUC1C_AUDIT/`; voir le [rapport de réanalyse](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/MRTX1133_MUC1C_AUDIT/RAPPORT_REANALYSE_RNASEQ_MUC1C_FR.md).

## H7 — 2026-11-21 : disponibilité des données de réponse directe à l’ADC anti-MUC1-C

**Question :** les publications précliniques qui évaluent directement l’ADC anti-MUC1-C seul ou avec MRTX1133 déposent-elles les mesures par puits ou par animal dans une forme permettant de lancer v6.0.0?

**Observation bibliographique et dépôt :** l’article 2025 présente des essais directs de viabilité cellulaire et PDO, des combinaisons avec MRTX1133 et des volumes de xénogreffes. Son énoncé de disponibilité dit que les données brutes supplémentaires sont accessibles sur demande raisonnable. L’inventaire Figshare reproductible retrouve dix fichiers supplémentaires `.docx` (figures S1–S8, table S1 et document de supplément); aucun tableau public de valeurs brutes par puits ou animal n’a été trouvé. GSE181961 et GSE293756 sont des séries d’expression, pas des réponses à l’ADC. Un résumé ASCO 2024 rapporte aussi un xénogreffe HPAF-II avec 3D1-MMAE/7B8-MMAE sans fournir de matrice individuelle. L’article de 2022 sur HzMUC1-MMAE rapporte des réponses PDAC, mais vise une autre région de MUC1 et indique également que ses données sont sur demande.

**Compatibilité pipeline :** minimum actuel v6.0.0 = 50 points par flux. Les documents publics consultés ne donnent pas de série brute traçable de cette longueur. Les figures cellulaires/PDO rapportent trois ou cinq déterminations et les xénogreffes des groupes de six ou sept souris; les mesures répétées d’un animal restent groupées dans cet animal et ne doivent pas être empilées comme observations indépendantes. Aucun flux n’a été reconstruit à partir d’un graphique, aucune donnée n’a été imputée et aucun run complet cible/contrôle, T0 ou TLog n’a été produit.

**Décision et limite :** la disponibilité publique ne permet pas l’analyse numérique de la réponse à cet ADC avec la configuration courante. Ce constat ne réfute pas les résultats publiés, ne démontre pas leur réplication indépendante et ne valide ni n’invalide la théorie/pipeline. Le rapport, le script d’inventaire et les empreintes de métadonnées sont publiés dans `pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/MRTX1133_MUC1C_AUDIT/`. La prochaine donnée nécessaire est le tableau expérimental individuel transmis par les auteurs; aucune demande externe n’a été envoyée.

## H8 — 2026-11-21 : audit des recommandations petite cohorte / trithérapie / courbes dose-réponse

**Question :** les trois recommandations reçues sont-elles étayées et existe-t-il une donnée biomédicale publique permettant de commencer un essai reproductible des flux courts?

**Faits documentaires :** Yin et al. 2025 rapportent 46 PDO, 63 médicaments, plus de 7 000 mesures, essais en double et deux expériences indépendantes; le criblage utilise sept concentrations. Le fichier supplémentaire Data 10 contient des AUC résumées. La feuille Figure 6d du Source Data donne 75 courbes PDO–composé, avec deux colonnes de mesure par courbe et 7 ou 8 concentrations par colonne; le rôle exact des deux colonnes n’est pas expliqué dans l’en-tête et elles ont donc été gardées séparées.

**Test effectué :** avec Python du .venv, le fichier pancréas/universal_v6.0.0_cohen - Copie.py.txt (SHA-256 bb8bbdba4eb1f8c55b49748274ae8fbfef8a43f6c1b890964f18ba77960c0773) a été importé sans le modifier. Les 150 colonnes Figure 6d ont chacune été transmises à la fonction réelle apply_complexity en mode fast, Cohen-d, minimum 50. 30 colonnes avaient 7 mesures, 120 en avaient 8; 150/150 ont été rejetées par la limite, 0/29 estimateur fini. Il s’agit d’un contrôle de compatibilité d’entrée; aucune réponse biologique, aucun contrôle cible, aucun T0 ou TLog n’a été calculé.

**Évaluation des recommandations :** l’existence d’un enjeu petites séries est établie, mais la règle « 1 000 bootstraps et persistance à 95 % » n’est pas calibrée ici. Elle ne peut pas transformer 7–8 doses en 50 observations indépendantes. Les essais MRTX1133 + olaparib sont précliniquement documentés, mais aucun élément consulté n’établit le triplet ajouté à l’ADC MUC1-C ou à AS-77. Le chiffre de 87 % n’a pas été trouvé dans l’article primaire MRTX1133–olaparib. AS-77 demande vérification d’identité; il est aussi référencé comme PAP-1/Kv1.3, distinct de KCNN4/KCa3.1. PRISM et GDSC fournissent des courbes de 7–9 doses et constituent des benchmarks possibles, mais IC50 n’est pas égal par définition à T0.

**Décision :** ne pas modifier les limites ni annoncer un mode court validé. Créer une calibration séparée pour les courbes ordonnées courtes et les comparaisons de cohortes; faire des simulations à seuil connu et comparer à l’ajustement dose-réponse/AUC/IC50 conventionnel; conserver les réplicats groupés et permettre l’abstention. Rapport, scripts, empreintes source et résultat de compatibilité sont dans pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/AUDIT_RECOMMANDATIONS_PETITES_COHORTES/.

## H9 — 2026-11-21 : pilote synthétique de courbes courtes, 4PL et disponibilité des 29 estimateurs

**Question :** sur des courbes de dose synthétiques de 7–10 points dont l'IC50 est connue, le fit conventionnel et les estimateurs v6.0.0 se comportent-ils de façon à autoriser un mode court?

**Protocole :** protocole v1.1 gelé dans `pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/AUDIT_RECOMMANDATIONS_PETITES_COHORTES/COURBES_COURTES_SYNTHETIQUES_V1/PROTOCOLE_FR.md`. Le `.venv` a produit 800 courbes Monte-Carlo (4 longueurs, 4 scénarios, 50 tirages). Le fit Hill 4 paramètres a été calculé sur chaque courbe. `apply_complexity` de v6.0.0 inchangé a été appelé sur un seul premier tirage par condition, avec `min_len=N`, en profil `all`; ce diagnostic direct ne lève pas le seuil du pipeline complet. La durée rapportée est 301,3 s.

**Observations :** l'erreur médiane absolue de log10(IC50) sur la sigmoïde forte favorable est de 0,028–0,042 décade (P90 0,074–0,099); sur la sigmoïde faible/bruitée, médiane 0,572–0,626 et P90 1,968–4,500. Les 4PL convergent tous, y compris sur les nuls sans IC50 vraie; l'IC50 ajustée est néanmoins dans la plage testée dans 35–40/50 nuls plats et 34–43/50 courbes de bruit sans tendance. La convergence seule n'est donc pas un critère suffisant d'identifiabilité. Les sondages des 29 méthodes donnent 4/29 estimations finies dans tous les cas, sauf 5/29 sur deux courbes fortes à N=9/10.

**Limites :** les générateurs, bruit, plage de doses et IC50 au milieu de la gamme sont choisis. Les estimateurs n'ont qu'un seul sondage par combinaison, ne voient pas l'axe de dose, et leur stabilité n'est pas estimée. Aucun T0, TLog, Q, F1/F2, Voie 1/2 ou L7a/L7b n'a été calculé. Le nombre de tirages synthétiques ne correspond pas à des réplicats biologiques. Un premier plan de 800 appels aux estimateurs a été arrêté avant écriture; aucun résultat de cette tentative n'est utilisé et l'arrêt est journalisé.

**Décision :** les observations justifient de concevoir une calibration dose-réponse dédiée avec identifiabilité et abstention; elles ne valident pas un mode `N=7..10`, ne donnent pas de taux biologique de faux positifs et ne démontrent pas `T0=IC50`. Ne pas modifier la limite du run complet dans cette étape.

## H10 — 2026-11-21 : édition maître V5 et séparation du snapshot

**Question :** peut-on maintenir un seul livre blanc complet actif et fournir en même temps une archive reproductible du projet sans incorporer cette archive au PDF?

**Résultat de build :** le générateur `build_complete_whitepaper_v5.py`, exécuté avec le `.venv`, a construit le livre blanc V5 de 3 207 pages (environ 45,5 MB) et un snapshot ZIP externe de 6 260 fichiers (environ 8,7 GiB compressés; 13,6 GB avant compression). Les empreintes exactes sont enregistrées dans le manifeste et les sidecars de sortie.

**Contrôles :** le PDF a été relu par pypdf (3 207 pages, aucun EmbeddedFiles, aucun catalogue `/AF`, aucune annotation de pièce jointe) et par `pdfinfo`; l'archive a passé le contrôle CRC intégré au générateur. Les pages 1–4 et les deux dernières pages ont été rendues et inspectées visuellement. Le PDF ne contient aucun ZIP. L'archive exclut le V4 complet de 7,78 Go pour éviter l'imbrication d'un snapshot précédent; les livres blancs autonomes précédents sont conservés dans `archive_sources/whitepapers_legacy/`.

**Décision et limites :** V5 devient le seul livre blanc maître actif. Le ZIP est un fichier compagnon autonome et le PDF reste un document de 45,5 MB. Le snapshot ne comprend pas l'environnement `.venv`, l'historique Git, ni les sorties construites dans `output/master_whitepaper_v5/`; son manifeste liste les exclusions. Ce contrôle concerne le packaging et la lisibilité du livre blanc, pas une validation scientifique supplémentaire du pipeline ni des résultats PDAC.
