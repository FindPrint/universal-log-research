# Portée de publication V12

**État provisoire :** V12 est en cours de constitution. AI4I est terminé; la rotation Bike est partielle; Air Quality est audité et préparé, mais sa rotation pipeline n'a pas commencé. Ce document ne doit pas être lu comme une annonce de campagne terminée.

## Inclus dans le dépôt public

- source v6.0.1 utilisée, scripts reproductibles, environnements de benchmark et protocoles;
- CSV publics AI4I 2020 et Bike Sharing, avec attribution/licence et empreintes;
- audits, protocoles et scripts Air Quality; les fichiers bruts Air Quality restent exclus de GitHub et du PDF;
- métriques prédictives, prédictions de test sélectionnées, rapports synthétiques, résumés expurgés des chemins locaux et graphiques;
- cadre à trois niveaux, journal V12, audit d’archives rendu public sans chemins absolus, outils delta et test de reconstruction.

## Conservé dans les archives locales

- le PDF maître complet et son SHA-256;
- le snapshot complet V11 et le delta V12;
- les sorties complètes par appel, journaux locaux et résultats binaires de profilage;
- les snapshots historiques V4–V10 et leurs copies de sauvegarde sur D:.

Les exclusions évitent de versionner un PDF et des snapshots de plusieurs gigaoctets ou des journaux contenant des chemins `C:\Users\...`. Les sorties détaillées demeurent dans le dossier local complet, le livre blanc et l’archive reconstructible; elles ne sont pas supprimées. Le ZIP n’est pas inclus dans le PDF.

## Licence et prudence

Code du projet : MIT. Documentation et résultats produits : CC BY 4.0. Chaque jeu tiers conserve ses conditions. AI4I est synthétique; Bike Sharing est publié sous CC BY 4.0. La page UCI Air Quality affiche CC BY 4.0 et indique également un usage de recherche uniquement, non commercial; le CSV brut reste exclu tant que ce libellé n'est pas clarifié. Les résultats ne valident aucune affirmation clinique, causale ou d’universalité.
