# Protocole d'évaluation de TLog sur courbes dose-réponse

**Version :** 0.1 — 24 novembre 2026
**Statut :** version historique, remplacée par [`V1.0`](./PROTOCOLE_EVALUATION_TLOG_COURBES_V1.0.md); ne pas utiliser pour une nouvelle analyse.
**Portée :** évaluation analytique in vitro, pas une validation clinique.

V0.1 est conservée pour l'historique des décisions. Les critères en vigueur et l'audit des jeux candidats figurent dans [`PROTOCOLE_EVALUATION_TLOG_COURBES_V1.0.md`](./PROTOCOLE_EVALUATION_TLOG_COURBES_V1.0.md) et [`AUDIT_JEUX_CANDIDATS_COURBES_INDEPENDANTES_2026-11-24.md`](./AUDIT_JEUX_CANDIDATS_COURBES_INDEPENDANTES_2026-11-24.md).

## 1. Question et estimand

Sur des courbes dose-réponse courtes et indépendantes, quelle est l'erreur de l'estimation TLog du point médian de transition, en unités `log10(concentration)`, par rapport au point médian défini par une courbe de référence complète mesurée sur des réplicats biologiques indépendants?

Le point médian de transition TLog est le milieu entre les plateaux haut et bas observés, selon `compute_ic50_tlog` dans `UNIVERSAL_LOG_dose_response_v1.py`. Il n'est pas nécessairement équivalent à une concentration produisant exactement 50 % de viabilité, ni à `LN_IC50` de GDSC. Ces estimands ne seront comparés que si leur définition est explicitement harmonisée.

## 2. Population et données admissibles

- Modèles PDAC humains identifiés par un identifiant stable; composés avec identité, dose et unité vérifiées.
- Réponses de viabilité non arrondies, normalisées par plaque selon une méthode documentée, dans `[0, 1]`.
- Au moins 7 concentrations distinctes, strictement positives et ordonnées; conserver les courbes jusqu'à 20 doses pour respecter l'interface actuelle.
- Au moins 3 réplicats **biologiques indépendants** par condition et par jeu (courbe courte et référence complète). Une répétition technique ou un puits ne constitue pas un réplicat biologique.
- Pour chaque réplicat, conserver l'identifiant de l'expérience, la date, la plaque, la lignée, le composé, la dose, le résultat et les motifs d'exclusion.
- Ne pas imputer des doses ni interpoler avant l'analyse. Exclure uniquement selon des critères de qualité établis avant l'ouverture des résultats.

Le jeu de référence doit provenir d'une expérience indépendante, menée sur la même lignée et le même composé, avec une gamme de doses suffisamment dense pour observer les deux plateaux et le point médian. Il ne doit pas être construit à partir des doses utilisées comme entrée de TLog.

## 3. Séparation et verrouillage

1. Geler le code TLog, l'environnement logiciel, les règles de prétraitement, les exclusions, les métriques et la graine avant d'accéder au jeu de test. Archiver les versions et empreintes SHA-256.
2. Garder les données de développement distinctes du test final. Séparer par expérience/lot et, lorsque possible, par lignée; aucun réplicat, puits ou courbe de la même expérience ne peut traverser les partitions.
3. Le jeu test reste inaccessible à toute sélection de seuil, modification du code ou choix de métrique. Toute modification ultérieure crée une nouvelle version et requiert un nouveau jeu test.
4. Les courbes TLog courtes et les courbes de référence complètes sont mesurées sur des cultures/plaques indépendantes. Les répétitions techniques sont agrégées à l'intérieur de chaque réplicat biologique avant l'analyse.

Le jeu GDSC2 étudié précédemment n'est pas un test indépendant : ses références ajustées proviennent des mêmes expériences que les courbes brutes, les puits sont techniques, et le sous-ensemble PDAC observé ne comprend que trois lignées. Ces résultats ne serviront qu'au développement et à la vérification du pipeline; ils ne seront pas réétiquetés comme validation.

## 4. Algorithmes et analyses figés

- **Méthode testée :** `UNIVERSAL_LOG_dose_response_v1.py`, version de code et empreinte à inscrire avant l'analyse. Garder ses règles actuelles, y compris le seuil de 3 estimateurs finis sur 5 et la plage de 7 à 20 doses. Aucun réglage après consultation du test.
- **Référence :** ajustement 4PL de la courbe complète indépendante avec `sigmoid_4pl` et `fit_4pl_sigmoid` du module figé. La valeur de référence est le milieu entre les plateaux ajustés; rapporter l'incertitude et le diagnostic d'identifiabilité.
- **Comparateur :** la même fonction `fit_4pl_sigmoid` appliquée uniquement aux doses de la courbe courte. Elle évalue l'apport relatif de TLog à partir des mêmes données limitées.
- Calculer les méthodes sur les moyennes par dose des réplicats biologiques de la courbe courte; conserver aussi les résultats par réplicat. Le bootstrap, si calculé, rééchantillonne les réplicats biologiques entiers, jamais les puits ni les doses.

## 5. Seuil de 50 % et extrapolation

Pour chaque courbe courte, enregistrer séparément si les réponses observées encadrent (a) la viabilité absolue de 0,5 et (b) le point médian de transition défini par les deux premiers et deux derniers niveaux selon la fonction TLog. Ces indicateurs ne sont pas interchangeables.

Présenter trois strates préspécifiées :

1. **Point médian encadré :** les mesures courtes observées se trouvent des deux côtés du point médian TLog; l'interpolation est permise.
2. **Point médian non encadré :** le point médian n'est pas encadré par les observations; une valeur TLog de type « point le plus proche » est étiquetée comme telle et ne compte pas comme IC50 observée.
3. **Référence non identifiable ou invalide :** échec d'ajustement, absence de transition ou point médian de référence hors gamme; rapporter comme échec/abstention, sans erreur numérique artificielle.

Les courbes sans franchissement ne sont jamais supprimées du dénominateur de couverture. Toute extrapolation et toute abstention sont rapportées explicitement.

## 6. Critères et rapport statistique

**Critère principal :** erreur absolue en `log10(concentration)` entre le point médian TLog de la courbe courte et celui de la référence indépendante, parmi les paires où la référence est identifiable. Rapporter le nombre de paires et lignées, MAE, médiane de l'erreur absolue, biais signé et IC à 95 %.

**Comparaison principale :** différence appariée de MAE entre TLog et le 4PL court face à la même référence complète. Estimer l'incertitude par bootstrap groupé par lignée, et non par puits ou par courbe si plusieurs courbes viennent d'une même lignée.

**Couverture :** nombre de courbes admissibles, réussites TLog, abstentions, échecs numériques, références non identifiables et taux de couverture, chacun rapporté globalement et par lignée, composé et strate de franchissement.

**Analyses secondaires descriptives :** AUC, T0 et complexité des courbes, avec incertitude groupée par lignée. Aucune conclusion clinique, aucun classement thérapeutique et aucune affirmation de bénéfice patient ne seront tirés de ces mesures in vitro.

Le plan ne fixe pas de seuil de succès clinique. Avant toute collecte ou ouverture du jeu test, un biostatisticien indépendant devra valider le calcul de taille d'échantillon et les marges d'erreur acceptables pour l'usage analytique visé. Jusqu'à cette validation, les résultats seront descriptifs et leurs intervalles de confiance seront publiés sans dichotomiser la performance en « validée » ou « non validée ».

## 7. Journal des exclusions et publication

Publier le diagramme des données depuis leur réception jusqu'aux paires analysées; le nombre et la raison de chaque exclusion; toutes les abstentions, erreurs de convergence et résultats par strate; les versions, empreintes, paramètres et commandes d'exécution. Fournir un tableau ligne par courbe sans identifiants sensibles, les scripts et un manifeste de provenance. Ne jamais ne rapporter que les courbes ayant réussi.

## 8. Blocages actuels et prochaine action

Les fichiers actuellement disponibles dans le projet ne satisfont pas le plan pour un test indépendant : les sorties GDSC2 sont des données de développement issues d'une seule source, les références ajustées réutilisent ces expériences, et les mesures brutes ne démontrent pas la présence d'au moins trois réplicats biologiques indépendants par courbe. De plus, l'extraction détaillée tous-lignées et les tables d'ajustement sont des résultats locaux non présents dans le dépôt.

**Décision :** ne pas calculer ni annoncer une performance confirmatoire sur GDSC2 avec le matériel actuel. La prochaine étape empirique est d'obtenir une source indépendante avec les métadonnées de réplication biologique et les courbes complètes, puis de figer les empreintes, de vérifier l'admissibilité sans ouvrir les résultats, et de faire approuver la taille d'échantillon avant toute analyse du test.
