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

## Motivation & Analogy

### Comparison to Molecular Dynamics

The Bateman depletion equations share similarities with molecular dynamics (MD) simulations:

**Similarities:**
- Both solve **systems of coupled ODEs** describing temporal evolution
- Both track populations: MD tracks atom positions/velocities, Bateman tracks nuclide densities
- Both use integrators to advance in time (MD: Verlet/Runge-Kutta, Bateman: predictor-corrector/CRAM)
- Both have **stiff equations**: MD has fast vibrations vs slow diffusion; Bateman has fast-decaying isotopes (I-135, λ=2.9×10⁻⁵ s⁻¹) vs slow ones (U-238, λ=4.9×10⁻¹⁸ s⁻¹)

**Key Differences:**
- **Coupling**: MD is many-body (every atom interacts with neighbors), Bateman is one-way chains (parent→daughter)
- **Feedback**: MD forces depend on positions instantaneously; Bateman requires external neutronics solve for flux/cross sections
- **Timescales**: MD operates on femtoseconds to nanoseconds; Bateman on seconds to years
- **Scale**: MD simulates 10³-10⁹ individual atoms; Bateman treats 10²³ atoms/cm³ as bulk densities

**The Analogy**: Standard Bateman solvers are like **rigid-body MD** (assumes bonds don't stretch). Derivative-enhanced Bateman is like **flexible MD** (accounts for how forces change as positions evolve), enabling better energy conservation over larger timesteps.

## Scalability to Full-Core Problems

### Challenge: BEAVRS-Class Benchmarks

Real reactor cores present significant computational challenges:
- **193 fuel assemblies** with ~50,000 fuel pins
- **~50 unique material compositions** (different enrichments, burnups)
- **~300 depletion nuclides** in full chains (U-234 through Cm-247)
- **~10,000 spatial zones** for depletion tracking

### Computational Cost Analysis

**Derivative Tally Overhead per Nuclide:**
```
Standard tally:   Store 1 value per bin
Derivative tally: Store 1 value + flux derivative tracking
                  ≈ 1.5-2× memory, similar runtime cost
```

**Naive Approach** (all nuclides):
- 300 nuclides × 10,000 zones = **3 million derivative tallies**
- Memory: ~100 GB extra ❌ **INFEASIBLE**
- Runtime: 1.5-2× longer per transport solve

### Practical Implementation: Selective Derivatives

Compute derivatives **only** for nuclides with significant self-shielding:

| Category | Nuclides | Zones | Tallies | Why? |
|----------|----------|-------|---------|------|
| **Strong absorbers** | Xe-135, Sm-149, Gd-155/157 | Most zones | ~50k | Largest self-shielding effects |
| **Actinides** | Pu-239/240/241, U-235 | High-burnup only | ~10k | Spectrum hardening from Pu buildup |
| **Burnable absorbers** | B-10, Er-167 | BA rods only | ~500 | Critical for reactivity control |

**Total: ~60,000 derivative tallies** (vs 3 million naive)

**Memory overhead:** ~60 MB (acceptable vs GB statepoint baseline)

### Expected Speedup for Full-Core Depletion

**Standard Approach:**
- Timestep limited by Xe-135 dynamics: ~3-6 hour steps
- 18-month cycle: ~4,000 timesteps × 8 hours/solve = **32,000 CPU-hours**

**Derivative Approach** (realistic):
- Larger timesteps: ~12-24 hours (2-4× fewer timesteps)
- Overhead: 1.3× per solve (selective tallies)
- Total: 1,000 timesteps × 10.4 hours/solve = **10,400 CPU-hours**

**Realistic speedup: 2-3× for full-core depletion** ✅

### When Is It Worth Using?

✅ **Recommended for:**
- Assembly-level problems with strong absorbers (Xe-135, Sm-149)
- Gadolinium-bearing fuels (strong self-shielding)
- Problems where transport dominates runtime (>80% of total time)
- Studies requiring many depletion cases (parameter sweeps)

❌ **Not recommended for:**
- Rapid transients (small timesteps required anyway)
- Systems without strong absorbers (little self-shielding benefit)
- Limited memory systems (derivative overhead unaffordable)
- Already-fast problems (overhead exceeds benefit)

### Implementation Challenges

1. **Spatial coupling**: Xe-135 in assembly A affects flux in assembly B
   - May require global derivative tallies for core-wide feedback
   - Local derivatives capture most physics for pin-level problems

2. **Burnup-dependent derivatives**: ∂σ/∂N changes as fuel composition evolves
   - Need adaptive strategy: re-evaluate which nuclides need derivatives
   - Can disable derivatives after transients equilibrate

3. **Parallel efficiency**: 
   - Derivative tallies are local → good MPI scaling
   - More tallies → more communication for reduction (manageable)

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
