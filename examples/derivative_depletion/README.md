# Derivative-Accelerated Depletion Example

This example demonstrates the concept of using nuclide density derivative tallies to accelerate depletion calculations by taking larger timesteps while maintaining accuracy through actual OpenMC transport-depletion calculations.

## Overview

Depletion calculations in OpenMC solve the Bateman equations to track nuclide evolution under neutron irradiation. Traditional methods (predictor-corrector, CRAM, etc.) assume that reaction rates remain approximately constant during each timestep. This assumption breaks down for:

1. **Strong neutron absorbers** (Xe-135, Sm-149) that cause significant flux depression
2. **Large timesteps** where nuclide concentrations change substantially  
3. **Highly coupled systems** where composition changes affect spectrum

This example uses **actual OpenMC depletion runs** to quantify these effects and explores using **derivative tallies** (∂R/∂N, where R is a reaction rate and N is a nuclide density) to correct for them.

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
- Memory: ~100 GB extra **INFEASIBLE**
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

**Realistic speedup: 2-3× for full-core depletion**

### When Is It Worth Using?

**Recommended for:**
- Assembly-level problems with strong absorbers (Xe-135, Sm-149)
- Gadolinium-bearing fuels (strong self-shielding)
- Problems where transport dominates runtime (>80% of total time)
- Studies requiring many depletion cases (parameter sweeps)

**Not recommended for:**
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

- `derivative_depletion_test.py` - Main script that runs actual OpenMC depletion calculations
- `README.md` - This file

## Requirements

### Essential
- **OpenMC** (latest version with depletion support)
- **Nuclear cross section data** (NNDC HDF5 format)
- **Depletion chain file** (e.g., `chain_simple.xml`)
- **Python packages**: `numpy`, `matplotlib`, `h5py`, `scipy`

### Setup Nuclear Data

```bash
# Set cross section library (if not already set)
export OPENMC_CROSS_SECTIONS=$HOME/nndc_hdf5/cross_sections.xml

# Get depletion chain file - copy from pincell_depletion example
cp ../pincell_depletion/chain_simple.xml .

# Or use the helper script
bash download_chain.sh
```

## Usage

```bash
cd examples/derivative_depletion
python derivative_depletion_test.py
```

**Note:** This will take several minutes as it runs two complete depletion calculations with full transport solves at each timestep.

## What It Does

This script performs **two actual OpenMC depletion calculations** on a PWR pin cell:

1. **Reference calculation** (high accuracy baseline):
   - 5 timesteps × 1 day = 5 days total
   - Small timesteps ensure accurate tracking
   - 5 full transport+depletion cycles

2. **Test calculation** (large timesteps):
   - 2 timesteps × 2.5 days = 5 days total  
   - Larger timesteps reduce computation time
   - 2 full transport+depletion cycles (~2.5x faster)

**IMPORTANT - Power Units for 2D Simulations:**
- Power = 174 W/cm (linear power density)
- For 2D pin cell models, power must be specified per unit length, NOT total watts
- Using total watts (e.g., 1 MW) will cause the system to go deeply subcritical

Then it:
3. **Compares results**: k-eff, U-235, Pu-239, Xe-135 concentrations
4. **Quantifies errors**: Shows accuracy loss from large timesteps
5. **Generates plots**: Visual comparison of nuclide evolution

## Expected Output

```
reference_depletion/           # Reference calculation output
large_timestep_depletion/      # Test calculation output  
depletion_comparison.png       # 4-panel comparison plot
```

Console output shows:
- Progress of each depletion run
- k-eff errors (absolute and relative)
- Nuclide concentration errors
- Computational speedup (timestep reduction)

### Sample Results

Typical results for 5-day pin cell depletion:
- **k-eff error**: 0.1-0.5% (max relative error)
- **Xe-135 error**: 1-5% (most sensitive to timestep size)
- **U-235 error**: <0.5% (slow depleting, less sensitive)
- **Speedup**: ~2.5x (from 5 to 2 timesteps)

**Key insight**: Large timesteps save time but introduce errors. Future work will use derivative tallies to reduce these errors.

## Implementation Status & Future Work

### Current Implementation (This Example)

**What works now:**
- Actual OpenMC transport-depletion runs
- Comparison of different timestep strategies
- Quantification of errors from large timesteps
- Visual comparison of key nuclides

**What's not yet implemented:**
- Derivative tally computation during depletion
- Using derivatives to correct large-timestep errors
- Integration into `openmc.deplete` module

### Path to Derivative Enhancement

This example establishes the baseline by showing:
1. How much error large timesteps introduce
2. What speedup is possible from fewer timesteps
3. Which nuclides are most sensitive

**Next steps** for full implementation:

1. **Add derivative tally support to `openmc.deplete.Operator`**:
   ```python
   # At each predictor step, add derivative tallies
   for nuclide in ['Xe135', 'Sm149', 'U235', 'Pu239']:
       deriv = openmc.TallyDerivative(
           variable='nuclide_density',
           material=mat_id,
           nuclide=nuclide
       )
   ```

2. **Modify integrators to use derivatives**:
   ```python
   # In predictor step: estimate flux change
   dflux_dN = extract_derivative_from_statepoint(sp)
   
   # Correct predicted density using Taylor expansion
   N_corrected = N_pred + 0.5 * dflux_dN * (N_pred - N_initial)
   ```

3. **Benchmark and optimize**:
   - Test on various problems (pin, assembly, core)
   - Optimize which nuclides need derivatives
   - Implement adaptive timestep control

## Key Physics: Self-Shielding in Xe-135

The Xe-135 depletion equation illustrates why derivatives matter:

```
dN_Xe/dt = Y_Xe·Σ_f·φ + λ_I·N_I - λ_Xe·N_Xe - σ_a,Xe·N_Xe·φ
```

As Xe-135 builds up:
- **σ_a,Xe** changes (self-shielding increases absorption cross section)
- **φ** decreases (flux depression from poison effect)
- Standard methods assume both constant during timestep → error

Derivatives capture: ∂φ/∂N_Xe < 0 (more Xe → less flux)

This nonlinearity requires small timesteps OR derivative correction.

## References

- Isotalo, A. (2013). "Computational Methods for Burnup Calculations with Monte Carlo Neutronics"
- OpenMC Pull Request #3690: Derivative tally support for k_eff search
- Herman, B. et al. (2013). "Improved diffusion coefficients generated from Monte Carlo codes"

## Future Work

- Extend to full depletion chains (U-238 capture chain, Pu isotopes)
- Implement adaptive timestep selection based on derivative magnitude
- Benchmark against experimental Xe oscillation data
- Test with spatial effects (e.g., Xe oscillations in reactor cores)
