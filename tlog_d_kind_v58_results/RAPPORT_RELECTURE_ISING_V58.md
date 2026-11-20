# Relecture TLog typée des paysages Ising archivés (v5.8)

Cette sortie regroupe les médianes déjà présentes dans les anciens fichiers df_feat.csv selon le nouveau d_kind. Les estimateurs ne sont pas recalculés. T_log_by_d_kind conserve (d−4) ln(n) et signale chaque regroupement comme exploratoire, à calibrer par domaine.

Comparaison aux vecteurs de classe archivés : 9 cas, écart absolu maximal 0.0, correspondance exacte = True.

## Vecteurs de classe historiques et comparaisons

| Cas | Contrôle | n | d_sat | d_crit | d_div | d_null |
|---|---|---:|---:|---:|---:|---:|
| classical_temperature_sweep | Temperature | 105 | 1.275672 | 2.639726 | 2.614785 | 2.390604 |
| classical_field_sweep | Field | 105 | 1.242038 | 2.720776 | 2.564516 | 2.533476 |
| classical_tlog_profile_sweep | Temperature | 105 | 1.251936 | 2.713662 | 2.606923 | 2.412139 |
| classical_controlled_chain_0 | Temperature | 76 | 1.097791 | 1.979599 | 2.535234 | 2.219851 |
| classical_controlled_chain_1 | Temperature | 76 | 1.09414 | 1.944695 | 2.534641 | 2.219973 |
| classical_controlled_chain_2 | Temperature | 76 | 1.109257 | 1.953231 | 2.514603 | 2.254508 |
| quantum_transverse_ising_N8 | g | 81 | 1.027398 | 0.978444 | 1.619718 | 1.757298 |
| quantum_transverse_ising_N10 | g | 81 | 1.027406 | 0.961384 | 1.581818 | 1.758036 |
| quantum_transverse_ising_N12 | g | 81 | 1.027406 | 0.964456 | 1.563636 | 1.75864 |

## Profils par type

Voir le [CSV détaillé](ising_tlog_d_kind_v58.csv) et le [JSON complet](ising_tlog_d_kind_v58.json) pour les valeurs, les estimateurs utilisés, l'IQR (lorsqu'il est estimable) et les avertissements de classes hétérogènes.

Les paysages sources sont des exports antérieurs; cette relecture ne recalcule pas les trajectoires des estimateurs.
