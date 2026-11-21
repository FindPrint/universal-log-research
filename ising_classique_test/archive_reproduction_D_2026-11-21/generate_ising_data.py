# -*- coding: utf-8 -*-
"""
Générateur de données du modèle Ising 2D pour tester le pipeline d'analyse de complexité.

Ce script simule un modèle Ising 2D sur réseau carré avec une transition de phase
à la température critique Tc ≈ 2.269 (J/kB = 1).

Les observables générées sont compatibles avec le pipeline pipeline_autonome.py.
"""

import numpy as np
import pandas as pd
from tqdm import tqdm

def metropolis_step(spins, T, J=1.0):
    """Une étape de Monte Carlo avec l'algorithme de Metropolis."""
    L = spins.shape[0]
    for _ in range(L * L):
        # Choisir un site aléatoire
        i, j = np.random.randint(0, L, 2)
        
        # Calculer le changement d'énergie
        s = spins[i, j]
        neighbors = spins[(i+1)%L, j] + spins[(i-1)%L, j] + spins[i, (j+1)%L] + spins[i, (j-1)%L]
        dE = 2 * J * s * neighbors
        
        # Critère de Metropolis
        if dE < 0 or np.random.random() < np.exp(-dE / T):
            spins[i, j] *= -1
    
    return spins

def compute_observables(spins, J=1.0):
    """Calcule les observables du système."""
    L = spins.shape[0]
    
    # Magnétisation par spin
    magnetization = np.sum(spins) / (L * L)
    
    # Énergie par spin
    energy = 0
    for i in range(L):
        for j in range(L):
            neighbors = spins[(i+1)%L, j] + spins[i, (j+1)%L]
            energy += -J * spins[i, j] * neighbors
    energy /= (L * L)
    
    return magnetization, energy

def simulate_ising_2d(L=32, T_min=1.0, T_max=4.0, n_temps=200, n_thermal=1000, n_measure=100):
    """
    Simule le modèle Ising 2D sur une plage de températures.
    
    Paramètres:
    - L: Taille du réseau (L×L)
    - T_min, T_max: Plage de températures
    - n_temps: Nombre de températures
    - n_thermal: Étapes de thermalisation
    - n_measure: Étapes de mesure par température
    """
    temperatures = np.linspace(T_min, T_max, n_temps)
    
    data = {
        'Progress': [],
        'Temperature': [],
        'Magnetization': [],
        'Energy': [],
        'Abs_Magnetization': [],
        'Magnetization_Squared': [],
        'Energy_Squared': []
    }
    
    # Initialiser l'état aléatoire
    spins = np.random.choice([-1, 1], size=(L, L))
    
    print(f"Simulation Ising 2D (L={L}×{L}) sur {n_temps} températures...")
    
    for idx, T in enumerate(tqdm(temperatures, desc="Simulation")):
        # Thermalisation
        for _ in range(n_thermal):
            spins = metropolis_step(spins, T)
        
        # Mesures
        magnetizations = []
        energies = []
        
        for _ in range(n_measure):
            spins = metropolis_step(spins, T)
            mag, eng = compute_observables(spins)
            magnetizations.append(mag)
            energies.append(eng)
        
        # Statistiques
        avg_mag = np.mean(magnetizations)
        avg_energy = np.mean(energies)
        avg_abs_mag = np.mean(np.abs(magnetizations))
        avg_mag_sq = np.mean(np.array(magnetizations)**2)
        avg_energy_sq = np.mean(np.array(energies)**2)
        
        # Progress (0-100) pour le pipeline
        progress = (idx / (n_temps - 1)) * 100
        
        data['Progress'].append(progress)
        data['Temperature'].append(T)
        data['Magnetization'].append(avg_mag)
        data['Energy'].append(avg_energy)
        data['Abs_Magnetization'].append(avg_abs_mag)
        data['Magnetization_Squared'].append(avg_mag_sq)
        data['Energy_Squared'].append(avg_energy_sq)
    
    return pd.DataFrame(data)

def generate_robust_dataset(output_file='ising_2d_data.csv', L=32, n_temps=200):
    """Génère un jeu de données robuste du modèle Ising 2D."""
    
    print("=" * 60)
    print("GÉNÉRATION DE DONNÉES ISING 2D")
    print("=" * 60)
    print(f"Taille du réseau: {L}×{L}")
    print(f"Nombre de températures: {n_temps}")
    print(f"Température critique théorique: Tc ≈ 2.269")
    print(f"Fichier de sortie: {output_file}")
    print("=" * 60)
    
    # Simulation avec paramètres robustes
    df = simulate_ising_2d(
        L=L,
        T_min=1.0,
        T_max=4.0,
        n_temps=n_temps,
        n_thermal=2000,  # Thermalisation plus longue
        n_measure=200    # Plus de mesures par température
    )
    
    # Calculer les dérivées pour enrichir les données
    df['Magnetization_Diff'] = np.diff(df['Magnetization'], prepend=df['Magnetization'].iloc[0])
    df['Energy_Diff'] = np.diff(df['Energy'], prepend=df['Energy'].iloc[0])
    
    # Ajouter du bruit réaliste
    noise_level = 0.01
    for col in ['Magnetization', 'Energy', 'Abs_Magnetization']:
        df[col] += np.random.normal(0, noise_level * np.std(df[col]), len(df))
    
    # Sauvegarder
    df.to_csv(output_file, index=False)
    
    print(f"\n✓ Données sauvegardées dans: {output_file}")
    print(f"✓ Nombre de points: {len(df)}")
    print(f"✓ Colonnes: {list(df.columns)}")
    print(f"\nPour utiliser avec le pipeline:")
    print(f"  python pipeline_autonome.py --input {output_file} --output results")
    
    return df

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Générer des données du modèle Ising 2D')
    parser.add_argument('--output', '-o', type=str, default='ising_2d_data.csv',
                        help='Fichier CSV de sortie')
    parser.add_argument('--size', '-L', type=int, default=32,
                        help='Taille du réseau (défaut: 32)')
    parser.add_argument('--temps', '-n', type=int, default=200,
                        help='Nombre de températures (défaut: 200)')
    
    args = parser.parse_args()
    
    generate_robust_dataset(
        output_file=args.output,
        L=args.size,
        n_temps=args.temps
    )
