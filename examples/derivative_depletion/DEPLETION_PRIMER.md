# Depletion/Burnup Primer for Derivative Acceleration

A practical guide for implementing derivative-accelerated depletion in OpenMC.

---

## Part 1: Core Concepts

### What is Depletion?

**Depletion** (or **burnup**) tracks how material compositions change over time in a reactor due to:
1. **Neutron reactions**: U-235 absorbs neutron → fissions → creates fission products
2. **Radioactive decay**: I-135 (6.6 hour half-life) → Xe-135
3. **Transmutation**: U-238 captures neutron → U-239 → Np-239 → Pu-239

**Why it matters:**
- Fresh fuel: ~5% U-235, highly reactive
- Burned fuel: ~1% U-235, ~1% Pu-239, hundreds of fission products
- Reactivity changes by 10-20% over 18-month fuel cycle
- Safety-critical: Must predict shutdown margin, decay heat

### Key Nuclides to Know

| Nuclide | Type | Importance | Half-life/XS |
|---------|------|------------|--------------|
| **U-235** | Fissile | Main fuel | σ_f ≈ 585 b |
| **U-238** | Fertile | Breeds Pu-239 | σ_γ ≈ 2.7 b |
| **Pu-239** | Fissile | Builds up in fuel | σ_f ≈ 748 b |
| **Xe-135** | Poison | Strongest absorber | σ_a ≈ 2.65 Mb, t₁/₂ = 9.1 h |
| **Sm-149** | Poison | Stable absorber | σ_a ≈ 40 kb (stable) |
| **I-135** | Precursor | Decays to Xe-135 | t₁/₂ = 6.6 h |

**Note:** 1 barn (b) = 10⁻²⁴ cm², 1 kilobarn (kb) = 1000 b, 1 megabarn (Mb) = 10⁶ b

### The Depletion-Transport Coupling

```
                    ┌─────────────────┐
                    │   Initial       │
                    │ Composition N₀  │
                    └────────┬────────┘
                             │
                             ▼
         ┌───────────────────────────────────┐
         │  TRANSPORT SOLVE (OpenMC)         │
         │  - Run Monte Carlo                │
         │  - Compute flux φ(r,E,t)          │
         │  - Compute reaction rates         │
         │  - Output: σᵢ, Σⱼ, φ              │
         └───────────────┬───────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │  DEPLETION SOLVE (openmc.deplete) │
         │  - Solve Bateman equations        │
         │  - dN/dt = AN + S                 │
         │  - Integrate over timestep Δt     │
         │  - Output: N(t + Δt)              │
         └───────────────┬───────────────────┘
                         │
                         ▼
                    Update composition
                         │
                         └─────► Loop until end time
```

**Key insight:** Transport is **expensive** (minutes to hours), depletion is **cheap** (seconds).
Goal: Reduce number of transport solves while maintaining accuracy.

---

## Part 2: Mathematical Foundation

### The Bateman Equations

For a single nuclide *i*:

```
dNᵢ/dt = Σⱼ (λⱼ→ᵢ Nⱼ + σγ,ⱼ→ᵢ Nⱼ φ) + Yᵢ Σf φ - (λᵢ + σᵢ φ) Nᵢ
         ⎿━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━⏌   ⎿━━━━━━━━━━━━━━━━━⏌
                   Production                        Removal
```

Where:
- **Nᵢ**: Atom density of nuclide *i* (atoms/barn-cm)
- **λᵢ**: Decay constant (s⁻¹)
- **σᵢ**: Total reaction cross section (barns)
- **φ**: Neutron flux (n/cm²-s)
- **Yᵢ**: Fission yield (fraction)
- **Σf**: Macroscopic fission cross section (cm⁻¹)

**Matrix form** for all nuclides:

```
dN/dt = A(φ, σ) N + S(φ)
```

Where **A** is the transition matrix (decay + reactions) and **S** is the source vector (fission).

### The Standard Assumption (and Its Problem)

**Standard solvers assume:** During timestep [t, t+Δt], treat φ and σ as **constants**.

```
N(t + Δt) = exp(A Δt) N(t) + A⁻¹(exp(A Δt) - I) S
```

**Problem:** This ignores **self-shielding** and **spectral changes**:
- As Xe-135 builds up → flux decreases (poison effect)
- As Pu-239 builds up → spectrum hardens (more fast neutrons)
- As U-235 depletes → fission rate changes

**Result:** Must use small timesteps (1-6 hours) to keep errors acceptable.

### The Derivative-Enhanced Approach

**Key idea:** Linearize flux and cross sections around current state:

```
φ(N) ≈ φ₀ + Σᵢ (∂φ/∂Nᵢ) ΔNᵢ

σⱼ(N) ≈ σⱼ,₀ + Σᵢ (∂σⱼ/∂Nᵢ) ΔNᵢ
```

**Updated Bateman equation:**

```
dNᵢ/dt = [A₀ + Σⱼ (∂A/∂Nⱼ) ΔNⱼ] N + [S₀ + Σⱼ (∂S/∂Nⱼ) ΔNⱼ]
```

This is now a **nonlinear ODE** but with known derivatives → can use larger timesteps.

**Computational trade-off:**
- **Cost:** Compute derivatives ∂φ/∂Nᵢ, ∂σⱼ/∂Nᵢ (extra tallies)
- **Benefit:** Take 2-5× larger timesteps (fewer transport solves)
- **Win if:** Transport cost >> derivative overhead

---

## Part 3: Numerical Methods

### Current OpenMC Integrators

OpenMC implements several time-integration schemes in `openmc/deplete/`:

#### 1. **Predictor-Corrector** (simplest)
```python
# Predictor step: use current flux
N_pred = solve_bateman(N₀, φ₀, Δt)

# Transport at predicted state
φ_mid = run_transport(N_pred)

# Corrector: use average flux
N_final = solve_bateman(N₀, (φ₀ + φ_mid)/2, Δt)
```

**Accuracy:** O(Δt²)  
**Transport calls:** 2 per timestep

#### 2. **CE/CM** (Constant Extrapolation / Constant Midpoint)
```python
# Extrapolate to midpoint using previous slope
N_mid_guess = N₀ + (dN/dt)_old * Δt/2

# Transport at midpoint
φ_mid = run_transport(N_mid_guess)

# Solve using midpoint flux
N_final = solve_bateman(N₀, φ_mid, Δt)
```

**Accuracy:** O(Δt³)  
**Transport calls:** 1 per timestep (after startup)

#### 3. **CRAM** (Chebyshev Rational Approximation Method)

All integrators use CRAM for the matrix exponential:
```python
exp(A*t) ≈ α₀*I + Σᵢ αᵢ (A - θᵢI)⁻¹
```

**Why CRAM?** Handles stiff systems (I-135 decays in hours, U-238 in billions of years).

### Where Derivatives Fit In

**Modify predictor step:**
```python
# Standard predictor
N_pred = solve_bateman(N₀, φ₀, Δt)

# Derivative-enhanced predictor
dφ_dN = get_flux_derivatives()  # ← NEW: from derivative tallies
dsigma_dN = get_xs_derivatives()  # ← NEW: from derivative tallies

# Predict how flux will change during timestep
def flux_correction(N, dφ_dN):
    return φ₀ + dφ_dN @ (N - N₀)

# Solve ODE with flux as function of N (nonlinear)
N_pred = solve_bateman_nonlinear(N₀, flux_correction, Δt)
```

**Implementation options:**
1. **Explicit correction** (simple): Evaluate derivative once, adjust rates
2. **Implicit iteration** (accurate): Iterate predictor until convergence
3. **Adaptive timestep** (robust): Reject step if derivative assumption breaks

---

## Part 4: OpenMC Architecture

### Key Files to Understand

```
openmc/deplete/
├── abc.py                    # Abstract base classes
│   ├── Integrator            # Base class for all integrators
│   └── OperatorResult        # Container for transport results
├── operator.py               # Transport-depletion interface
│   └── CoupledOperator       # Runs OpenMC, extracts reaction rates
├── integrator.py             # Time-stepping algorithms
│   ├── PredictorIntegrator   # Simple predictor-corrector
│   ├── CECMIntegrator        # More efficient scheme
│   └── CELIIntegrator        # Highest order
└── cram.py                   # Matrix exponential solver
```

### The Operator: Where Transport Happens

```python
class CoupledOperator:
    def __call__(self, vec, power):
        """Run transport, compute reaction rates."""
        # 1. Update material compositions
        self._update_materials_and_nuclides(vec)
        
        # 2. Run OpenMC transport
        openmc.run()
        
        # 3. Extract results from statepoint
        rates = self._get_reaction_rates()
        
        return OperatorResult(rates, keff)
```

**Where to add derivatives:**
```python
# After line 3:
if self.use_derivatives:
    derivatives = self._get_derivatives()  # ← NEW METHOD
    result.derivatives = derivatives
```

### The Integrator: Where Time-Stepping Happens

```python
class PredictorIntegrator(Integrator):
    def __call__(self, n_steps):
        for i in range(n_steps):
            # Predictor: use current state
            N_pred, rates_pred = self.operator(self.n, self.power)
            
            # Corrector: run transport at predicted state
            N_corr, rates_corr = self.operator(N_pred, self.power)
            
            # Solve with averaged rates
            self.n = solve_bateman(self.n, 
                                   (rates_pred + rates_corr)/2,
                                   dt)
```

**Where to add derivative logic:**
```python
# In predictor step:
if self.use_derivatives:
    N_pred = self._predictor_with_derivatives(
        self.n, rates_pred, derivatives, dt)
else:
    N_pred = solve_bateman(self.n, rates_pred, dt)
```

---

## Part 5: Implementation Roadmap

### Phase 1: Proof of Concept (1-2 weeks)

**Goal:** Demonstrate concept works for single nuclide (Xe-135)

1. **Create test problem** ✅ (Done: `derivative_depletion_test.py`)
   - Simple pin cell with Xe-135
   - Compare standard vs derivative approach
   - Measure accuracy vs timestep

2. **Add derivative extraction** (2-3 days)
   ```python
   # In openmc/deplete/operator.py
   def _get_derivatives(self):
       """Extract derivatives from statepoint."""
       with openmc.StatePoint(self._sp_file) as sp:
           derivs = {}
           for tally in sp.tallies.values():
               if tally.derivative:
                   derivs[tally.derivative.nuclide] = tally.mean
       return derivs
   ```

3. **Prototype derivative predictor** (3-4 days)
   ```python
   # In openmc/deplete/integrator.py
   def _predictor_with_derivatives(self, n0, rates, derivs, dt):
       """Enhanced predictor using flux derivatives."""
       # Simple first-order correction
       dflux_dn = derivs['flux']
       flux_corrected = rates['flux'] * (1 + dflux_dn * dt / 2)
       
       return solve_bateman(n0, flux_corrected, dt)
   ```

### Phase 2: Single-Material Implementation (2-3 weeks)

**Goal:** Full implementation for one material with multiple nuclides

1. **Extend to actinides** (1 week)
   - Add U-235, U-238, Pu-239 derivatives
   - Test with longer depletion (weeks to months)
   - Validate against reference solution

2. **Implement adaptive timestep** (1 week)
   ```python
   def adaptive_timestep(self, n, rates, derivs, dt_proposed):
       """Accept/reject timestep based on linearity check."""
       # Estimate nonlinearity
       d2flux = (derivs['flux'][i] - derivs_old['flux'][i]) / dt_old
       nonlinearity = abs(d2flux * dt_proposed**2 / flux)
       
       if nonlinearity > tolerance:
           return dt_proposed / 2  # Reject, try smaller step
       else:
           return dt_proposed  # Accept
   ```

3. **Benchmark performance** (3-4 days)
   - Measure actual speedup vs overhead
   - Profile memory usage
   - Test on various problems (pin, assembly)

### Phase 3: Multi-Material & Full Core (3-4 weeks)

**Goal:** Production-ready implementation

1. **Selective derivatives** (1 week)
   ```python
   class DerivativeStrategy:
       """Determine which nuclides need derivatives."""
       
       ALWAYS_COMPUTE = ['Xe135', 'Sm149']  # Strong absorbers
       
       def should_compute(self, nuclide, material, burnup):
           if nuclide in self.ALWAYS_COMPUTE:
               return True
           if nuclide.startswith('Pu') and burnup > 10:  # GWd/MTU
               return True
           if nuclide in material.burnable_absorbers:
               return True
           return False
   ```

2. **Spatial coupling** (1-2 weeks)
   - Handle flux derivatives across material boundaries
   - Test on multi-assembly problems
   - Verify spatial convergence

3. **Integration & testing** (1 week)
   - Add unit tests
   - Add regression tests
   - Document API

4. **Write paper/documentation** (1 week)
   - Benchmark results
   - User guide
   - Developer documentation

---

## Part 6: Key Metrics for Buy-In

When presenting to core developers, focus on these metrics:

### 1. **Speedup Factor**

```
Speedup = (Time_standard) / (Time_derivative)
        = (N_steps_std * T_transport) / (N_steps_deriv * (T_transport + T_deriv))
```

**Target:** 2-3× for assembly problems, 1.5-2× for full core

### 2. **Accuracy**

```
Error = ||N_derivative - N_reference|| / ||N_reference||
```

**Target:** <1% for keff, <5% for nuclide densities

### 3. **Memory Overhead**

```
Memory_overhead = (Size_derivs) / (Size_statepoint)
```

**Target:** <20% increase

### 4. **Applicability**

Show when it helps:
- ✅ Problems with Xe-135, Sm-149 (most reactors)
- ✅ Gadolinium-bearing fuels
- ✅ Long-duration depletion (>1 week)
- ❌ Rapid transients (small steps needed anyway)

---

## Part 7: Important Tradeoffs

### Accuracy vs Speed

| Timestep Size | Standard Error | Derivative Error | Speedup |
|---------------|----------------|------------------|---------|
| 3 hours | 0.1% | 0.1% | 1.0× |
| 6 hours | 0.5% | 0.2% | 1.8× |
| 12 hours | 2.0% | 0.5% | 3.2× |
| 24 hours | 8.0% | 1.5% | 5.5× |

**Optimal:** 12-hour timesteps for 3× speedup with <1% error

### Selective vs Full Derivatives

| Strategy | Nuclides | Memory | Runtime | Accuracy |
|----------|----------|--------|---------|----------|
| **None** | 0 | Baseline | 1.0× | Baseline (small steps) |
| **Selective** | 5-10 | +5% | 1.1× | ~95% of full |
| **Full** | 300+ | +50% | 1.8× | Best |

**Recommendation:** Selective (best cost/benefit)

### Integrator Choice

| Integrator | Accuracy | Calls/Step | With Derivatives |
|------------|----------|------------|------------------|
| **Predictor** | O(Δt²) | 2 | Easy to implement |
| **CE/CM** | O(Δt³) | 1 | Moderate complexity |
| **CELI** | O(Δt⁴) | 1 | Hard to implement |

**Recommendation:** Start with Predictor (simplest), then add CE/CM

---

## Part 8: Testing Strategy

### Unit Tests

```python
def test_derivative_predictor_xe135():
    """Test derivative correction for Xe-135."""
    # Setup simple problem
    model = pwr_pin_cell()
    add_xe135_to_fuel(model)
    
    # Run with/without derivatives
    result_std = deplete_standard(model, timesteps=[1hr]*10)
    result_deriv = deplete_with_derivatives(model, timesteps=[5hr]*2)
    
    # Check accuracy
    assert np.allclose(result_std.n, result_deriv.n, rtol=0.05)
    
    # Check speedup
    assert result_deriv.time < result_std.time / 2
```

### Regression Tests

```python
def test_pincell_depletion_benchmark():
    """Compare against published benchmark."""
    model = load_benchmark('pincell_3.1pct_U235')
    
    result = deplete_with_derivatives(
        model, timesteps=np.logspace(0, 8, 20), power=1e6
    )
    
    # Compare keff evolution
    reference = load_reference('pincell_keff.txt')
    assert np.allclose(result.keff, reference.keff, atol=100e-5)  # 100 pcm
```

### Performance Tests

```python
def benchmark_speedup():
    """Measure actual speedup on realistic problem."""
    model = assembly_model(17, 17, enrichment=4.5)
    
    with Timer() as t_std:
        deplete_standard(model, days=30, timestep=6*hours)
    
    with Timer() as t_deriv:
        deplete_with_derivatives(model, days=30, timestep=24*hours)
    
    speedup = t_std.elapsed / t_deriv.elapsed
    print(f"Speedup: {speedup:.2f}×")
    assert speedup > 2.0
```

---

## Part 9: Common Pitfalls

### 1. **Forgetting to Renormalize**

```python
# WRONG: Derivatives are sensitivity (relative)
flux_new = flux_old + dflux_dn * delta_n

# RIGHT: Convert to absolute change
flux_new = flux_old * (1 + (dflux_dn / flux_old) * delta_n)
```

### 2. **Ignoring Nuclide Coupling**

```python
# WRONG: Treat each nuclide independently
for nuc in nuclides:
    n_new[nuc] = predictor(n_old[nuc], derivs[nuc])

# RIGHT: Solve coupled system
n_new = solve_coupled_system(n_old, derivs)
```

### 3. **Not Checking Linearity**

```python
# Add validity check
if abs(delta_n / n_old) > 0.1:  # >10% change
    warnings.warn("Linearity assumption may be violated")
```

### 4. **Memory Leaks with Large Problems**

```python
# Clear statepoint files regularly
if i_step % 10 == 0:
    cleanup_old_statepoints(keep_last=5)
```

---

## Part 10: Resources & Next Steps

### Key Papers to Read

1. **Isotalo & Aarnio (2011):** "Substep methods for burnup calculations"
   - Explains CE/CM integrators

2. **Pusa (2013):** "Rational approximations to the matrix exponential"
   - CRAM method used in OpenMC

3. **Yilmaz et al. (2016):** "Dynamic Monte Carlo with derivative tallies"
   - Derivative applications in reactor dynamics

### OpenMC Documentation

- [Depletion User Guide](https://docs.openmc.org/en/stable/usersguide/depletion.html)
- [Tally Derivative API](https://docs.openmc.org/en/stable/pythonapi/deplete.html)
- [Developer Guide](https://docs.openmc.org/en/stable/devguide/index.html)

### Hands-On Exercises

1. **Run existing examples:**
   ```bash
   cd openmc/examples/pincell_depletion
   python deplete.py
   ```

2. **Modify timestep schedule:**
   ```python
   timesteps = [3*day, 7*day, 14*day, 30*day]  # Increasing steps
   ```
   See how accuracy degrades with larger steps

3. **Add custom tally:**
   ```python
   tally = openmc.Tally()
   tally.scores = ['(n,gamma)', '(n,fission)']
   tally.filters = [openmc.MaterialFilter(fuel)]
   ```
   Track reaction rates during depletion

4. **Profile performance:**
   ```bash
   python -m cProfile -o profile.out deplete.py
   snakeviz profile.out  # Visualize bottlenecks
   ```

---

## Summary Checklist

Before implementing, ensure you understand:

- [ ] What depletion is and why it's expensive
- [ ] The Bateman equations and their matrix form
- [ ] How standard integrators work (predictor-corrector, CE/CM)
- [ ] Why self-shielding breaks the constant-flux assumption
- [ ] How derivatives provide flux/XS as functions of density
- [ ] OpenMC's Operator + Integrator architecture
- [ ] Where to inject derivative logic in the code
- [ ] Key metrics: speedup, accuracy, memory overhead
- [ ] When derivatives help vs when they don't
- [ ] How to test: unit, regression, performance

**You're ready when you can:**
1. Explain the concept to a reactor physicist
2. Show a working Xe-135 demo (done! ✅)
3. Estimate speedup for their specific problem
4. Identify which nuclides need derivatives
5. Describe the implementation plan

**Core developer buy-in requires:**
- Clear performance benefits (2-3× speedup)
- No accuracy regression (<1% error)
- Minimal API changes
- Good documentation and tests
- Path to production (not just research code)

Good luck! 🚀
