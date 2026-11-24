# Erratum scientifique — livre blanc PDAC Universal Log V12

**Objet :** clarifier la portée des résultats résumés dans le livre blanc intégral V12 et dans le dossier PDAC de six pages.
**Statut :** erratum de recherche; les PDF archivés ne sont pas modifiés par cette note.

## Corrections de portée

1. **Benchmark GDSC2, `r = 0,9911` (livre blanc, pp. 1–2 et appendice PDAC, p. 2).** Les fichiers `GDSC2_PDAC_REFERENCE_CURVES.csv` inspectés sont générés par `run_gdsc2_pdac_benchmark.py` à partir d'IC50 et de pentes paramétrés dans le code, puis de bruit simulé. La corrélation mesure l'accord avec ces valeurs synthétiques intégrées au générateur; elle ne constitue pas une validation indépendante sur 675 mesures brutes de Sanger/GDSC2. Le code et les colonnes du paquet ont été renommés pour rendre cette provenance explicite.

2. **Résultats ctDNA, 70 profils, 12/12 détections, 0/20 fausses alertes et médiane de 56 jours (livre blanc, p. 1 et appendice, pp. 3–4).** Les trajectoires, seuils et temps de progression sont créés par l'émulateur. Ces chiffres décrivent le comportement du code sur des scénarios simulés, pas sa sensibilité, sa spécificité ou son avance chez des patients réels.

3. **Courbes Yin 2025, 75/75 `VALIDE` et 0/75 ajustements 4PL convergents (livre blanc, p. 1 et appendice, pp. 2–3).** `VALIDE` signifie que les règles internes du module ont produit une sortie. Le drapeau 4PL est propre à l'implémentation, aux options et aux données de cette exécution. Ces nombres ne prouvent ni l'exactitude des estimations TLog, ni une incapacité générale du 4PL, ni une supériorité clinique.

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
