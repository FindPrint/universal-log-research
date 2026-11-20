# Contrat de configuration universel — proposition v1

**Statut :** proposition de spécification pour la prochaine phase de validation. Ce document décrit les règles d'interprétation attendues; il ne prétend pas que toutes les validations ou tous les contrôles sont déjà implémentés dans v6.0.  
**Date :** 15 novembre 2026.  
**Référence logicielle auditée :** `v6.0.0-L7aL7b-CohenD`, empreinte source consignée dans `pipeline_v6_ising_manifest.json`.

## 1. But

Décrire sans restriction de domaine comment une analyse relie ses données aux rôles **flux**, **cible** et **contrôle**. Le contrat ne doit pas interdire une configuration parce qu'elle paraît inhabituelle. Il doit rendre explicites ses dépendances et limiter les interprétations que la sortie autorise.

« Universel » signifie ici que le même moteur peut recevoir plusieurs formes de flux et de contrôles, sous réserve de ses limites techniques. Cela ne signifie pas qu'une configuration, un estimateur ou une interprétation est scientifiquement valide dans tous les domaines.

## 2. Définitions opérationnelles

| Rôle | Définition à déclarer | Ce que le rôle n'implique pas à lui seul |
|---|---|---|
| **Flux** | Colonne mesurée ou construite que l'utilisateur fournit au pipeline pour analyse. | Indépendance des autres flux, causalité, pertinence ou unité connue. |
| **Cible** | Colonne choisie pour la question déclarée; le protocole précise si elle est fixe ou déterminée par la politique du pipeline. | Cible prédictive, résultat clinique ou vérité terrain, sauf déclaration explicite. |
| **Contrôle / axe** | Colonne qui ordonne, indexe ou définit la coupe de lecture des lignes. | Variable causale, variable indépendante ou axe exprimé en temps. |
| **Position T0** | Rang ou position renvoyée sur le parcours utilisé par le pipeline. | Température, temps, événement réel ou transition physique sans conversion justifiée. |
| **Vérité terrain** | Étiquette connue du générateur ou d'une expérience indépendante; conservée hors du CSV transmis au pipeline pendant les essais aveugles. | Colonne d'entrée de l'analyse. |

La même colonne peut jouer plusieurs rôles. En particulier, `cible == contrôle` est permis. Le logiciel et les rapports doivent marquer ce cas **diagonal**, conserver la sortie brute et avertir que certains contrastes peuvent être auto-référentiels. Il ne faut pas traduire automatiquement son T0 en événement physique.

Un contrôle peut aussi être transmis comme flux si l'analyse le demande. Le manifeste doit donc énumérer exactement les colonnes analysées comme flux, plutôt que déduire cette liste du nom des contrôles.

## 3. Champs proposés du manifeste

Le schéma ci-dessous est un contrat conceptuel; les noms ne sont pas présentés comme une API déjà implémentée.

```json
{
  "schema_version": "1.0",
  "analysis_id": "identifiant stable",
  "analysis_purpose": "descriptif | localisation | comparaison | autre décrit",
  "domain": "domaine déclaré par l'utilisateur",
  "input": {
    "path": "input.csv",
    "sha256": "empreinte",
    "row_unit": "unité observée par ligne",
    "order_column": "colonne ou null"
  },
  "flows": [
    {
      "column": "Energy_per_spin",
      "unit": "unité déclarée ou unknown",
      "origin": "mesuré | calculé | simulé | inconnu",
      "dependence_group": "groupe de provenance ou unknown",
      "relation_to_other_flows": "indépendant | dérivé | copie_affine | corrélé | inconnu"
    }
  ],
  "target": {"column": "Energy_per_spin", "policy": "fixed"},
  "controls": [
    {"column": "Energy_per_spin", "meaning": "axe déclaré", "direction": "auto"}
  ],
  "control_target_relation": "diagonal",
  "control_as_flow": true,
  "missing_data_policy": "à déclarer",
  "expected_event": {"coordinate": null, "known_to_pipeline": false},
  "pipeline": {
    "version": "v6.0.0-L7aL7b-CohenD",
    "source_sha256": "empreinte",
    "mode": "fast",
    "seed": 20261115,
    "l7b_mode": "light"
  }
}
```

`control_target_relation` devrait être calculé automatiquement à partir des noms de colonnes, avec une possibilité de vérification humaine. Les étiquettes de dépendance décrivent la provenance connue; le pipeline ne doit pas prétendre établir l'indépendance statistique en les lisant.

## 4. Règles d'interprétation à rendre visibles

1. **Aucun rôle n'est interdit par défaut.** Valider la présence et le type des colonnes requises; accepter explicitement les recouvrements cible/contrôle/flux.
2. **Cas diagonal.** Produire un indicateur de configuration, le nom de la colonne commune, T0 en rang et en valeur brute, et une note d'interprétation. La configuration demeure exécutable.
3. **Monotonie.** Rapporter le diagnostic, la direction, le rang et la valeur brute du contrôle. Pour un contrôle non monotone, signaler que la conversion d'un rang vers une unité brute peut être ambiguë.
4. **Dépendance entre flux.** Documenter copies, transformations, mesures dérivées ou relations inconnues. Une copie ou un flux corrélé n'est pas une confirmation indépendante.
5. **Valeurs manquantes et estimateurs indisponibles.** Garder les statuts (`calculé`, `non calculable`, `non exécuté par le profil`, `erreur`) distincts. Ne pas remplacer un NaN par zéro ni supprimer silencieusement son dénominateur.
6. **Séries courtes.** Déclarer le nombre de lignes et l'unité expérimentale. Autoriser une sortie `indéterminée` ou `non estimable`; ne pas transformer l'absence de calcul en preuve d'absence d'effet.
7. **Seuil toujours sélectionné.** Si le code renvoie T0 même sous un scénario sans événement, T0 seul ne constitue pas une décision de détection. Une règle d'alerte/abstention séparée doit être spécifiée avant de calculer un taux de faux positifs.
8. **Séparation hypothèse/résultat.** Les journaux distinguent configuration pré-déclarée, observation calculée, interprétation et décision prise après examen.

## 5. État vérifié sur v6.0 dans cet audit

- Les appels audités acceptent plusieurs axes de contrôle et un appel avec cible égale au contrôle; le test diagonal énergie L=16 a terminé.
- Le mode principal fixe la cible énergie. Les cinq axes testés à L=16 étaient température, aimantation absolue, susceptibilité, capacité calorifique et Binder.
- Les rangs ne sont pas comparables comme températures lorsque les axes diffèrent; les figures actuelles le signalent.
- L'essai diagonal a T0 = 31,657 % du parcours énergie, valeur brute −1,623109 et conversion ambiguë. Il confirme l'acceptation de cette configuration dans cet appel, pas son utilité pour localiser Tc.
- La validation générale de toutes les colonnes, types de données, valeurs manquantes, tailles d'échantillon et domaines reste à faire.

## 6. Hypothèses de conception à tester

- Un manifeste explicite rend les analyses plus faciles à reproduire et à interpréter.
- Le marquage diagonal et les statuts d'estimateurs empêchent des lectures excessives des sorties sans bloquer les usages valides.
- La pertinence des flux et les relations entre eux dépendent du domaine; elles doivent rester déclaratives et auditables, pas être inférées comme des faits par le pipeline.

Ces propositions sont des exigences de conception, pas des résultats expérimentaux.
