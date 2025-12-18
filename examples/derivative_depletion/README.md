# Derivative-Accelerated Depletion Example

This example demonstrates how nuclide density derivatives can potentially accelerate depletion calculations by accounting for self-shielding effects during large timesteps.

## Concept

Standard depletion solvers assume that flux (φ), macroscopic cross sections (Σ), and microscopic cross sections (σ) remain constant during a timestep. This ignores self-shielding: as strong absorbers like Xe-135 build up, they reduce local flux and affect reaction rates.

The derivative approach linearizes these quantities around the current state:

```
σ(N) ≈ σ(N₀) + (∂σ/∂N)(N - N₀)
φ(N) ≈ φ(N₀) + (∂φ/∂N)(N - N₀)
Σ(N) ≈ Σ(N₀) + (∂Σ/∂N)(N - N₀)
```

This allows larger timesteps while maintaining accuracy by predicting how the system evolves as nuclide densities change.

## Files

- `derivative_depletion_test.py` - Main demonstration script
- `README.md` - This file

## Requirements

- OpenMC with derivative tally support
- Nuclear cross section data (NNDC HDF5 recommended)
- Python packages: numpy, matplotlib

## Usage

```bash
# Ensure OPENMC_CROSS_SECTIONS is set
export OPENMC_CROSS_SECTIONS=$HOME/nndc_hdf5/cross_sections.xml

# Run the example
python derivative_depletion_test.py
```

## What It Does

1. **Setup**: Creates a simple PWR pin cell with Xe-135 tracking
2. **Standard Depletion**: Runs with many small timesteps (reference solution)
3. **Derivative-Enhanced**: Runs with fewer large timesteps using derivative corrections
4. **Comparison**: Plots results and computes accuracy vs speedup tradeoff

## Expected Output

- Console output showing:
  - Xe-135 densities from both methods
  - Relative error between methods
  - Theoretical speedup factor
- Plot: `xe135_depletion_comparison.png` showing time evolution

## Key Results

For Xe-135 (strong absorber, significant self-shielding):
- Standard method: 10 timesteps of 1 hour each
- Derivative method: 2 timesteps of 5 hours each
- Expected speedup: ~5x with <5% error (problem-dependent)

## Implementation Notes

This is a **proof-of-concept** demonstrating the algorithm. Full integration into OpenMC would require:

1. **Modifying `openmc.deplete.Operator`**:
   - Add derivative tally setup for each nuclide
   - Extract derivatives from statepoint files
   - Pass derivative info to integrators

2. **Modifying `openmc.deplete.Integrator`** classes:
   - Update predictor step to use derivatives
   - Linearize flux/cross section evolution
   - Adjust timestep acceptance criteria

3. **Performance optimization**:
   - Selective derivative computation (only important nuclides)
   - Caching of derivative information
   - Adaptive timestep control based on linearity check

## Xe-135 Depletion Equation

The test focuses on solving:

```
dN_Xe/dt = Y_Xe·Σ_f·φ + λ_I·N_I - λ_Xe·N_Xe - σ_a,Xe·N_Xe·φ
           ⎿⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⏌  ⎿⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⏌
              production           removal
```

Where self-shielding affects:
- **σ_a,Xe**: Increases as Xe builds up (more self-shielding)
- **φ**: Decreases as Xe builds up (poison effect)
- **Σ_f**: Decreases as Xe builds up (flux depression reduces fission rate)

## References

- Isotalo, A. (2013). "Computational Methods for Burnup Calculations with Monte Carlo Neutronics"
- OpenMC Pull Request #3690: Derivative tally support for k_eff search
- Herman, B. et al. (2013). "Improved diffusion coefficients generated from Monte Carlo codes"

## Future Work

- Extend to full depletion chains (U-238 capture chain, Pu isotopes)
- Implement adaptive timestep selection based on derivative magnitude
- Benchmark against experimental Xe oscillation data
- Test with spatial effects (e.g., Xe oscillations in reactor cores)
