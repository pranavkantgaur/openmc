# Quick Reference: Key Equations for Derivative Tally k-eff Search

## Core Equations

### k-eff Derivative (Quotient Rule)
```
dk_eff/dx = (A · dF/dx - F · dA/dx) / A²

where:
  F = fission production tally (nu-fission)
  A = absorption tally
  dF/dx = derivative nu-fission tally
  dA/dx = derivative absorption tally
```

### Gradient-Augmented Least Squares Objective
```
minimize: Σᵢ (fᵢ - a - b·xᵢ)²/σᵢ² + Σⱼ (b - gⱼ)²/σ²ᵍ,ⱼ

where:
  (xᵢ, fᵢ, σᵢ) = function evaluations
  gⱼ = df/dx gradient at xⱼ
  σᵍ,ⱼ = gradient uncertainty
  f(x) = a + bx = linear fit
```

### Root Prediction
```
x_next = -a/b
```

### Derivative Normalization Scale
```
s = geometric_mean(|gⱼ|) for gⱼ ≠ 0
g̃ⱼ = gⱼ / s
σ̃ᵍ,ⱼ = σᵍ,ⱼ / s
```

### Adaptive Uncertainty Target (from GRSecant)
```
σ_target,n+1 = q · σ_final · (min|fᵢ| / k_tol)ᵖ

where:
  q = 0.95 (safety factor)
  p = 0.5 (exponent)
  σ_final = max acceptable uncertainty
  k_tol = convergence tolerance
```

### Batch Size Estimation
```
σ ≈ k / √B
B_next = (k / σ_target)²

where:
  k = estimated from ln(σ) vs ln(B) fit
  B = number of batches
```

## Matrix Formulation

### Augmented System: Ac = b

```
A = [1/σ₁   x₁/σ₁  ]     b = [f₁/σ₁        ]     c = [a]
    [  ⋮       ⋮    ]         [  ⋮          ]         [b]
    [1/σₙ   xₙ/σₙ  ]         [fₙ/σₙ        ]
    [ 0       1    ]         [g₁/σᵍ,₁      ]
    [ ⋮       ⋮    ]         [  ⋮          ]
    [ 0       1    ]         [gₙ_g/σᵍ,ₙ_g  ]

Solution: c = (AᵀA)⁻¹Aᵀb
```

## Derivative Types

### Nuclide Density (number density N in atoms/cm³)
```
For single nuclide score:
  (1/c)(∂c/∂N)|_φ = 1/N

For total material score:
  (1/c)(∂c/∂N)|_φ = σ_nuclide / Σ_total
```

### Material Density (ρ in g/cm³)
```
(1/c)(∂c/∂ρ)|_φ = 1/ρ
```

### Parameter Conversion
```
If OpenMC gives dk/dN but you search over x:
  dk/dx = (dk/dN) · (dN/dx)

Example for boron ppm:
  N = (ppm × 10⁻⁶ × ρ_water × N_A) / M_boron
  dN/dx = (10⁻⁶ × ρ_water × N_A) / M_boron
```

## Uncertainty Propagation

### First-Order Taylor Expansion
```
For k = F/A:
  σ²ₖ ≈ (∂k/∂F)² σ²_F + (∂k/∂A)² σ²_A

For dk/dx:
  σ²_{dk/dx} ≈ (∂/∂F)² σ²_F + (∂/∂A)² σ²_A + 
               (∂/∂(dF/dx))² σ²_{dF/dx} + 
               (∂/∂(dA/dx))² σ²_{dA/dx}
```

## Convergence Criteria

```
Converged when BOTH:
  |f(x)| = |k_eff - k_target| ≤ k_tol
  σ ≤ σ_final

Typical values:
  k_tol = 1×10⁻⁴ (100 pcm)
  σ_final = 3×10⁻⁴ (300 pcm)
```

## Implementation Notes

### Python Code Structure
```python
# Add derivative tallies (automatic)
model.add_derivative_tallies(deriv_variable, deriv_material, deriv_nuclide)

# Extract dk/dx from StatePoint
dk_dx = model._extract_derivative_constraint(sp, ...)

# Augmented least squares
A = np.vstack([point_rows, gradient_rows])
b_vec = np.hstack([point_targets, gradient_targets])
coeffs = np.linalg.lstsq(A, b_vec)[0]
a, b = coeffs[0], coeffs[1]

# Next evaluation point
x_next = -a/b
x_next = clamp(x_next, x_min, x_max)
```

### C++ Derivative Application
```cpp
// In apply_derivative_to_score():
score *= flux_deriv + (1/c) * (∂c/∂x)|_φ

where flux_deriv = d(ln φ)/dx
```

## Typical Performance

### Without Derivatives (GRSecant baseline)
- Boron search: 17 MC runs, 2282 batches, 55.5s
- Fuel density search: 43 MC runs, 9627 batches, 229s

### With Derivatives (This method)
- Boron search: 9 MC runs, 1090 batches, 31.2s (47% fewer runs)
- Fuel density search: 27 MC runs, 4783 batches, 137s (37% fewer runs)

## References

Full derivations in:
- `derivative_tally_keff_search_analysis.md` (complete mathematical treatment)
- `derivative_tally_keff_search_summary.md` (executive summary)

Sources:
- Price & Roskoff (2023): GRSecant algorithm
- Harper (2017): Derivative tally theory
- Nocedal & Wright (2006): Optimization theory
