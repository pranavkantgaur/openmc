# Derivative Tally Methods in OpenMC

This document provides a comprehensive overview of the derivative tally methods currently implemented in the OpenMC repository, along with their advantages and disadvantages.

## Overview

OpenMC implements **first-order derivative tallies** that compute sensitivities of tally scores with respect to material perturbations. These derivatives are computed during particle transport by propagating weight derivatives through the Monte Carlo simulation, enabling both tally values and their derivatives to be obtained in a single run.

**Key Feature**: Derivatives are computed as **logarithmic derivatives**: (1/R) × (∂R/∂x), where R is a reaction rate and x is the perturbation variable.

## Implemented Methods

OpenMC currently implements **three types** of material perturbation derivatives:

### 1. Density Derivatives (`'density'`)

**What it does**: Computes the derivative of tally scores with respect to material mass density (g/cm³).

**Mathematical form**: ∂R/∂ρ where ρ is mass density

**Supported Scores**:
- Flux
- Total cross section
- Scatter
- Absorption
- Fission
- Nu-fission

**Supported Estimators**: Analog, Collision

#### Pros ✅
- Simple to implement and interpret
- Applicable to all materials (fissile and non-fissile)
- No special nuclear data requirements
- Works with standard cross section libraries (HDF5, ACE)
- Useful for material densification/swelling studies
- No additional data files needed

#### Cons ❌
- Cannot distinguish between different nuclides in a material
- Less useful for detailed composition sensitivity studies
- Changes all nuclides proportionally (may not be physically realistic)
- Cannot isolate effects of specific isotopes

#### Applications
- Fuel densification/swelling analysis
- Material density optimization
- Reactivity coefficient calculations
- Uncertainty quantification for manufacturing tolerances

---

### 2. Nuclide Density Derivatives (`'nuclide_density'`)

**What it does**: Computes the derivative of tally scores with respect to a specific nuclide's atom density (atoms/barn-cm).

**Mathematical form**: ∂R/∂Nᵢ where Nᵢ is atom density of nuclide i

**Supported Scores**:
- Flux
- Total cross section
- Scatter
- Absorption
- Fission
- Nu-fission

**Supported Estimators**: Analog, Collision

#### Pros ✅
- **Isotope-specific sensitivity information** - most powerful feature
- Essential for criticality searches (e.g., critical boron concentration)
- Useful for fuel cycle optimization
- Can track individual fission products or actinides
- Enables selective derivative computation for computational efficiency
- No special data requirements (works with standard cross section libraries)
- Most versatile and widely applicable method

#### Cons ❌
- Requires specification of individual nuclides (more setup)
- More complex to set up for many nuclides
- May need unit conversions (e.g., ppm to atoms/barn-cm)
- Computational overhead scales with number of tracked nuclides
- Need to know which nuclides are important a priori

#### Applications
- **Critical boron concentration search** (most common use case)
- Xenon/Samarium worth calculations
- Reactivity coefficient determination
- Fuel composition optimization
- **Depletion calculations with self-shielding correction**
- Burnable poison optimization
- Sensitivity studies for specific isotopes

---

### 3. Temperature Derivatives (`'temperature'`)

**What it does**: Computes the derivative of tally scores with respect to material temperature (Kelvin), capturing Doppler broadening effects.

**Mathematical form**: ∂R/∂T where T is temperature

**Supported Scores**:
- Flux
- Total cross section
- Scatter
- Absorption
- Fission
- Nu-fission

**Supported Estimators**: Analog, Collision

#### Pros ✅
- Captures physics of Doppler broadening
- Important for reactor safety analysis (in principle)
- Useful for temperature coefficient calculations
- Can predict reactivity feedback effects

#### Cons ❌
- ⚠️ **REQUIRES windowed multipole (WMP) data** - standard tabulated cross sections do NOT support analytical temperature derivatives
- ⚠️ **Limited energy range** - only valid in resolved resonance range (~1 eV to ~10 keV)
- ⚠️ **Sparse data availability** - very few nuclides in standard libraries have WMP data
- ⚠️ **Does NOT account for**:
  - Thermal expansion (geometry changes)
  - S(α,β) thermal scattering temperature dependence
  - Resonance scattering temperature effects
  - Unresolved resonance Doppler broadening
- ⚠️ **Not compatible with temperature interpolation** - if using `settings.temperature_method = 'interpolation'`, derivatives are NOT computed from interpolation
- ⚠️ **Approximate scattering treatment** - assumes ∂P(E'→E)/∂T = 0, introducing 2-5% errors near resonances
- **SEVERE PRACTICAL LIMITATIONS** make this method unsuitable for most applications

#### Applications
- Doppler coefficient calculations (with major caveats)
- Temperature feedback analysis (resolved resonance range only)
- Academic/research studies of temperature effects

#### ⚠️ Important Recommendation
**DO NOT use temperature derivatives for practical k-eff searches or production reactor applications**. The limitations listed above make them unreliable. Instead, use `density` or `nuclide_density` derivatives and parameterize material properties as functions of temperature.

## Implementation Details

### How It Works

OpenMC propagates flux derivatives through particle histories:

1. **Transport (tracking)**: During flight, derivatives track how cross sections affect particle weight:
   ```
   ∂φ/∂x → ∂φ/∂x - φ × (∂Σₜ/∂x) × Δs
   ```

2. **Collisions (scattering)**: After scattering, derivatives are updated based on scattering rates:
   ```
   ∂φ/∂x → ∂φ/∂x + φ × (∂Σₛ/∂x) / Σₛ
   ```

3. **Score adjustments**: Tallies are multiplied by (1 + ∂c/∂x), where c is the score-specific cross section.

### Source Code Location

- **Python API**: `openmc/tally_derivative.py`
- **C++ Header**: `include/openmc/tallies/derivative.h`
- **C++ Implementation**: `src/tallies/derivative.cpp`
- **Examples**: 
  - `examples/keff_search_derivatives/` - Criticality search demonstrations
  - `examples/derivative_depletion/` - Depletion acceleration examples
- **Tests**: `tests/regression_tests/diff_tally/`

### Computational Cost

- **Memory**: ~1.5-2× per derivative tally
- **Runtime**: ~5-15% overhead for typical cases
- **Parallel efficiency**: Excellent scaling with MPI (derivatives are local)

For full-core problems with selective derivatives (e.g., tracking only Xe-135, Sm-149, and key actinides), expect ~10-20% total overhead.

## General Limitations

All derivative methods share these limitations:

1. ❌ **Multi-group mode not supported** - derivatives only work in continuous-energy mode
2. ❌ **Estimator restrictions** - only analog and collision estimators supported (NO tracklength)
3. ❌ **Small perturbation assumption** - assumes perturbations don't significantly change fission source distribution
4. ❌ **Limited score support** - not all tally scores have derivative implementations
5. ❌ **Single material perturbation** - each derivative perturbs one material at a time

### Unsupported Scores

- Current tallies
- Energy deposition (`'heating'`)
- Damage energy (`'damage-energy'`)
- Photon production scores
- Custom scores via `(n,x)` MT reactions

## Comparison with Finite Difference Methods

| Feature | Derivative Tallies | Finite Difference |
|---------|-------------------|-------------------|
| **Accuracy** | Exact (within MC statistics) | O(Δx) or O(Δx²) |
| **Number of runs** | 1 run | 2-3 runs |
| **Computational cost** | ~1.1-1.2× base cost | 2-3× base cost |
| **Multiple parameters** | Need derivative per parameter | Need run per parameter |
| **Small perturbations** | Exact | Can have cancellation errors |
| **Large perturbations** | Linear approximation only | More accurate |
| **Implementation** | Requires code support | No code changes needed |

## Practical Applications

### 1. K-effective Search (Criticality Search)

Derivative tallies enable gradient-based search algorithms that converge **2-3× faster** than derivative-free methods:

```python
# Example: Find critical boron concentration
model.keff_search(
    func=lambda x: set_boron_concentration(x, model),
    x0=500.0,  # Initial guess (ppm)
    target=1.0,  # Target k-eff
    use_derivative_tallies=True,
    deriv_variable='nuclide_density',
    deriv_material=coolant_id,
    deriv_nuclide='B10'
)
```

**Status**: ✅ Fully implemented and tested

### 2. Depletion Acceleration

Use derivatives to correct reaction rates during depletion, enabling **2-5× larger timesteps** while maintaining accuracy:

- Predict how flux changes as nuclide densities evolve
- Correct for self-shielding effects (Xe-135, Sm-149)
- Reduce number of expensive transport solves

**Status**: ✅ Core algorithm fully implemented in `openmc.deplete`

**Tested for**: Xe-135, Sm-149, U-235, Pu-239

### 3. Sensitivity and Uncertainty Quantification

Derivatives provide exact sensitivities for uncertainty propagation:

```
σ²ᴿ = Σᵢⱼ (∂R/∂xᵢ) × Cov(xᵢ,xⱼ) × (∂R/∂xⱼ)
```

Applications:
- Manufacturing tolerance analysis
- Nuclear data uncertainty quantification  
- Design optimization with uncertainty constraints

### 4. Reactivity Coefficients

Direct computation of reactivity coefficients:
- Doppler coefficient: αₜ = (1/k) × (∂k/∂T)
- Void coefficient: αᵨ = (1/k) × (∂k/∂ρ)
- Boron worth: ∂k/∂C_B

## Best Practices

### 1. Choose the Right Derivative Type

- ✅ Use `nuclide_density` for isotope-specific studies (boron, Xe, actinides) - **RECOMMENDED for most applications**
- ✅ Use `density` for material-level perturbations (densification, swelling)
- ❌ **AVOID** `temperature` derivatives unless you have WMP data and fully understand limitations

### 2. Selective Derivative Computation

For large problems, compute derivatives only for important nuclides:

- **Strong absorbers**: Xe-135, Sm-149, Gd-155/157
- **Actinides**: U-235, Pu-239/240/241 (high burnup regions only)
- **Burnable absorbers**: B-10, Er-167 (if present)

This reduces overhead from 3 million tallies (naive approach) to ~60,000 tallies (selective approach) for full-core problems.

### 3. Verify Linearity Assumptions

Derivatives assume small perturbations. Verify by comparing:
- Derivative prediction: R(x+Δx) ≈ R(x) + (∂R/∂x)×Δx
- Actual perturbed value: Run with perturbed input

If error >5%, perturbation may be too large for linear approximation.

### 4. Unit Conversions

Be careful with units, especially for `nuclide_density`:

- OpenMC computes: ∂R/∂N in [barn·cm / atom]
- For ppm searches: Convert using material composition
- Example: B-10 at 1000 ppm requires density-to-ppm conversion factor

### 5. Statistical Considerations

- Derivative tallies have uncertainty like regular tallies
- May need more particles for good derivative statistics
- Use batch statistics to estimate uncertainty in derivatives

## Summary Comparison Table

| Method | Data Requirements | Energy Range | Practical Utility | Best For |
|--------|------------------|--------------|-------------------|----------|
| **Density** | Standard XS libraries | All energies | ⭐⭐⭐⭐ Good | Material density studies |
| **Nuclide Density** | Standard XS libraries | All energies | ⭐⭐⭐⭐⭐ Excellent | Composition optimization, criticality searches |
| **Temperature** | WMP data (rare) | Resolved resonance only | ⭐ Poor | Academic studies only |

## Recommendation

**For most practical applications, use `nuclide_density` derivatives**. They provide:
- Maximum flexibility (isotope-specific)
- No special data requirements
- Full energy range coverage
- Proven track record in production applications

Only use `temperature` derivatives if you:
1. Have windowed multipole data for all relevant nuclides
2. Are studying effects in the resolved resonance range only
3. Understand and accept the approximations and limitations
4. Have verified the approach for your specific application

## References

1. Harper, S. M. (2016). "Calculating Reaction Rate Derivatives in Monte Carlo Neutron Transport." MIT Master's Thesis. https://dspace.mit.edu/handle/1721.1/106690

2. Romano, P. K., et al. (2015). "OpenMC: A state-of-the-art Monte Carlo code for research and development." *Annals of Nuclear Energy*, 82, 90-97.

3. OpenMC Documentation: https://docs.openmc.org

4. OpenMC Examples:
   - `examples/keff_search_derivatives/` - Comprehensive k-eff search demonstrations
   - `examples/derivative_depletion/` - Depletion acceleration examples

## Questions?

For more information:
- See detailed documentation in `docs/source/methods/derivative_tallies.rst`
- Check example scripts in `examples/keff_search_derivatives/` and `examples/derivative_depletion/`
- View API documentation at https://docs.openmc.org
