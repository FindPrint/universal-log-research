# Profil sur l'entrée de 80 lignes

Entrée: simulation Ising classique, 80 lignes, 15 colonnes. SHA-256: `b76a2ef1ddc50855baa8959714744e0764304bbe9408c6842c5596530ad9c216`.

## Exécutions réellement terminées

| Variante | Durée | Code | Note |
|---|---:|---:|---|
| v5.9.2 référence | 441,265 s | 0 | Un run complet enregistré |
| v5.9.2 répétition interrompue | 49,472 s | -1 | Pas une durée complète |
| v5.9.2 avec cProfile | 817,810 s | 0 | Instrumentation; durée non comparable directement |
| v5.9.3 division scalaire | 482,658 s | 0 | Parité des exports vérifiée; accélération globale non démontrée |
| v5.9.2, horizons `1,3,6,12` | 430,380 s | 0 | Couverture d'horizon réduite; TLog et exports clés identiques |
| v5.9.4 `--no-plots` | 776,502 s | 0 | Pas de PNG; exports clés/TLog identiques; accélération non démontrée |

Ne pas interpréter l'écart de 2,5 % du test horizons ou le temps élevé du test sans figures comme des effets établis : un seul run complet par variante et une forte variabilité rendent les comparaisons fragiles.

## Reproduction des variantes

```powershell
powershell -ExecutionPolicy Bypass -File .\audit_release\2026-11-15_pipeline_profile_baseline\sample_80\run_profile_80.ps1
powershell -ExecutionPolicy Bypass -File .\audit_release\2026-11-15_pipeline_profile_baseline\sample_80\run_cprofile_only.ps1
powershell -ExecutionPolicy Bypass -File .\audit_release\2026-11-15_pipeline_profile_baseline\sample_80\run_candidate_v5_9_3.ps1
powershell -ExecutionPolicy Bypass -File .\audit_release\2026-11-15_pipeline_profile_baseline\sample_80\run_horizons4.ps1
powershell -ExecutionPolicy Bypass -File .\audit_release\2026-11-15_pipeline_profile_baseline\sample_80\run_no_plots_v5_9_4.ps1
```

Les deux premiers scripts relancent les calculs coûteux. Les enregistrements passés sont conservés dans leurs sous-dossiers correspondants. Voir le rapport parent pour les empreintes et la portée des résultats.
