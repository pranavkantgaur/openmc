# Review of keff_search Implementation

## Executive Summary

This document provides a comprehensive review of the `keff_search` implementation in `openmc/model/model.py`, addressing questions about the GRsecant method, comparison with least squares approaches, and considerations for multivariate k_eff search.

## 1. Current Implementation: GRsecant Method

### Overview
The current `keff_search` implementation uses the **GRsecant method** from Price and Roskoff (2023), which is specifically designed for uncertainty-aware criticality searches. The method combines:
- Weighted least squares linear regression for next-point prediction
- Adaptive batch sizing based on uncertainty targets
- Memory-based approach using recent evaluations

### Key Components

#### 1.1 Weighted Linear Regression (Lines 2549-2552)
```python
(a, b), _ = curve_fit(
    lambda x, a, b: a + b*x,
    xs[-m:], fs[-m:], sigma=ss[-m:], absolute_sigma=True
)
x_new = float(-a / b)
```

**Analysis:**
- Uses `scipy.optimize.curve_fit` with weighted least squares
- Fits linear model: f(x) = a + bx
- Weights based on uncertainties (sigma values)
- `absolute_sigma=True` ensures proper uncertainty weighting
- Predicts next point as x_new = -a/b (root of linear function)

**Correctness:** ✅ **CORRECT**
- The implementation correctly applies weighted least squares
- Properly accounts for measurement uncertainties in Monte Carlo simulations
- Minimizes chi-squared: χ² = Σ[(f_i - (a + b*x_i))²/σ_i²]

#### 1.2 Adaptive Batch Sizing (Lines 2572-2582)
```python
if len(gs) >= 2 and np.var(np.log(gs)) > 0.0:
    (ln_k,), _ = curve_fit(
        lambda ln_b, ln_k: ln_k - 0.5*ln_b,
        np.log(gs[-4:]), np.log(ss[-4:]),
    )
    k = float(np.exp(ln_k))
else:
    k = float(ss[-1] * math.sqrt(gs[-1]))
```

**Analysis:**
- Estimates relationship between batches and uncertainty: σ ∝ k/√b
- Uses log-transformed regression: ln(σ) = ln(k) - 0.5*ln(b)
- Falls back to simple estimate if insufficient data
- Fixed r=0.5 (assumes 1/√N convergence)

**Potential Issue:** ⚠️ **MINOR CONCERN**
- Hardcoded r=0.5 may not be optimal for all problems
- Uses last 4 points only (gs[-4:]) which may be sensitive to outliers
- No error handling if curve_fit fails

#### 1.3 Convergence Criteria (Lines 2594-2596)
```python
if abs(f_new) <= k_tol and s_new <= sigma_final:
    return SearchResult(x_new, xs, fs, ss, gs, True, "converged")
```

**Analysis:**
- Dual criteria: both function value AND uncertainty must meet tolerances
- Ensures statistical significance of result
- Conservative approach suitable for safety-critical applications

**Correctness:** ✅ **CORRECT**

## 2. Comparison with Standard Least Squares

### Standard Least Squares (Hypothetical Implementation)
A standard least squares approach would:
1. Fit polynomial or other model to (x, keff) pairs
2. Not account for uncertainties in keff measurements
3. Use equal weighting for all points
4. Not adapt batch sizes

### GRsecant vs. Standard Least Squares

| Aspect | GRsecant (Current) | Standard Least Squares |
|--------|-------------------|------------------------|
| **Uncertainty Handling** | ✅ Explicitly accounts for MC uncertainties | ❌ Ignores uncertainties |
| **Batch Adaptation** | ✅ Adapts batches to reduce uncertainty | ❌ Fixed batch sizes |
| **Efficiency** | ✅ Optimal batch allocation | ❌ Potentially wasteful |
| **Convergence** | ✅ Guarantees uncertainty bounds | ❌ No uncertainty guarantee |
| **Complexity** | Medium | Low |
| **Robustness** | ✅ Handles noisy data well | ❌ Sensitive to noise |

### For Boron-10 Concentration Search

**Question:** Is the search for the same parameter (boron-10 concentration) in both methods?

**Answer:** Yes, both methods should search for the same physical parameter (boron-10 concentration). The difference is in HOW they search:

1. **GRsecant**: 
   - Accounts for Monte Carlo statistical uncertainty
   - Adapts sampling to reduce uncertainty where needed
   - More efficient for expensive function evaluations

2. **Standard Least Squares**:
   - Would fit a curve through (concentration, keff) points
   - Treats all evaluations equally regardless of uncertainty
   - May require more evaluations to achieve same confidence

**Fair Comparison Requirements:**
- Same initial guesses (x0, x1)
- Same target keff value
- Same tolerance requirements (k_tol)
- Same total computational budget (batches or particles)
- Same model modification function

## 3. Multivariate k_eff Search

### Problem Formulation
Multivariate search involves finding multiple parameters simultaneously:
- Example: Optimize both boron concentration AND enrichment
- Goal: Find (x₁, x₂, ..., xₙ) such that keff(x₁, x₂, ..., xₙ) = target

### GRsecant Extension for Multivariate

**Pros:**
1. ✅ Natural extension using multivariate weighted regression
2. ✅ Maintains uncertainty awareness
3. ✅ Adaptive batch sizing still applicable
4. ✅ Memory-based approach works with gradient estimation

**Cons:**
1. ❌ Requires more function evaluations (curse of dimensionality)
2. ❌ Linear model may be inadequate (need higher-order terms)
3. ❌ Convergence becomes more complex
4. ❌ Initial guesses required for each dimension

**Implementation Approach:**
```python
# Multivariate weighted linear regression
# Fit: f(x₁, x₂, ..., xₙ) = a₀ + a₁x₁ + a₂x₂ + ... + aₙxₙ

# Would need to solve:
# ∇f = 0
# Subject to constraints on x₁, x₂, ..., xₙ
```

### Standard Least Squares for Multivariate

**Pros:**
1. ✅ Well-established methods (Levenberg-Marquardt, etc.)
2. ✅ Can use response surface methodology
3. ✅ Easier to implement with existing libraries
4. ✅ Can incorporate gradient information if available

**Cons:**
1. ❌ Does not handle Monte Carlo uncertainty properly
2. ❌ No adaptive batch sizing
3. ❌ May require many evaluations to build response surface
4. ❌ Sensitive to noise in high dimensions

### Recommendation for Multivariate

**Best Approaches:**

1. **Bayesian Optimization** ⭐ RECOMMENDED
   - Pros:
     * Naturally handles uncertainty (Gaussian process model)
     * Acquisition functions balance exploration/exploitation
     * Efficient for expensive black-box functions
     * Works well in 2-10 dimensions
     * Available in libraries: scikit-optimize, GPyOpt, BoTorch
   - Cons:
     * More complex to implement
     * Requires careful tuning of hyperparameters
     * Computational overhead for GP fitting

2. **Trust Region Methods**
   - Pros:
     * Robust convergence properties
     * Can use derivative-free approaches
     * Well-suited for noisy functions
   - Cons:
     * Requires many function evaluations
     * May struggle with high dimensionality

3. **Gradient-Free Optimization with Uncertainty**
   - Methods like SNOBFIT (Stable Noisy Optimization by Branch and Fit)
   - Pros:
     * Designed for noisy objective functions
     * Good for low-dimensional problems (< 5 variables)
   - Cons:
     * Less efficient than Bayesian optimization

## 4. Bayesian Optimization Analysis

### Would Bayesian Search Converge Faster?

**Answer:** ✅ **YES, FOR MOST CASES**

### Bayesian Optimization Overview

Bayesian optimization uses:
1. **Gaussian Process (GP)** surrogate model of f(x)
2. **Acquisition function** to select next evaluation point
3. **Uncertainty quantification** naturally built-in

### Convergence Comparison

| Method | Convergence Rate | Typical Iterations | Best Use Case |
|--------|-----------------|-------------------|---------------|
| **GRsecant** | Linear (secant-like) | 5-15 | 1D problems, local search |
| **Bayesian Opt** | Sub-linear (GP-based) | 10-50 | Multi-D, global search |
| **Standard LS** | Linear | 10-30 | Smooth functions, known form |

### When Bayesian Optimization is Better:

1. ✅ **Multivariate problems** (2+ dimensions)
   - GP naturally extends to multiple dimensions
   - Acquisition functions handle exploration vs exploitation

2. ✅ **Global search needed**
   - Can find global optimum, not just local
   - Exploration-exploitation tradeoff

3. ✅ **Limited evaluation budget**
   - Each evaluation is expensive (Monte Carlo simulation)
   - Bayesian opt is sample-efficient

4. ✅ **Unknown function form**
   - No assumption about linearity
   - GP can model complex response surfaces

5. ✅ **Noisy evaluations**
   - GP naturally handles measurement noise
   - Can incorporate heteroscedastic noise (varying uncertainty)

### When GRsecant is Better:

1. ✅ **1D problems** (single parameter)
   - Simpler, faster convergence
   - Less overhead

2. ✅ **Local search with good initial guess**
   - Secant method is efficient near solution
   - Linear assumption often valid locally

3. ✅ **Simple implementation needed**
   - No external dependencies beyond scipy
   - Easier to debug and understand

4. ✅ **Guaranteed convergence properties**
   - Well-studied theoretical properties
   - Predictable behavior

## 5. Recommendations

### For Current Implementation (1D search):

1. **Keep GRsecant as default** ✅
   - Well-suited for single-parameter criticality searches
   - Handles uncertainty correctly
   - Efficient for local search

2. **Add optional Bayesian optimization** 📝 ENHANCEMENT
   - Provide as alternative method parameter
   - Use for global search or when initial guess is poor
   - Implementation using scikit-optimize or GPyOpt

3. **Improve robustness** 📝 RECOMMENDED
   - Add try-except for curve_fit failures
   - Add bounds checking on fitted parameters
   - Add option to vary r parameter (currently fixed at 0.5)
   - Use more than 4 points for batch estimation

### For Multivariate Extensions:

1. **Implement Bayesian Optimization** ⭐ PRIORITY
   ```python
   def keff_search_multivariate(
       self,
       func: ModelModifier,
       x0: np.ndarray,
       bounds: list[tuple[float, float]],
       method: str = 'bayesian',  # or 'grsecant', 'trust-region'
       ...
   ) -> SearchResult
   ```

2. **Alternative: Extend GRsecant** 📝 OPTION
   - Use multivariate linear model
   - Estimate gradient via finite differences
   - Line search in gradient direction
   - More work but maintains consistency

3. **Consider hybrid approach** 💡 FUTURE
   - Use Bayesian opt for global exploration
   - Switch to GRsecant for local refinement
   - Best of both worlds

## 6. Code Issues Found

### Critical Issues: None ✅

### Minor Issues:

1. **Line 2578: Limited history for batch estimation**
   ```python
   np.log(gs[-4:]), np.log(ss[-4:])  # Only last 4 points
   ```
   **Recommendation:** Use `min(len(gs), 8)` or make configurable

2. **Line 2576-2580: No error handling**
   ```python
   (ln_k,), _ = curve_fit(...)  # May fail
   ```
   **Recommendation:** Add try-except with fallback

3. **Line 2549-2552: No check for b ≈ 0**
   ```python
   x_new = float(-a / b)  # Division by zero if b ≈ 0
   ```
   **Recommendation:** Check if abs(b) < epsilon, use bisection instead

4. **Fixed r=0.5 assumption**
   - May not be optimal for all problem types
   **Recommendation:** Make configurable or estimate from data

## 7. Conclusions

### For Boron Search Comparison:
- Both methods search the same parameter (boron-10 concentration)
- Fair comparison requires same initial conditions and computational budget
- GRsecant should be more efficient due to uncertainty handling

### For Multivariate k_eff Search:
- **Bayesian Optimization** is the superior choice for 2+ dimensions
- Would converge faster due to:
  * Better handling of high-dimensional spaces
  * Intelligent exploration-exploitation balance
  * No linearity assumptions
  * Natural uncertainty quantification
- GRsecant can be extended but becomes less efficient in high dimensions
- Hybrid approaches offer best of both worlds

### Overall Assessment:
The current GRsecant implementation is **correct and well-designed** for 1D criticality searches. The weighted least squares approach properly handles Monte Carlo uncertainty, and the adaptive batch sizing is an elegant solution to minimize computational cost while meeting accuracy requirements.

## References

1. Price and Roskoff (2023), "A Generalized Regula-Falsi (GRsecant) Method for Criticality Searches", Progress in Nuclear Energy
2. Shahriari et al. (2016), "Taking the Human Out of the Loop: A Review of Bayesian Optimization", Proceedings of the IEEE
3. Snoek et al. (2012), "Practical Bayesian Optimization of Machine Learning Algorithms", NIPS
