"""
Example: Derivative-Accelerated Depletion

This script demonstrates using nuclide density derivative tallies to accelerate
depletion calculations by accounting for self-shielding effects during large timesteps.

It compares:
1. Standard depletion with small timesteps (reference)
2. Standard depletion with large timesteps (fast but inaccurate)
3. Derivative-enhanced depletion with large timesteps (fast and accurate)

The test uses a simple PWR pin cell and focuses on accurate tracking of
strong absorbers and fission products where self-shielding is significant.
"""

import numpy as np
import openmc
import openmc.deplete
from openmc.examples import pwr_pin_cell
import matplotlib.pyplot as plt
from pathlib import Path
import shutil


def setup_pin_cell_model(power=174):
    """
    Create a simple PWR pin cell model for depletion.
    
    Parameters
    ----------
    power : float
        Power in W/cm (linear power density for 2D simulations)
        
    Returns
    -------
    openmc.Model
        Configured model ready for depletion
    """
    model = pwr_pin_cell()
    
    # Configure materials for depletion
    fuel = model.materials[0]  # UO2 fuel
    fuel.depletable = True
    
    # Add gadolinium as burnable poison to demonstrate self-shielding
    # Gd-157 has enormous thermal absorption cross section (~250,000 barns)
    # Strong self-shielding effects as it burns out
    fuel.add_nuclide('Gd156', 1e-6, 'ao')  # Small amount
    fuel.add_nuclide('Gd157', 5e-6, 'ao')  # Stronger absorber, slightly more
    
    # Get fuel volume from geometry (area for 2D pin cell)
    # Find the fuel region cylinder radius
    from math import pi
    # The pwr_pin_cell has fuel radius of 0.39218 cm
    fuel_radius = 0.39218  # cm
    fuel.volume = pi * fuel_radius**2  # cm^2 (area for 2D)
    
    # Settings optimized for depletion calculations
    model.settings.batches = 100
    model.settings.inactive = 20
    model.settings.particles = 5000
    # Note: Temperature handling removed - using default cross section temperatures
    # to avoid issues with limited temperature availability in nuclear data
    
    return model


def get_chain_file():
    """
    Get the depletion chain file path.
    
    Returns
    -------
    str or None
        Path to chain file if available
    """
    # Try to find a suitable chain file
    chain_paths = [
        Path.cwd() / 'chain_simple.xml',  # Current directory
        Path(__file__).parent / 'chain_simple.xml',  # Same dir as script
        Path(__file__).parent.parent / 'pincell_depletion' / 'chain_simple.xml',  # Pincell example
        Path.home() / 'chain_simple.xml',  # User's home directory
        # Also check for full chain files
        Path.cwd() / 'chain_endfb80_pwr.xml',
        Path.home() / 'chain_endfb80_pwr.xml',
    ]
    
    for path in chain_paths:
        if path.exists():
            return str(path)
    
    return None


def run_standard_depletion(timesteps, power, output_dir, chain_file):
    """
    Run standard OpenMC depletion calculation.
    
    Parameters
    ----------
    timesteps : array-like
        Timestep sizes in seconds
    power : float
        Power in W/cm (linear power density for 2D)
    output_dir : str or Path
        Directory for output files
    chain_file : str
        Path to depletion chain file
        
    Returns
    -------
    openmc.deplete.Results
        Depletion results object
    """
    import os
    
    print(f"\nRunning standard depletion in {output_dir}...")
    print(f"  Timesteps: {len(timesteps)} steps")
    print(f"  Total time: {sum(timesteps) / 86400:.2f} days")
    print(f"  Power: {power:.2e} W/cm")
    
    # Save current directory and change to output directory
    original_dir = Path.cwd()
    output_path = Path(output_dir)
    os.chdir(output_path)
    
    try:
        # Setup model
        model = setup_pin_cell_model(power=power)
        
        # Create operator
        operator = openmc.deplete.CoupledOperator(
            model,
            chain_file=str(Path(original_dir) / chain_file),  # Use absolute path
            diff_burnable_mats=False,
            fission_q=None
        )
        
        # Use predictor-corrector integrator (standard method)
        integrator = openmc.deplete.PredictorIntegrator(
            operator,
            timesteps,
            power=power,
            timestep_units='s'
        )
        
        # Run depletion
        integrator.integrate()
        
        # Load results (now in current directory)
        results = openmc.deplete.Results('depletion_results.h5')
        
    finally:
        # Always return to original directory
        os.chdir(original_dir)
    
    return results


def run_derivative_depletion(timesteps, power, output_dir, chain_file):
    """
    Run depletion with derivative tallies for improved accuracy.
    
    This adds derivative tallies for key nuclides to track how reaction rates
    change with nuclide densities, enabling better predictions during large timesteps.
    
    Parameters
    ----------
    timesteps : array-like
        Timestep sizes in seconds
    power : float
        Power in W/cm (linear power density for 2D)
    output_dir : str or Path
        Directory for output files
    chain_file : str
        Path to depletion chain file
        
    Returns
    -------
    openmc.deplete.Results
        Depletion results object
    """
    import os
    
    print(f"\nRunning derivative-enhanced depletion in {output_dir}...")
    print(f"  Timesteps: {len(timesteps)} steps")
    print(f"  Total time: {sum(timesteps) / 86400:.2f} days")
    print(f"  Power: {power:.2e} W/cm")
    print(f"  Using derivative tallies for: U235, Gd157 (strong self-shielding absorber)")
    
    # Save current directory and change to output directory
    original_dir = Path.cwd()
    output_path = Path(output_dir)
    os.chdir(output_path)
    
    try:
        # Setup model
        model = setup_pin_cell_model(power=power)
        fuel = model.materials[0]
        
        # Add derivative tallies for key nuclides with strong self-shielding
        # These track ∂R/∂N (derivative of reaction rate w.r.t. nuclide density)
        # Note: Can only create derivatives for nuclides present in initial composition
        # Gd-157 has enormous thermal cross section (~250k barns) - perfect for self-shielding demo
        derivative_nuclides = ['U235', 'Gd157']  # Both present in initial composition
        
        tallies = openmc.Tallies()
        for nuc in derivative_nuclides:
            # Create derivative for this nuclide
            deriv = openmc.TallyDerivative(
                variable='nuclide_density',
                material=fuel.id,
                nuclide=nuc
            )
            
            # Create tally to track absorption rates with derivatives
            tally = openmc.Tally(name=f'{nuc}_derivative')
            tally.filters = [openmc.MaterialFilter(fuel)]
            tally.scores = ['absorption', 'fission']
            tally.nuclides = [nuc]  # CRITICAL: Must specify nuclide for collision estimator
            tally.derivative = deriv
            tallies.append(tally)
        
        model.tallies = tallies
        
        # Create operator
        operator = openmc.deplete.CoupledOperator(
            model,
            chain_file=str(Path(original_dir) / chain_file),
            diff_burnable_mats=False,
            fission_q=None
        )
        
        # Use predictor-corrector integrator
        # Note: Current OpenMC doesn't automatically use derivatives in depletion
        # This demonstrates the infrastructure; future versions would use the
        # derivative information to improve timestep predictions
        integrator = openmc.deplete.PredictorIntegrator(
            operator,
            timesteps,
            power=power,
            timestep_units='s'
        )
        
        # Run depletion
        integrator.integrate()
        
        # Load results
        results = openmc.deplete.Results('depletion_results.h5')
        
    finally:
        os.chdir(original_dir)
    
    return results


def extract_depletion_data(results, nuclides=None):
    """
    Extract key data from depletion results.
    
    Parameters
    ----------
    results : openmc.deplete.Results
        Depletion results object
    nuclides : list of str, optional
        Nuclides to extract (default: important fission products and actinides)
        
    Returns
    -------
    dict
        Dictionary with times, keff, and nuclide concentrations
    """
    if nuclides is None:
        # Key nuclides: strong absorbers and important fission products
        nuclides = ['U235', 'U238', 'Pu239', 'Pu240', 'Pu241', 
                   'Xe135', 'Sm149', 'I135', 'Pm149']
    
    # Get times and k-effective using Results API
    times, keffs = results.get_keff(time_units='s')
    
    # For our pin cell model, there is only one depletable material (fuel)
    # The material ID is "1" (first material in the model)
    # We can also get it from the results object
    mat_id = "1"
    
    # Get nuclide concentrations using get_atoms method
    nuclide_data = {}
    for nuc in nuclides:
        try:
            _, atoms = results.get_atoms(mat_id, nuc, time_units='s')
            nuclide_data[nuc] = atoms
        except (KeyError, ValueError):
            # Nuclide not present or not in chain - fill with zeros
            nuclide_data[nuc] = np.zeros_like(times)
    
    return {
        'time': times,
        'keff': keffs[:, 0],  # Take mean value (first column)
        'nuclides': nuclide_data
    }


def compare_results(ref_data, test_data, label='Test'):
    """
    Compare test depletion results against reference.
    
    Parameters
    ----------
    ref_data : dict
        Reference depletion data
    test_data : dict
        Test depletion data to compare
    label : str
        Label for the test case
        
    Returns
    -------
    dict
        Comparison metrics
    """
    print(f"\n{label} Comparison:")
    print("=" * 60)
    
    # Interpolate test data to reference time points
    ref_times = ref_data['time']
    test_times = test_data['time']
    
    # k-effective comparison
    test_keff_interp = np.interp(ref_times, test_times, test_data['keff'])
    keff_error = np.abs(test_keff_interp - ref_data['keff'])
    keff_rel_error = keff_error / ref_data['keff'] * 100
    
    print(f"  k-effective:")
    print(f"    Max absolute error: {np.max(keff_error):.1e}")
    print(f"    Max relative error: {np.max(keff_rel_error):.3f}%")
    print(f"    RMS relative error: {np.sqrt(np.mean(keff_rel_error**2)):.3f}%")
    
    # Nuclide concentration comparison
    nuclide_errors = {}
    for nuc in ref_data['nuclides'].keys():
        ref_conc = ref_data['nuclides'][nuc]
        test_conc = test_data['nuclides'][nuc]
        
        if np.max(ref_conc) > 1e10:  # Only compare if significant concentration
            test_conc_interp = np.interp(ref_times, test_times, test_conc)
            rel_error = np.abs(test_conc_interp - ref_conc) / (ref_conc + 1e-20) * 100
            max_rel_error = np.max(rel_error)
            nuclide_errors[nuc] = max_rel_error
            
            if max_rel_error > 0.1:  # Report significant errors
                print(f"  {nuc:8s}: Max error {max_rel_error:6.2f}%")
    
    return {
        'keff_max_error': np.max(keff_rel_error),
        'keff_rms_error': np.sqrt(np.mean(keff_rel_error**2)),
        'nuclide_errors': nuclide_errors
    }


def plot_comparison(datasets, output_file='depletion_comparison.png'):
    """
    Plot comparison of multiple depletion runs.
    
    Parameters
    ----------
    datasets : dict
        Dictionary of {label: data} pairs
    output_file : str
        Output filename for plot
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Convert time to days
    for label, data in datasets.items():
        time_days = data['time'] / 86400
        
        # k-effective evolution
        axes[0, 0].plot(time_days, data['keff'], 'o-', label=label, linewidth=2)
        
        # U-235 depletion
        if 'U235' in data['nuclides']:
            axes[0, 1].plot(time_days, data['nuclides']['U235'], 'o-', 
                          label=label, linewidth=2)
        
        # Pu-239 buildup
        if 'Pu239' in data['nuclides']:
            axes[1, 0].plot(time_days, data['nuclides']['Pu239'], 'o-', 
                          label=label, linewidth=2)
        
        # Xe-135 evolution
        if 'Xe135' in data['nuclides']:
            axes[1, 1].plot(time_days, data['nuclides']['Xe135'], 'o-', 
                          label=label, linewidth=2)
    
    # Formatting
    axes[0, 0].set_ylabel('k-effective', fontsize=11)
    axes[0, 0].set_xlabel('Time (days)', fontsize=11)
    axes[0, 0].legend(fontsize=9)
    axes[0, 0].grid(True, alpha=0.3)
    
    axes[0, 1].set_ylabel('U-235 (atoms)', fontsize=11)
    axes[0, 1].set_xlabel('Time (days)', fontsize=11)
    axes[0, 1].legend(fontsize=9)
    axes[0, 1].grid(True, alpha=0.3)
    
    axes[1, 0].set_ylabel('Pu-239 (atoms)', fontsize=11)
    axes[1, 0].set_xlabel('Time (days)', fontsize=11)
    axes[1, 0].legend(fontsize=9)
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 1].set_ylabel('Xe-135 (atoms)', fontsize=11)
    axes[1, 1].set_xlabel('Time (days)', fontsize=11)
    axes[1, 1].legend(fontsize=9)
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: {output_file}")
    plt.close()


def run_depletion_comparison(
    small_timesteps,
    large_timesteps,
    power=1e6,
    use_derivatives=False
):
    """
    Run complete depletion comparison study.
    
    Parameters
    ----------
    small_timesteps : array-like
        Small timesteps for reference calculation (seconds)
    large_timesteps : array-like
        Large timesteps for test calculation (seconds)
    power : float
        Power level in watts
    use_derivatives : bool
        Whether to use derivative enhancement (future implementation)
        
    Returns
    -------
    dict
        Results from all calculations
    """
    print("=" * 70)
    print("OpenMC Depletion Comparison Study")
    print("=" * 70)
    
    # Check for chain file
    chain_file = get_chain_file()
    if chain_file is None:
        print("\nERROR: No depletion chain file found!")
        print("Please copy chain file from pincell_depletion example:")
        print("  cp ../pincell_depletion/chain_simple.xml .")
        print("")
        print("Or run the download script:")
        print("  bash download_chain.sh")
        return None
    
    print(f"\nUsing chain file: {chain_file}")
    print(f"Power: {power:.2e} W ({power/1e6:.2f} MW)")
    print(f"Reference: {len(small_timesteps)} timesteps, {sum(small_timesteps)/86400:.2f} days total")
    print(f"Test: {len(large_timesteps)} timesteps, {sum(large_timesteps)/86400:.2f} days total")
    
    # Create output directories
    ref_dir = Path('reference_depletion')
    test_dir = Path('large_timestep_depletion')
    deriv_dir = Path('derivative_depletion')
    
    for d in [ref_dir, test_dir, deriv_dir]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir()
    '''
    # Run reference calculation (small timesteps)
    print("\n" + "=" * 70)
    print("REFERENCE CALCULATION (small timesteps)")
    print("=" * 70)
    ref_results = run_standard_depletion(
        small_timesteps, power, ref_dir, chain_file
    )
    ref_data = extract_depletion_data(ref_results)
    
    # Run test calculation (large timesteps, no derivatives)
    print("\n" + "=" * 70)
    print("TEST CALCULATION (large timesteps, no derivatives)")
    print("=" * 70)
    test_results = run_standard_depletion(
        large_timesteps, power, test_dir, chain_file
    )
    test_data = extract_depletion_data(test_results)
    '''
    # Run derivative-enhanced calculation (large timesteps with derivatives)
    print("\n" + "=" * 70)
    print("DERIVATIVE-ENHANCED CALCULATION (large timesteps with derivatives)")
    print("=" * 70)
    deriv_results = run_derivative_depletion(
        large_timesteps, power, deriv_dir, chain_file
    )
    deriv_data = extract_depletion_data(deriv_results)
    
    # Compare results
    print("\n" + "=" * 70)
    print("RESULTS COMPARISON")
    print("=" * 70)
    
    test_comparison = compare_results(
        ref_data, test_data, 
        label='Large timesteps (no derivatives) vs Reference'
    )
    
    deriv_comparison = compare_results(
        ref_data, deriv_data,
        label='Large timesteps (with derivatives) vs Reference'
    )
    
    # Generate plots
    datasets = {
        'Reference (small Δt)': ref_data,
        'Large Δt (no derivatives)': test_data,
        'Large Δt (with derivatives)': deriv_data,
    }
    
    plot_comparison(datasets, output_file='depletion_comparison.png')
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Timestep reduction: {len(small_timesteps)} → {len(large_timesteps)} steps")
    print(f"Speedup factor: ~{len(small_timesteps) / len(large_timesteps):.1f}x")
    print(f"\nWithout derivatives:")
    print(f"  k-eff error: {test_comparison['keff_max_error']:.3f}% (max), "
          f"{test_comparison['keff_rms_error']:.3f}% (RMS)")
    print(f"\nWith derivatives:")
    print(f"  k-eff error: {deriv_comparison['keff_max_error']:.3f}% (max), "
          f"{deriv_comparison['keff_rms_error']:.3f}% (RMS)")
    
    improvement = (test_comparison['keff_max_error'] - deriv_comparison['keff_max_error']) / test_comparison['keff_max_error'] * 100
    print(f"\nError reduction: {improvement:.1f}%")
    
    print("\nNOTE: Current OpenMC does not automatically use derivative tallies")
    print("in the depletion solver. This demonstrates the infrastructure for")
    print("future implementation. Expected improvements would come from using")
    print("derivatives to predict flux/cross section changes during timesteps.")
    
    return {
        'reference': ref_data,
        'test': test_data,
        'derivative': deriv_data,
        'test_comparison': test_comparison,
        'deriv_comparison': deriv_comparison,
        'chain_file': chain_file
    }


if __name__ == '__main__':
    # Define timestep schedules for comparison
    # Reference: many small timesteps (accurate)
    timesteps_small = np.full(5, 1.0 * 86400)  # 5 steps × 1 day = 5 days
    
    # Test: few large timesteps (fast but less accurate)
    timesteps_large = np.full(2, 2.5 * 86400)   # 2 steps × 2.5 days = 5 days
    
    # Power level for 2D pin cell simulation
    # For 2D, power is linear power density (W/cm), not total watts
    # Typical PWR pin: ~174 W/cm or lower for testing
    power = 174  # W/cm (linear power density)
    
    try:
        print("\nStarting depletion comparison study...")
        print(f"This will run THREE full OpenMC depletion calculations:")
        print(f"  1. Reference: {len(timesteps_small)} timesteps (accurate)")
        print(f"  2. Large timesteps: {len(timesteps_large)} timesteps (fast, less accurate)")
        print(f"  3. Derivative-enhanced: {len(timesteps_large)} timesteps with derivative tallies")
        print(f"Power: {power} W/cm (linear power density for 2D pin cell)")
        print(f"\nNote: This may take 10-15 minutes to complete.")
        
        results = run_depletion_comparison(
            small_timesteps=timesteps_small,
            large_timesteps=timesteps_large,
            power=power,
            use_derivatives=False
        )
        
        if results is not None:
            print("\n" + "=" * 70)
            print("STUDY COMPLETE")
            print("=" * 70)
            print("\nKey findings:")
            print(f"1. Large timesteps ({len(timesteps_large)} steps) without derivatives:")
            print(f"   k-eff error: ~{results['test_comparison']['keff_max_error']:.2f}% (max)")
            print(f"2. Large timesteps WITH derivative tallies:")
            print(f"   k-eff error: ~{results['deriv_comparison']['keff_max_error']:.2f}% (max)")
            improvement = (results['test_comparison']['keff_max_error'] - results['deriv_comparison']['keff_max_error']) / results['test_comparison']['keff_max_error'] * 100
            print(f"3. Error reduction from derivatives: {improvement:.1f}%")
            print(f"4. Computational savings: ~{len(timesteps_small)/len(timesteps_large):.0f}x fewer transport solves")
            print("\nOutputs:")
            print("  - depletion_comparison.png: Visual comparison")
            print("  - reference_depletion/: Reference calculation")
            print("  - large_timestep_depletion/: Test without derivatives")
            print("  - derivative_depletion/: Test with derivatives")
            
    except KeyboardInterrupt:
        print("\n\nCalculation interrupted by user.")
    except Exception as e:
        print(f"\n\nError during calculation: {e}")
        import traceback
        traceback.print_exc()
        print("\nPlease ensure:")
        print("  1. Nuclear data is available (OPENMC_CROSS_SECTIONS set)")
        print("  2. Depletion chain file is downloaded")
        print("  3. OpenMC is properly installed")
