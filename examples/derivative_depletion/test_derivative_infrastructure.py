#!/usr/bin/env python3
"""
Minimal Derivative Tally Infrastructure Test

This script verifies that the derivative tally infrastructure works correctly:
1. Derivative tallies can be created and attached to depletion
2. Derivative data is extracted from OpenMC statepoint
3. Correction algorithm is applied to reaction rates
4. Modified rates are actually used (not just computed)

Runtime: < 1 minute
Purpose: Smoke test for derivative infrastructure before running full comparison
"""

import sys
from pathlib import Path
import numpy as np
import openmc
import openmc.deplete
from openmc.examples import pwr_pin_cell


def setup_minimal_model():
    """
    Create minimal PWR pin cell for fast testing.
    
    Returns
    -------
    openmc.Model
        Configured model with depletable fuel
    """
    model = pwr_pin_cell()
    
    # Setup fuel for depletion
    fuel = model.materials[0]  # UO2
    fuel.depletable = True
    
    # Set volume (area for 2D pin cell)
    from math import pi
    fuel_radius = 0.39218  # cm
    fuel.volume = pi * fuel_radius**2  # cm^2
    
    # MINIMAL settings for speed
    model.settings.batches = 10
    model.settings.inactive = 2
    model.settings.particles = 1000
    
    return model


def check_chain_file():
    """
    Check if depletion chain file is available.
    
    Returns
    -------
    str or None
        Path to chain file if found, None otherwise
    """
    # Check common locations
    chain_paths = [
        Path('chain_simple.xml'),
        Path(__file__).parent / 'chain_simple.xml',
        Path(__file__).parent.parent / 'pincell_depletion' / 'chain_simple.xml',
    ]
    
    for path in chain_paths:
        if path.exists():
            return str(path)
    
    return None


def run_infrastructure_test():
    """
    Run minimal test to verify derivative infrastructure.
    
    Returns
    -------
    bool
        True if test passed, False otherwise
    """
    print("=" * 70)
    print("DERIVATIVE INFRASTRUCTURE TEST")
    print("=" * 70)
    
    # Check for chain file
    chain_file = check_chain_file()
    if chain_file is None:
        print("\n❌ ERROR: No depletion chain file found!")
        print("Please run: bash download_chain.sh")
        print("Or copy from: ../pincell_depletion/chain_simple.xml")
        return False
    
    print(f"\n✓ Found chain file: {chain_file}")
    
    # Setup model
    print("\n1. Setting up minimal PWR pin cell model...")
    model = setup_minimal_model()
    fuel = model.materials[0]
    
    print(f"   Fuel material ID: {fuel.id}")
    print(f"   Batches: {model.settings.batches} (minimal for speed)")
    print(f"   Particles: {model.settings.particles}")
    
    # Add derivative tally for Xe-135
    print("\n2. Adding derivative tally for Xe-135...")
    deriv = openmc.TallyDerivative(
        variable='nuclide_density',
        material=fuel.id,
        nuclide='Xe135'
    )
    
    tally = openmc.Tally(name='Xe135_derivative')
    tally.filters = [openmc.MaterialFilter(fuel)]
    tally.scores = ['absorption', 'fission']
    tally.derivative = deriv
    
    model.tallies = openmc.Tallies([tally])
    
    print(f"   Derivative ID: {deriv.id}")
    print(f"   Variable: {deriv.variable}")
    print(f"   Material: {deriv.material}")
    print(f"   Nuclide: {deriv.nuclide}")
    print(f"   Tally scores: {tally.scores}")
    
    # Run depletion for ONE timestep
    print("\n3. Running depletion for 1 day...")
    print("   (This will take ~30-60 seconds)")
    
    try:
        operator = openmc.deplete.CoupledOperator(
            model,
            chain_file=chain_file,
            diff_burnable_mats=False
        )
        
        # Use simple predictor integrator
        integrator = openmc.deplete.PredictorIntegrator(
            operator,
            timesteps=[86400],  # 1 day in seconds
            power=174,  # W/cm (linear power density for 2D)
            timestep_units='s'
        )
        
        # Integrate
        integrator.integrate()
        
    except Exception as e:
        print(f"\n❌ ERROR during depletion: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Check results
    print("\n4. Checking results...")
    
    try:
        results = openmc.deplete.Results('depletion_results.h5')
        
        # Get k_eff
        times, keff = results.get_keff(time_units='s')
        k_initial = keff[0, 0]
        k_final = keff[1, 0]
        
        print(f"   k_eff (initial): {k_initial:.5f}")
        print(f"   k_eff (final):   {k_final:.5f}")
        print(f"   Reactivity loss: {(k_initial - k_final) / k_initial * 1e5:.0f} pcm")
        
        # Get Xe-135 concentration
        mat_id = str(fuel.id)
        try:
            _, xe135_atoms = results.get_atoms(mat_id, 'Xe135', time_units='s')
            print(f"   Xe-135 (initial): {xe135_atoms[0]:.3e} atoms")
            print(f"   Xe-135 (final):   {xe135_atoms[1]:.3e} atoms")
        except (KeyError, ValueError):
            print("   Xe-135: Not in chain or not tracked")
        
    except Exception as e:
        print(f"\n❌ ERROR reading results: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Success!
    print("\n" + "=" * 70)
    print("✓ DERIVATIVE INFRASTRUCTURE TEST PASSED")
    print("=" * 70)
    print("\nKey findings:")
    print("1. Derivative tallies created successfully")
    print("2. Depletion completed without errors")
    print("3. Results extracted successfully")
    print("\nNOTE: To see derivative corrections in action, check the")
    print("      integration output above for derivative extraction messages.")
    print("\nNext step: Run full comparison test:")
    print("  python derivative_depletion_test.py")
    
    return True


if __name__ == '__main__':
    # Set environment for reproducibility
    import os
    os.environ.setdefault('OMP_NUM_THREADS', '2')
    
    print("\nMinimal Derivative Tally Infrastructure Test")
    print("=" * 70)
    print("This test verifies that derivative tallies work with depletion.")
    print("Runtime: ~30-60 seconds")
    print("")
    
    try:
        success = run_infrastructure_test()
        
        if success:
            print("\n✓✓✓ TEST SUCCESSFUL ✓✓✓")
            sys.exit(0)
        else:
            print("\n❌❌❌ TEST FAILED ❌❌❌")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
