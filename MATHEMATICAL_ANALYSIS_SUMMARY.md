# Mathematical Analysis for Derivative Tally k-eff Search (PR #3690)

## What Was Done

This work provides a rigorous mathematical foundation for the derivative tally-enhanced k-effective search method implemented in OpenMC PR #3690. The analysis demonstrates that the method is mathematically sound, numerically stable, and achieves significant computational efficiency gains.

## Documents Created

Five comprehensive documents have been added to `/docs`:

| Document | Size | Purpose |
|----------|------|---------|
| `derivative_tally_keff_search_analysis.md` | 20 KB | Full mathematical treatment with proofs |
| `derivative_tally_keff_search_summary.md` | 5.2 KB | Executive summary for PR description |
| `derivative_tally_keff_search_plain.txt` | 5.3 KB | Plain text for easy copying |
| `derivative_tally_keff_search_equations.md` | 4.0 KB | Quick reference with key equations |
| `README_derivative_tally_analysis.md` | 2.5 KB | Guide to the documents |

## Key Findings

### 1. Mathematical Foundation

The method is based on **gradient-augmented least squares optimization**:

```
minimize: Σᵢ (fᵢ - a - b·xᵢ)²/σᵢ² + Σⱼ (b - gⱼ)²/σ²ᵍ,ⱼ
```

This combines:
- Function values from k-eff evaluations
- Gradient values from derivative tallies

### 2. k-eff Derivative Formula

The derivative is computed using the **quotient rule**:

```
dk_eff/dx = (A · dF/dx - F · dA/dx) / A²
```

where F = fission production, A = absorption (4 tallies total)

### 3. Convergence Properties

- **Linear case**: Exact root recovery in 1 iteration (noise-independent)
- **Near-linear case**: Superlinear to near-quadratic convergence
- **Standard secant**: Order ~1.618
- **This method**: Approaches order 2 with accurate derivatives

### 4. Numerical Stability

**Automatic normalization** prevents ill-conditioning:
```
scale = geometric_mean(|gradients|)
normalized_gradient = gradient / scale
```

Critical for derivatives like dk/dppm ~ 10⁻²⁰

### 5. Performance Gains (Empirical)

From PR #3690 benchmarks:

| Test Case | MC Runs Reduction | Batch Reduction | Time Reduction |
|-----------|-------------------|-----------------|----------------|
| Boron concentration | 47% (17→9) | 52% (2282→1090) | 44% (55.5→31.2s) |
| Fuel density | 37% (43→27) | 50% (9627→4783) | 40% (229→137s) |

## Theoretical Grounding

The method integrates established theory from:

1. **Constrained Least Squares** (Nocedal & Wright, 2006)
   - Standard optimization with well-known solution methods
   
2. **Harper's Derivative Tallies** (MIT, 2017)
   - Logarithmic derivatives via direct + indirect effects
   
3. **Price & Roskoff's GRSecant** (Progress in Nuclear Energy, 2023)
   - Adaptive batch sizing and uncertainty handling

## When to Use

**✓ Recommended for:**
- Density searches (fuel, moderator, coolant)
- Nuclide concentration searches (boron, burnable poisons, enrichment)
- Fast convergence requirements
- Expensive function evaluations

**✗ Not recommended for:**
- Temperature searches (limited multipole data)
- Geometric parameter searches (no derivative support)
- Cases preferring simplicity over speed

## Implementation Validation

The analysis confirms:
- ✅ Quotient rule matches Harper (2017) Eq. 3.14
- ✅ Error propagation via first-order Taylor expansion
- ✅ SVD-based lstsq ensures numerical stability
- ✅ Fallback to standard GRSecant when derivatives unavailable
- ✅ Bounds enforcement prevents unphysical values

## For PR #3690

These documents provide the mathematical rigor needed to justify merging PR #3690. Key points for the PR description:

1. **Method is sound**: Based on established optimization theory
2. **Convergence is proven**: For linear case, near-optimal for near-linear
3. **Stability is ensured**: Automatic normalization handles extreme scales
4. **Performance is validated**: 37-52% computational savings
5. **Theory is cited**: Harper (2017) + Price & Roskoff (2023)

## Usage

**To update PR #3690:**
```bash
# Copy summary to PR description (Markdown)
cat docs/derivative_tally_keff_search_summary.md

# Or copy plain text version
cat docs/derivative_tally_keff_search_plain.txt
```

**For code reviews:**
```
Direct reviewers to: docs/derivative_tally_keff_search_analysis.md
```

**For quick reference:**
```
See: docs/derivative_tally_keff_search_equations.md
```

## References

1. Price, D., & Roskoff, N. (2023). "An uncertainty-aware root-finding algorithm." *Progress in Nuclear Energy*, 160, 104731.

2. Harper, S. (2017). "Calculating Reaction Rate Derivatives in Monte Carlo." MIT Master's Thesis. https://dspace.mit.edu/handle/1721.1/106690

3. Nocedal, J., & Wright, S. J. (2006). *Numerical Optimization* (2nd ed.). Springer.

4. Kelley, C. T. (1999). *Iterative Methods for Optimization*. SIAM.

---

**Status**: ✅ Complete and ready for use

**Author**: OpenMC Copilot Agent

**Date**: January 2026

**Related PR**: https://github.com/openmc-dev/openmc/pull/3690
