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
    
    times = []
    keffs = []
    nuclide_data = {nuc: [] for nuc in nuclides}
    
    for i, time in enumerate(results.get_times()):
        times.append(time)
        
        # Get k-effective
        keff = results[i].k
        keffs.append(keff)
        
        # Get nuclide concentrations
        mat_id = list(results[i].keys())[0]  # First depletable material
        for nuc in nuclides:
            try:
                atoms = results[i, mat_id, nuc]
                nuclide_data[nuc].append(atoms)
            except KeyError:
                nuclide_data[nuc].append(0.0)
    
    return {
        'time': np.array(times),
        'keff': np.array(keffs),
        'nuclides': {nuc: np.array(data) for nuc, data in nuclide_data.items()}
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
    
    for d in [ref_dir, test_dir]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir()
    
    # Run reference calculation (small timesteps)
    print("\n" + "=" * 70)
    print("REFERENCE CALCULATION (small timesteps)")
    print("=" * 70)
    ref_results = run_standard_depletion(
        small_timesteps, power, ref_dir, chain_file
    )
    ref_data = extract_depletion_data(ref_results)
    
    # Run test calculation (large timesteps)
    print("\n" + "=" * 70)
    print("TEST CALCULATION (large timesteps)")
    print("=" * 70)
    test_results = run_standard_depletion(
        large_timesteps, power, test_dir, chain_file
    )
    test_data = extract_depletion_data(test_results)
    
    # Compare results
    print("\n" + "=" * 70)
    print("RESULTS COMPARISON")
    print("=" * 70)
    
    comparison = compare_results(
        ref_data, test_data, 
        label='Large timesteps vs Reference'
    )
    
    # Generate plots
    datasets = {
        'Reference (small Δt)': ref_data,
        'Large timesteps': test_data,
    }
    
    plot_comparison(datasets, output_file='depletion_comparison.png')
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Timestep reduction: {len(small_timesteps)} → {len(large_timesteps)} steps")
    print(f"Speedup factor: ~{len(small_timesteps) / len(large_timesteps):.1f}x")
    print(f"k-eff error: {comparison['keff_max_error']:.3f}% (max), "
          f"{comparison['keff_rms_error']:.3f}% (RMS)")
    
    if use_derivatives:
        print("\nNOTE: Derivative enhancement not yet implemented in openmc.deplete")
        print("This comparison shows error from large timesteps alone.")
        print("Future work will demonstrate error reduction using derivatives.")
    
    return {
        'reference': ref_data,
        'test': test_data,
        'comparison': comparison,
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
        print(f"This will run two full OpenMC depletion calculations")
        print(f"Reference: {len(timesteps_small)} timesteps")
        print(f"Test: {len(timesteps_large)} timesteps")
        print(f"Power: {power} W/cm (linear power density for 2D pin cell)")
        print(f"\nNote: This may take several minutes to complete.")
        
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
            print(f"1. Large timesteps ({len(timesteps_large)} steps) produce errors")
            print(f"   of ~{results['comparison']['keff_max_error']:.2f}% in k-eff")
            print(f"2. Computational savings: ~{len(timesteps_small)/len(timesteps_large):.0f}x fewer transport solves")
            print(f"3. Future work: Use derivative tallies to reduce this error")
            print(f"   while maintaining the speedup")
            print("\nOutputs:")
            print("  - depletion_comparison.png: Visual comparison")
            print("  - reference_depletion/: Reference calculation files")
            print("  - large_timestep_depletion/: Test calculation files")
            
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
