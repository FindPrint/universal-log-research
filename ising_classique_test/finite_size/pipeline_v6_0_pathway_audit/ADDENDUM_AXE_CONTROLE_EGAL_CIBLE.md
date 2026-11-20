# Addendum de configuration — contrôle identique à la cible

**Rédigé avant l'exécution du cas diagonal :** 15 novembre 2026. Il s'agit d'un essai de configuration, distinct du benchmark de localisation de Tc.

## Intention

Le pipeline se veut universel et le choix `control_col == target_col` peut correspondre à un usage légitime. Il ne doit pas être interdit par le rapport. Le logiciel doit toutefois l'indiquer clairement puisque le même flux détermine l'axe et la cible, ce qui peut rendre certaines interprétations tautologiques ou spécifiques à cette configuration.

## Essai fixé

- L=16, CSV physique complet du protocole principal, 76 lignes.
- Cible et axe de contrôle : `Energy_per_spin`.
- Mode `fast`, Cohen-d, graine 20261115, cible fixe, un worker, preset `default`, L7b `light`.
- Garder les diagnostics, alertes et messages de cas diagonal; ne pas comparer la valeur brute d'énergie à Tc ou aux pics/croisements en température.
- Comparer structure des sorties, alertes, seuil/rang et robustesse avec le run L=16 sur contrôle Temperature et cible Energy.

## Statut d'inférence

Ce test caractérise un cas d'usage universel du pipeline. Il ne contribue pas au critère Ising de localisation de Tc et ne compte pas comme réplication physique indépendante.
