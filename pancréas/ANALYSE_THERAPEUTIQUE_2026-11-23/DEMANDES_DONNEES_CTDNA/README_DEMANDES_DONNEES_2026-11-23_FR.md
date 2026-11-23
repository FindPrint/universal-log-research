# Dossier des Demandes d'Accès aux Données ctDNA & Organoïdes PDAC

**Date :** 23 novembre 2026  
**Auteur / Rôle :** `ctdna-requests` (Swarm Agent)  
**Projet :** Universal Log / TLog Pipeline — Détection précoce de rechute du cancer du pancréas (PDAC)  
**Répertoire GitHub public :** [https://github.com/FindPrint/universal-log-research](https://github.com/FindPrint/universal-log-research)  
**Emplacement des lettres :** `C:\Users\citys\Desktop\10-31-2026\pancréas\DEMANDES_DONNEES_CTDNA_2026-11-23\`

---

## 1. Vue d'ensemble des trois lettres finalisées

Trois lettres de demande formelle d'accès aux données de recherche (data access request) ont été rédigées en anglais académique professionnel de haut niveau, prêtes à être envoyées par le porteur du projet après personnalisation des champs d'identification :

| # | Fichier | Cible / Étude | Journal & DOI | Auteur Correspondant & Email | Type de Données Demandées |
|---|---|---|---|---|---|
| **1** | [`DEMANDE_DONNEES_KIRCHWEGER_2022_FINAL_EN.md`](./DEMANDE_DONNEES_KIRCHWEGER_2022_FINAL_EN.md) | **Kirchweger et al. (2022)** | *Frontiers in Oncology*<br>DOI: [10.3389/fonc.2022.902177](https://doi.org/10.3389/fonc.2022.902177) | **Dr. Holger Rumpold**<br>`holger.rumpold@ordensklinikum.at` | Matrice patient × visite (70 patients, prélèvements toutes les 2 semaines, MAF, copies/mL, CA19-9, RECIST 1.1) |
| **2** | [`DEMANDE_DONNEES_EDLAND_2023_FINAL_EN.md`](./DEMANDE_DONNEES_EDLAND_2023_FINAL_EN.md) | **Edland et al. (2023)** | *Molecular Oncology*<br>DOI: [10.1002/1878-0261.13472](https://doi.org/10.1002/1878-0261.13472) | **Prof. Oddmund Nordgård**<br>`oddmund.nordgard@sus.no` | Série longitudinale (81 patients, 425 échantillons de plasma toutes les 4 semaines, modèles conjoints, dates d'imagerie) |
| **3** | [`DEMANDE_DONNEES_YIN_2025_ORGANOIDS_FINAL_EN.md`](./DEMANDE_DONNEES_YIN_2025_ORGANOIDS_FINAL_EN.md) *(BONUS)* | **Yin et al. (2025)** | *Nature Communications*<br>DOI: [10.1038/s41467-025-57520-3](https://doi.org/10.1038/s41467-025-57520-3) | **Prof. Gang Jin**<br>`jingang@smmu.edu.cn`<br>*(CC: Dr. Xiaoyi Yin `jamesyin1991@hotmail.com`)* | Données brutes multi-points de criblage pharmacologique (46 organoïdes dérivés de patients × 63 médicaments, viabilité par puits) |

---

## 2. Détail des Cibles & Adresses Email Vérifiées

### Cible 1 : Kirchweger et al. (2022) — Ordensklinikum Linz (Autriche)
- **Titre de l'article :** *Prediction of response to systemic treatment by kinetics of circulating tumor DNA in metastatic pancreatic cancer*
- **Journal :** *Frontiers in Oncology*, 2022; 12:902177.
- **Engagement de partage :** *"The raw data supporting the conclusions of this article will be made available by the authors, without undue reservation."*
- **Auteur Correspondant :** Dr. Holger Rumpold, MD (Oncologie Médicale & Hématologie).
- **Email vérifié :** `holger.rumpold@ordensklinikum.at`
- **Institution :** Ordensklinikum Linz Barmherzige Schwestern, Linz, Autriche.
- **Données clés demandées :**
  - Cohorte de 70 patients (particulièrement les 32 patients avec cinétique complète et réponse connue : 12 progressions radiologiques vs 20 non-progressions).
  - Trajectoire sérielle de prélèvements toutes les 2 semaines : MAF (%) de ctDNA, copies mutées/mL, gène testé (*KRAS*), concentration totale de cfDNA, taux de CA19-9 sérique à chaque visite.
  - Catégorie de réponse radiologique RECIST 1.1 à la restadification, survie sans progression (PFS) et survie globale (OS).

### Cible 2 : Edland et al. (2023) — Stavanger University Hospital (Norvège)
- **Titre de l'article :** *Monitoring of circulating tumour DNA in advanced pancreatic ductal adenocarcinoma predicts clinical outcome and reveals disease progression earlier than radiological imaging*
- **Journal :** *Molecular Oncology*, 2023; 17(8): 1466–1478.
- **Auteur Correspondant :** Prof. Oddmund Nordgård, PhD (Département d'Hématologie et Oncologie / Département de Pathologie).
- **Email vérifié :** `oddmund.nordgard@sus.no`
- **Institution :** Stavanger University Hospital (Helse Stavanger HF), Stavanger, Norvège.
- **Données clés demandées :**
  - 81 patients avec PDAC avancé, 425 échantillons plasmatiques longitudinaux (visites toutes les 4 semaines).
  - Les 298 observations longitudinales ctDNA utilisées pour les modèles conjoints survie-biomarqueur.
  - Copies mutantes de *KRAS* par mL, MAF (%), statut qualitatif (positif/négatif), limites de détection (LoD/LoQ).
  - Délais d'avance (lead time) documentés par rapport à la progression radiologique (RECIST 1.1), suivi CA19-9, PFS, OS.

### Cible 3 (Bonus) : Yin et al. (2025) — Changhai Hospital / Naval Medical University (Chine)
- **Titre de l'article :** *Pathogenic germline variants in Chinese pancreatic adenocarcinoma patients*
- **Journal :** *Nature Communications*, 2025; 16: 2214.
- **Auteur Correspondant :** Prof. Gang Jin, MD, PhD (Chirurgie Hépato-Bilio-Pancréatique).
- **Email vérifié :** `jingang@smmu.edu.cn`
- **Premier Auteur / Contact direct :** Dr. Xiaoyi Yin, MD, PhD (`jamesyin1991@hotmail.com`).
- **Institution :** Changhai Hospital, Naval Medical University (Second Military Medical University), Shanghai, Chine.
- **Données clés demandées :**
  - Données brutes de criblage pharmacogénomique sur 46 organoïdes dérivés de patients (PDOs) testés contre 63 médicaments antinéoplasiques.
  - Valeurs brutes de réponse / viabilité cellulaire puits par puits pour chaque concentration testée ($N = 7$ à $9$ doses) plutôt que seulement les valeurs finales lissées IC50 / AUC.
  - Réplicats techniques et biologiques, témoins négatifs (DMSO) et positifs (kill control).
  - Statut génomique apparié (mutations constitutionnelles *BRCA1/2*, *PALB2*, *ATM*, *CFTR*, *RAD51D* et sous-types somatiques *KRAS*).
  - Rôle dans le pipeline : calibration du **Mode Courtes Courbes Dose-Réponse** (`UNIVERSAL_LOG_dose_response_v1.py`).

---

## 3. Éléments Clés Intégrés dans Chaque Lettre

Chaque lettre a été structurée pour maximiser le taux de réponse favorable en respectant scrupuleusement les codes de la communication académique internationale :
1. **Description claire du projet :** Présentation du cadre *UNIVERSAL_LOG / TLog* comme un pipeline d'analyse de séries multi-flux ordonnées axé sur la reproductibilité.
2. **Préenregistrement public :** Mention explicite du dépôt GitHub ouvert [https://github.com/FindPrint/universal-log-research](https://github.com/FindPrint/universal-log-research) garantissant la transparence méthodologique.
3. **Usage strictement non-commercial :** Recherche académique fondamentale et méthodologique sans but lucratif ni exploitation commerciale.
4. **Garde-fous méthodologiques stricts :** Assurance que les trajectoires des patients seront traitées individuellement (Mode Panel Hiérarchique V1) sans concaténation abusive de patients distincts.
5. **Protection des données & Éthique :** Demande de données strictement pseudonymisées (aucun identifiant direct), engagement à signer un DUA/MTA (Data Use Agreement / Material Transfer Agreement) ou à se conformer aux comités d'éthique locaux (ex. REK en Norvège).
6. **Reconnaissance scientifique :** Citations exhaustives des publications sources et proposition d'échanges collaboratifs / co-autorat si souhaité.

---

## 4. Ce que l'Utilisateur doit compléter avant envoi (`[À COMPLÉTER PAR L'UTILISATEUR]`)

Pour chaque lettre, les champs entre crochets suivants doivent être remplis avec les coordonnées institutionnelles réelles du chercheur :
- `[INVESTIGATOR NAME, MD/PhD]` : Nom complet et titres du demandeur.
- `[Academic Title / Position]` : Fonction officielle (ex. Professor, Senior Postdoctoral Researcher, Principal Investigator).
- `[Laboratory / Department Name]` : Nom du laboratoire ou service de rattachement.
- `[Institution / University]` : Nom de l'université, hôpital ou institut de recherche.
- `[Institutional Address]` : Adresse postale professionnelle.
- `[Institutional Email Address]` : Adresse email professionnelle (domaine `.edu`, `.org`, hôpital ou université).
- `[Institutional Telephone Number]` : Numéro de téléphone professionnel.
- `[ORCID]` : Identifiant ORCID du chercheur.
