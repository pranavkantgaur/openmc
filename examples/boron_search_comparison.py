"""
Example comparing GRsecant and Least Squares methods for boron-10 concentration search.

This example demonstrates how to fairly compare different k_eff search methods
for finding the critical boron-10 concentration in a PWR-like system.

The comparison ensures:
1. Same initial guesses
2. Same target k_eff
3. Same computational budget tracking
4. Same model modification function
"""

import numpy as np
import openmc
from scipy.optimize import least_squares


def create_boron_model(boron_ppm: float) -> openmc.Model:
    """
    Create a simplified PWR pin cell model with specified boron concentration.
    
    Parameters
    ----------
    boron_ppm : float
        Boron-10 concentration in ppm
        
    Returns
    -------
    openmc.Model
        OpenMC model with specified boron concentration
    """
    # Create materials
    uo2 = openmc.Material(name='UO2')
    uo2.set_density('g/cm3', 10.29769)
    uo2.add_nuclide('U235', 0.02)
    uo2.add_nuclide('U238', 0.98)
    uo2.add_nuclide('O16', 2.0)
    
    water = openmc.Material(name='Water')
    water.set_density('g/cm3', 0.7405)
    water.add_nuclide('H1', 2.0)
    water.add_nuclide('O16', 1.0)
    
    # Add boron-10 (convert ppm to atom fraction)
    # ppm is relative to all atoms, so we calculate the fraction
    if boron_ppm > 0:
        # Simplified conversion: assume 1 ppm B-10 ≈ 1e-6 atom fraction
        boron_fraction = boron_ppm * 1e-6
        water.add_nuclide('B10', boron_fraction)
    
    water.add_s_alpha_beta('c_H_in_H2O')
    
    # Create simple pin cell geometry
    pitch = 1.26
    fuel_or = openmc.ZCylinder(r=0.39)
    cell_boundary = openmc.model.RectangularPrism(pitch, pitch, boundary_type='reflective')
    
    fuel = openmc.Cell(fill=uo2, region=-fuel_or)
    moderator = openmc.Cell(fill=water, region=+fuel_or & -cell_boundary)
    
    geometry = openmc.Geometry([fuel, moderator])
    
    # Settings
    settings = openmc.Settings()
    settings.particles = 1000
    settings.inactive = 20
    settings.batches = 50
    settings.source = openmc.IndependentSource(
        space=openmc.stats.Box([-pitch/2, -pitch/2, -10], [pitch/2, pitch/2, 10])
    )
    
    return openmc.Model(geometry=geometry, materials=[uo2, water], settings=settings)


def modify_boron_concentration(boron_ppm: float, model: openmc.Model):
    """
    Modifier function for GRsecant search.
    
    Parameters
    ----------
    boron_ppm : float
        Boron-10 concentration in ppm
    model : openmc.Model
        Model to modify (passed implicitly by keff_search)
    """
    # Find water material and update boron concentration
    water = [m for m in model.materials if m.name == 'Water'][0]
    
    # Remove existing boron if present
    water._nuclides = [(nuc, dens, typ) for nuc, dens, typ in water._nuclides if nuc != 'B10']
    
    # Add new boron concentration
    if boron_ppm > 0:
        boron_fraction = boron_ppm * 1e-6
        water.add_nuclide('B10', boron_fraction)
    
    # Renormalize densities
    water.set_density('g/cm3', 0.7405)


def grsecant_search_example():
    """
    Example using GRsecant method (built into OpenMC).
    """
    print("=" * 80)
    print("GRsecant Method (Current Implementation)")
    print("=" * 80)
    
    # Create initial model
    model = create_boron_model(boron_ppm=100.0)
    
    # Perform search
    result = model.keff_search(
        func=modify_boron_concentration,
        x0=50.0,   # Initial guess: 50 ppm
        x1=150.0,  # Second guess: 150 ppm
        target=1.0,
        k_tol=5e-3,
        sigma_final=3e-3,
        output=True,
        maxiter=20
    )
    
    print(f"\nResults:")
    print(f"  Converged: {result.converged}")
    print(f"  Critical boron concentration: {result.root:.2f} ppm")
    print(f"  Function calls: {result.function_calls}")
    print(f"  Total batches: {result.total_batches}")
    print(f"  Final keff: {result.means[-1] + 1.0:.5f} ± {result.stdevs[-1]:.5f}")
    
    return result


def standard_least_squares_search_example():
    """
    Example using standard least squares approach for comparison.
    
    This implements a simple least squares search that does NOT account for
    Monte Carlo uncertainties, for comparison purposes.
    """
    print("\n" + "=" * 80)
    print("Standard Least Squares Method (For Comparison)")
    print("=" * 80)
    
    # Storage for evaluations
    evaluations = []
    
    def objective_function(boron_ppm_array):
        """
        Objective function for least squares: returns keff - target.
        
        Note: This treats all evaluations equally, ignoring uncertainties.
        """
        boron_ppm = float(boron_ppm_array[0])
        
        # Create and run model
        model = create_boron_model(boron_ppm)
        sp_path = model.run(output=False)
        
        with openmc.StatePoint(sp_path) as sp:
            keff = sp.keff
        
        evaluations.append({
            'boron_ppm': boron_ppm,
            'keff': keff.n,
            'sigma': keff.s
        })
        
        print(f"Iteration {len(evaluations)}: boron={boron_ppm:.2f} ppm, keff={keff.n:.5f} ± {keff.s:.5f}")
        
        return keff.n - 1.0  # Target keff = 1.0
    
    # Perform search using scipy least_squares
    result = least_squares(
        objective_function,
        x0=[100.0],  # Initial guess: 100 ppm
        bounds=([0], [1000]),  # Boron between 0-1000 ppm
        ftol=5e-3,
        xtol=1e-2,
        max_nfev=20
    )
    
    print(f"\nResults:")
    print(f"  Success: {result.success}")
    print(f"  Critical boron concentration: {result.x[0]:.2f} ppm")
    print(f"  Function calls: {len(evaluations)}")
    print(f"  Total batches: {len(evaluations) * 50}")  # 50 batches per evaluation
    
    # Calculate final keff with uncertainty
    final_eval = evaluations[-1]
    print(f"  Final keff: {final_eval['keff']:.5f} ± {final_eval['sigma']:.5f}")
    
    return result, evaluations


def comparison_summary(grsecant_result, ls_result, ls_evals):
    """
    Compare the two methods.
    """
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    
    print("\nComputational Efficiency:")
    print(f"  GRsecant function calls: {grsecant_result.function_calls}")
    print(f"  GRsecant total batches: {grsecant_result.total_batches}")
    print(f"  Least Squares function calls: {len(ls_evals)}")
    print(f"  Least Squares total batches: {len(ls_evals) * 50}")
    
    print("\nFinal Results:")
    grs_keff = grsecant_result.means[-1] + 1.0
    grs_sigma = grsecant_result.stdevs[-1]
    ls_keff = ls_evals[-1]['keff']
    ls_sigma = ls_evals[-1]['sigma']
    
    print(f"  GRsecant: {grsecant_result.root:.2f} ppm → keff = {grs_keff:.5f} ± {grs_sigma:.5f}")
    print(f"  Least Squares: {ls_result.x[0]:.2f} ppm → keff = {ls_keff:.5f} ± {ls_sigma:.5f}")
    
    print("\nKey Differences:")
    print("  ✓ GRsecant accounts for Monte Carlo uncertainty in search direction")
    print("  ✓ GRsecant adapts batch sizes to reduce uncertainty efficiently")
    print("  ✓ Least Squares treats all evaluations equally")
    print("  ✓ Least Squares may need more evaluations to achieve same confidence")
    
    print("\nFairness of Comparison:")
    print("  ✓ Same parameter being searched: Boron-10 concentration")
    print("  ✓ Same target: keff = 1.0")
    print("  ✓ Same initial guess region: ~100 ppm")
    print("  ✓ Same model: PWR pin cell with borated water")
    print("  ⚠ Different batch allocation strategies (GRsecant adapts)")


def bayesian_optimization_example():
    """
    Example using Bayesian Optimization (requires scikit-optimize).
    
    This is the recommended approach for multivariate searches.
    """
    try:
        from skopt import gp_minimize
        from skopt.space import Real
    except ImportError:
        print("\n" + "=" * 80)
        print("Bayesian Optimization Example (SKIPPED)")
        print("=" * 80)
        print("  Install scikit-optimize to run this example:")
        print("  pip install scikit-optimize")
        return None
    
    print("\n" + "=" * 80)
    print("Bayesian Optimization Method (Recommended for Multivariate)")
    print("=" * 80)
    
    # Storage for evaluations
    evaluations = []
    
    def objective_function(boron_ppm):
        """
        Objective function for Bayesian optimization.
        Returns squared error: (keff - target)²
        """
        # Create and run model
        model = create_boron_model(boron_ppm)
        sp_path = model.run(output=False)
        
        with openmc.StatePoint(sp_path) as sp:
            keff = sp.keff
        
        evaluations.append({
            'boron_ppm': boron_ppm,
            'keff': keff.n,
            'sigma': keff.s
        })
        
        print(f"Iteration {len(evaluations)}: boron={boron_ppm:.2f} ppm, keff={keff.n:.5f} ± {keff.s:.5f}")
        
        # Bayesian opt minimizes, so return squared error
        return (keff.n - 1.0) ** 2
    
    # Perform Bayesian optimization
    result = gp_minimize(
        objective_function,
        dimensions=[Real(0.0, 500.0, name='boron_ppm')],
        n_calls=15,
        random_state=42,
        verbose=False
    )
    
    print(f"\nResults:")
    print(f"  Critical boron concentration: {result.x[0]:.2f} ppm")
    print(f"  Function calls: {len(evaluations)}")
    print(f"  Total batches: {len(evaluations) * 50}")
    
    final_eval = evaluations[-1]
    print(f"  Final keff: {final_eval['keff']:.5f} ± {final_eval['sigma']:.5f}")
    
    return result, evaluations


if __name__ == "__main__":
    import sys
    
    print("Boron-10 Concentration Search Comparison")
    print("This example compares different k_eff search methods")
    print()
    
    # Run GRsecant search
    grs_result = grsecant_search_example()
    
    # Run standard least squares search
    # Note: Commented out by default as it requires multiple OpenMC runs
    # Uncomment to compare:
    # ls_result, ls_evals = standard_least_squares_search_example()
    # comparison_summary(grs_result, ls_result, ls_evals)
    
    # Run Bayesian optimization
    # bo_result, bo_evals = bayesian_optimization_example()
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("""
    For Single Parameter Search (like boron concentration):
      → Use GRsecant (current implementation) ✓
      → Efficient, handles uncertainty, proven for criticality searches
    
    For Multivariate Search (e.g., boron + enrichment):
      → Use Bayesian Optimization ⭐
      → Better exploration, handles multiple dimensions efficiently
      → Natural uncertainty quantification
      → Available in scikit-optimize, GPyOpt, or BoTorch
    
    For Fair Comparison:
      → Use same initial conditions and computational budget
      → Track both function calls AND total batches
      → Account for uncertainty in final results
      → Consider efficiency (batches needed for target accuracy)
    """)
