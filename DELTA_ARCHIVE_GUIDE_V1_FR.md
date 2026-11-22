# Guide de reconstruction par delta

## Principe

`build_project_delta.py` compare les fichiers du dossier de projet avec les membres du snapshot V11 et crée une archive contenant les ajouts/remplacements, les déplacements détectés, les suppressions et un manifeste SHA-256. Il reconnaît aussi un PDF PyMuPDF enregistré de façon incrémentale : si le nouveau livre blanc commence octet pour octet par un PDF complet présent dans la base, le delta conserve le seul suffixe PDF et son hash. Le reconstructeur vérifie la base, crée le PDF mis à jour à partir du PDF de base, ajoute le suffixe et valide l’empreinte du PDF final.

La paire **snapshot V11 + delta V12** permet de reconstruire l’arborescence de projet incluse dans ces archives. Les environnements `.venv`, `.git`, caches et les anciens ZIP de snapshots ne sont pas copiés dans les deltas. Les snapshots historiques V4–V10 restent un lot d’archives distinct, avec leur propre traçabilité.

## Créer un delta

Après avoir terminé tous les changements V12, générer le delta final :

```powershell
.\.venv\Scripts\python.exe .\build_project_delta.py --version V12 --output .\output\deltas\DELTA_V12_YYYY-MM-DD.zip
```

Le programme refuse d’écraser une archive existante, vérifie le SHA-256 des fichiers ajoutés au delta et écrit `DELTA_MANIFEST.json` à l’intérieur du ZIP. L’outil compare la base par chemin, taille et CRC ZIP; le reconstructeur vérifie l’empreinte SHA-256 complète de la base avant extraction.

## Reconstruire le projet

Dans un dossier de destination vide :

```powershell
.\.venv\Scripts\python.exe .\reconstruct_project_from_delta.py `
  .\output\master_whitepaper_v11\UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V11_2026-11-22.zip `
  .\output\deltas\DELTA_V12_YYYY-MM-DD.zip `
  D:\UNIVERSAL_LOG_RECONSTRUCTED_V12
```

Le test de fumée `test_delta_archive_smoke.py` a vérifié un exemple isolé avec un fichier inchangé, un remplacement, un ajout, une suppression, un déplacement, une mise à jour PDF incrémentale et l’exclusion d’un ancien ZIP historique.

## Limites de taille

La taille du delta dépend des données modifiées. Une version mise à jour du livre blanc complet peut peser plusieurs centaines de Mo; des images ou fichiers de données peuvent également dépasser 30 Mo. Cette méthode évite de recopier le snapshot complet, mais ne garantit pas qu’un delta fasse toujours 5–30 Mo.

**Ne pas supprimer les snapshots V4–V10 sur la seule base de cette méthode.** Certaines entrées V4 et V6 ne sont pas identiques à V11, et les ZIP historiques conservent l’état exact des archives telles qu’elles ont été produites.
