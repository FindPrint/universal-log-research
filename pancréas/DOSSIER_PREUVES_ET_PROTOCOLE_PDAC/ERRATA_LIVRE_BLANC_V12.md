# Erratum scientifique — livre blanc PDAC Universal Log V12

**Objet :** clarifier la portée des résultats résumés dans le livre blanc intégral V12 et dans le dossier PDAC de six pages.
**Statut :** erratum de recherche; les PDF archivés ne sont pas modifiés par cette note.

## Corrections de portée

1. **Benchmark GDSC2, `r = 0,9911` (livre blanc, pp. 1–2 et appendice PDAC, p. 2).** Les fichiers `GDSC2_PDAC_REFERENCE_CURVES.csv` inspectés sont générés par `run_gdsc2_pdac_benchmark.py` à partir d'IC50 et de pentes paramétrés dans le code, puis de bruit simulé. La corrélation mesure l'accord avec ces valeurs synthétiques intégrées au générateur; elle ne constitue pas une validation indépendante sur 675 mesures brutes de Sanger/GDSC2. Le code et les colonnes du paquet ont été renommés pour rendre cette provenance explicite.

2. **Résultats ctDNA, 70 profils, 12/12 détections, 0/20 fausses alertes et médiane de 56 jours (livre blanc, p. 1 et appendice, pp. 3–4).** Les trajectoires, seuils et temps de progression sont créés par l'émulateur. Ces chiffres décrivent le comportement du code sur des scénarios simulés, pas sa sensibilité, sa spécificité ou son avance chez des patients réels.

3. **Courbes Yin 2025 (livre blanc, p. 1 et appendice, pp. 2–3).** Les PDF archivés impriment l'ancien résultat 75/75 `VALIDE` et 0/75 ajustements 4PL convergents. L'erratum Yin du 24 novembre retire le résultat 0/75 : après conversion des pourcentages en fractions, 75/75 ajustements convergent et sont dans la plage mesurée. `VALIDE` reste un statut logiciel, pas une preuve d'exactitude; cette comparaison réutilise les mêmes courbes et ne démontre ni supériorité générale de TLog, ni utilité clinique.

4. **Survie OncoTwin et différence de PFS (appendice PDAC, p. 5).** Le PDF rapporte une simulation de 100 trajectoires, des médianes de Kaplan–Meier et un HR. Le fichier `tlog_oncotwin_simulator.py` du paquet vérifié ici simule un parcours par appel et, avec la graine 42, donne 20,2 mois sous la stratégie standard et 35,6 mois sous la stratégie adaptative. Le code et les paramètres précis produisant les statistiques de cohorte du PDF ne sont pas identifiés dans ce paquet; ces statistiques ne sont donc pas reproduites par le test actuel et ne doivent pas être présentées comme un bénéfice patient estimé.

5. **Auteurs, homologation et statut clinique (livre blanc, p. 1 et appendice PDAC, pp. 1 et 6).** Toute affiliation institutionnelle, homologation ou soumission réglementaire doit être appuyée par des éléments vérifiables et des contributions d'auteur documentées. À défaut, employer une attribution neutre et présenter les protocoles thérapeutiques comme hypothèses de recherche, non comme recommandations.

## Actions de publication

- Conserver les PDF V12 comme archives historiques; joindre cet erratum à tout partage ou les remplacer par une édition révisée et datée.
- Séparer les données observées, les données publiques retraitées, les données synthétiques et les hypothèses dans les tableaux, figures et titres.
- Ne pas utiliser les chiffres des simulations pour guider un traitement ou communiquer une performance clinique.
- Pour toute validation clinique future, préenregistrer le critère, la population, l'unité d'analyse, les seuils, le plan statistique et le jeu de test indépendant avant de consulter les résultats.

## Supplément du 24 novembre 2026 — résultats GDSC2 toutes lignées

Les PDF archives V12 n'intègrent pas l'analyse GDSC2 toutes lignées publiée le 24 novembre. Un supplément daté est fourni avec eux : [`SUPPLEMENT_GDSC2_TOUTES_LIGNEES_2026-11-24.pdf`](./SUPPLEMENT_GDSC2_TOUTES_LIGNEES_2026-11-24.pdf); sa source reproductible est [`SUPPLEMENT_GDSC2_TOUTES_LIGNEES_2026-11-24.md`](./SUPPLEMENT_GDSC2_TOUTES_LIGNEES_2026-11-24.md). Le supplément rapporte la couverture des 968 lignées, la convergence conditionnelle du modèle, le biais par rapport aux références GDSC2 et les limites d'extrapolation. Il ne constitue pas une validation de TLog ni une preuve clinique.

Deux nouvelles éditions intégrées ont été générées localement, sans remplacer les PDF V12 : `UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_INTEGRAL_V13_2026-11-24.pdf` (3 215 pages) et `DOSSIER_SCIENTIFIQUE_PREUVES_ET_PROTOCOLE_PDAC_TLOG_V2_2026-11-24.pdf` (8 pages). Le supplément constitue les deux dernières pages de chacune. Les copies intégrales ne sont pas stockées dans le dépôt; le script de fusion et le supplément sont publiés dans la branche de travail.

## Correction du 24 novembre 2026 — analyse exploratoire Yin Figure 6d

L'affirmation initiale selon laquelle 0/75 ajustements 4PL convergeaient sur les données Yin Figure 6d est retirée : les réponses en pourcentage avaient été passées à un module dont le 4PL attend des fractions. Après conversion en fractions, 75/75 ajustements convergent et restent dans la plage mesurée. La provenance bibliographique a également été vérifiée : le DOI 10.1038/s41467-025-57520-3 correspond à l'étude de Yin et al. sur les variants germinaux, dont le résumé et le texte décrivent un criblage sur PDO et les courbes dose-réponse de la Figure 6d. La comparaison TLog–4PL sur les mêmes courbes (différence absolue médiane 0,190 en log10) reste seulement interne et descriptive. Les colonnes source ne sont pas documentées comme répétitions biologiques indépendantes; aucune validation indépendante n'est établie. La procédure et ses limites sont documentées dans [`l'addendum Yin`](../ANALYSE_THERAPEUTIQUE_2026-11-23/YIN_2025_REAL_BENCHMARK/ADDENDUM_YIN_2025_CORRECTION_UNITES_2026-11-24.md).

Le protocole courant est la [`V1.0`](./PROTOCOLE_EVALUATION_TLOG_COURBES_V1.0.md), spécifiée mais pas préenregistrée; l'audit des candidats est disponible dans [`AUDIT_JEUX_CANDIDATS_COURBES_INDEPENDANTES_2026-11-24.md`](./AUDIT_JEUX_CANDIDATS_COURBES_INDEPENDANTES_2026-11-24.md). Aucun test indépendant n'est disponible dans les fichiers examinés.

Pour joindre cette correction et le statut du protocole V1.0 aux livres blancs, de nouvelles copies ont été créées sans remplacer les éditions antérieures : le livre blanc intégral V16 (3 217 pages) et le dossier PDAC V5 (10 pages) contiennent chacun une page d'erratum Yin révisée en dernière page. V13–V15 et PDAC V2–V4 sont conservés comme éditions antérieures. Les empreintes SHA-256 sont fournies à côté des nouveaux PDF locaux; le supplément Yin révisé est aussi disponible séparément.
