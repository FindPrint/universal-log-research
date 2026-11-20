from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit

@njit
def one_run(L, temp, field, n_burn, n_sample, seed):
    np.random.seed(seed)
    spins = np.where(np.random.random((L, L)) < 0.5, -1, 1).astype(np.int8)
    n = L * L
    e_acc = 0.0
    m_acc = 0.0
    absm_acc = 0.0
    for sweep in range(n_burn + n_sample):
        for _ in range(n):
            i = np.random.randint(0, L)
            j = np.random.randint(0, L)
            s = spins[i, j]
            nn = spins[(i + 1) % L, j] + spins[(i - 1) % L, j] + spins[i, (j + 1) % L] + spins[i, (j - 1) % L]
            delta_e = 2.0 * s * (nn + field)
            if delta_e <= 0.0 or np.random.random() < np.exp(-delta_e / temp):
                spins[i, j] = -s
        if sweep >= n_burn:
            magnet = 0.0
            energy = 0.0
            for i in range(L):
                for j in range(L):
                    s = spins[i, j]
                    magnet += s
                    energy += -s * (spins[(i + 1) % L, j] + spins[i, (j + 1) % L]) - field * s
            m = magnet / n
            e_acc += energy / n
            m_acc += m
            absm_acc += abs(m)
    return e_acc / n_sample, m_acc / n_sample, absm_acc / n_sample

root = Path(__file__).resolve().parent
L, burn, sample = 16, 250, 30
reps = 3
rows_T = []
for ti, temp in enumerate(np.linspace(1.5, 4.0, 35)):
    for rep in range(reps):
        energy, magnet, abs_magnet = one_run(L, float(temp), 0.0, burn, sample, 10000 + ti * reps + rep)
        rows_T.append({"Temperature": temp, "Energy_per_spin": energy,
                       "Magnetization": magnet, "Abs_magnetization": abs_magnet})
pd.DataFrame(rows_T).to_csv(root / "ising_temperature_sweep.csv", index=False)

rows_H = []
tc = 2.269185314213022
for hi, field in enumerate(np.linspace(-0.6, 0.6, 35)):
    for rep in range(reps):
        energy, magnet, abs_magnet = one_run(L, tc, float(field), burn, sample, 20000 + hi * reps + rep)
        rows_H.append({"Field": field, "Energy_per_spin": energy,
                       "Magnetization": magnet, "Abs_magnetization": abs_magnet})
pd.DataFrame(rows_H).to_csv(root / "ising_field_sweep.csv", index=False)
print(f"Wrote {len(rows_T)} temperature observations and {len(rows_H)} field observations; L={L}, burn={burn}, sample={sample}, replicas={reps}.")
