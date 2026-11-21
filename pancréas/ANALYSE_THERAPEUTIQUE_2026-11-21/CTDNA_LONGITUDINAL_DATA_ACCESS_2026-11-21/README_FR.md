# Piste données longitudinales ctDNA — PDAC

Ce dossier documente une étude prospective de ctDNA dans le PDAC, son adéquation aux analyses UNIVERSAL_LOG et les étapes nécessaires avant un calcul. Il sépare les faits tirés de la publication, les décisions de protocole et les éléments encore inconnus.

**État actuel :** audit documentaire terminé; aucune matrice patient × prélèvement brute n'est disponible dans le projet; aucun appel complet à `run_pipeline` n'a été effectué sur cette étude. La demande de données ci-jointe est un brouillon et n'a pas été envoyée.

## Fichiers

- `AUDIT_ACCES_DONNEES_FR.md` : structure de l'étude, disponibilité et décision de faisabilité.
- `PROTOCOLE_ANALYSE_AXE_FLUX_FR.md` : protocole à appliquer après accès aux données.
- `BROUILLON_DEMANDE_DONNEES_EN.md` : modèle anglais à relire et personnaliser; non envoyé.
- `DATA_FIT_DECISION.csv` : statut synthétique des données.
- `SOURCE_REGISTER.json` : référence et empreintes des sources documentaires utilisées.

## Règle centrale de configuration

À chaque passage, le contrôle sélectionné est exclu des flux de ce passage. Toutes les colonnes de mesure numériques admissibles sont examinées comme contrôles candidats, même non monotones. Les colonnes de texte/catégorie ne sont pas numérisées par commodité. Les séries par patient ne sont pas concaténées en une chronologie artificielle.
