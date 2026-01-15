# Bezier and Generalized Basis Functional Expansion Tallies in OpenMC

## Overview

This implementation adds support for Bezier-based and generalized polynomial basis functional expansion tallies (FETs) to OpenMC, complementing the existing Zernike, Legendre, and Spherical Harmonics expansions.

## Motivation

Functional expansion tallies allow reconstruction of spatial distributions using orthogonal or non-orthogonal basis functions. Different basis functions have different strengths:

- **Zernike polynomials**: Optimal for circular/cylindrical domains (e.g., fuel pins)
- **Legendre polynomials**: Optimal for rectangular domains with smooth variations
- **Bezier (Bernstein) polynomials**: Better for rectangular domains with localized features
- **Chebyshev polynomials**: Excellent for minimizing interpolation error (Runge's phenomenon)

## Mathematical Background

### Bernstein Basis Polynomials

The Bernstein basis polynomials of degree n are defined as:

```
B_{i,n}(t) = C(n,i) * t^i * (1-t)^(n-i)
```

where C(n,i) is the binomial coefficient "n choose i", and t ∈ [0,1].

**Properties:**
1. **Partition of unity**: Σ B_{i,n}(t) = 1 for all t
2. **Non-negativity**: B_{i,n}(t) ≥ 0 for t ∈ [0,1]
3. **Endpoint interpolation**: B_{0,n}(0) = 1, B_{n,n}(1) = 1
4. **Symmetry**: B_{i,n}(t) = B_{n-i,n}(1-t)

For 2D rectangular domains, tensor products are used:
```
B_{i,j}(u,v) = B_{i,n_u}(u) * B_{j,n_v}(v)
```

### Chebyshev Polynomials

**First kind (T_n)**: Orthogonal on [-1,1] with weight 1/√(1-x²)
```
T_0(x) = 1
T_1(x) = x
T_{n+1}(x) = 2x*T_n(x) - T_{n-1}(x)
```

**Second kind (U_n)**: Orthogonal on [-1,1] with weight √(1-x²)
```
U_0(x) = 1
U_1(x) = 2x
U_{n+1}(x) = 2x*U_n(x) - U_{n-1}(x)
```

## Implementation Details

### C++ Components

#### New Files
- `include/openmc/tallies/filter_bezier.h`: Bezier filter declarations
- `src/tallies/filter_bezier.cpp`: Bezier filter implementation
- `include/openmc/tallies/filter_generic_basis.h`: Generic basis framework
- `src/tallies/filter_generic_basis.cpp`: Polynomial basis implementation

#### Mathematical Functions (`math_functions.cpp`)
- `calc_bernstein_basis()`: Efficient recursive computation of Bernstein polynomials
- `calc_bernstein_basis_2d()`: Tensor product for 2D domains
- `calc_chebyshev_t()`: Chebyshev polynomials (first kind)
- `calc_chebyshev_u()`: Chebyshev polynomials (second kind)

**Implementation Note**: The Bernstein basis uses a recursive algorithm inspired by Pascal's triangle, avoiding explicit computation of binomial coefficients and powers, improving numerical stability and performance.

### Python API

#### Filter Classes

**BezierFilter**: 2D Bezier expansion over rectangular domains
```python
from openmc.filter_expansion import BezierFilter

bezier = BezierFilter(
    order_u=3,        # Degree in x direction
    order_v=3,        # Degree in y direction
    x_min=-0.5,       # Domain bounds
    x_max=0.5,
    y_min=-0.5,
    y_max=0.5
)
```

**Bezier1DFilter**: 1D Bezier expansion along any axis
```python
from openmc.filter_expansion import Bezier1DFilter

bezier_1d = Bezier1DFilter(
    order=4,          # Polynomial degree
    axis='x',         # Axis: 'x', 'y', or 'z'
    minimum=-1.0,
    maximum=1.0
)
```

**PolynomialBasisFilter**: Generalized polynomial basis (C++ only for now)
- Supports Legendre, Chebyshev T, Chebyshev U polynomials
- 1D expansion along any axis

## Comparative Analysis Framework

### Bezier vs Zernike Comparison

| Feature | Zernike | Bezier |
|---------|---------|--------|
| Domain | Circular (r ≤ R) | Rectangular |
| Orthogonality | Orthogonal on unit disk | Not orthogonal |
| Boundary behavior | Smooth at boundary | Exact at corners |
| Number of terms | (n+1)(n+2)/2 | (n_u+1)(n_v+1) |
| Best for | Cylindrical symmetry | Rectangular geometry |
| Localization | Global | More local |

### Recommended Usage

**Use Zernike when:**
- Geometry has cylindrical/circular symmetry (fuel pins, assemblies)
- Smooth radial variations expected
- Minimizing number of expansion terms is important

**Use Bezier when:**
- Geometry is naturally rectangular
- Localized features or discontinuities present
- Edge/corner accuracy is critical
- Control over expansion degree per direction is needed

**Use Legendre when:**
- Smooth variations in rectangular geometry
- Orthogonality is important for analysis
- Want to match existing spatial Legendre implementation

**Use Chebyshev when:**
- Minimizing interpolation error is critical
- Dealing with polynomial interpolation problems
- Runge's phenomenon is a concern

## Testing and Validation

### Unit Tests
- `tests/unit_tests/test_bezier_filters.py`: 12 tests covering Python API
- `tests/unit_tests/test_basis_functions.py`: 5 tests comparing filter properties
- All tests passing ✓

### Regression Tests
- `tests/regression_tests/filter_bezier/`: Pin cell geometry test
  - Tests 2D Bezier expansion in xy-plane
  - Tests 1D expansions along x and z axes
  - Ready for reference data generation

### Performance Considerations

1. **Computational Cost**: 
   - Bernstein basis: O(n²) for degree n (using recursive algorithm)
   - Chebyshev: O(n) using recurrence
   - Both are comparable to existing Legendre implementation

2. **Memory Usage**:
   - Number of bins scales as (n+1) for 1D, (n_u+1)(n_v+1) for 2D
   - Similar to other expansion filters

## Future Work

1. **B-spline basis**: Extend to use cubic/higher-order B-splines for local support
2. **3D Bezier surfaces**: Extend to full 3D tensor products
3. **Adaptive refinement**: Implement h/p refinement for local accuracy
4. **Comparative benchmarks**: Quantitative comparison with Zernike on standard problems
5. **Python bindings**: Expose PolynomialBasisFilter to Python API
6. **User-defined basis**: Allow runtime specification of custom basis functions

## References

1. Kord Smith, "Reactor Physics Methods", Chapter on Functional Expansion Tallies
2. INL Report: "Bezier-based Functional Expansion Tallies" (Sort_139876.pdf)
3. MDPI Article: "Functional Expansion Tallies in Reactor Physics" 
   (https://www.mdpi.com/2673-4362/2/2/16)
4. OpenMC Documentation: https://docs.openmc.org

## Implementation Status

- ✅ C++ core implementation complete and building
- ✅ Python API for Bezier filters complete
- ✅ Unit tests passing (17 tests)
- ✅ Mathematical validation complete
- ⏳ Regression test reference data pending (requires nuclear data)
- ⏳ Comparative analysis with Zernike pending
- ⏳ Documentation and examples in progress

## Usage Example

```python
import openmc
from openmc.filter_expansion import BezierFilter

# Create a 2D Bezier tally for flux in a pin cell
bezier_filter = BezierFilter(
    order_u=3, order_v=3,
    x_min=-0.63, x_max=0.63,  # Pin pitch
    y_min=-0.63, y_max=0.63
)

tally = openmc.Tally()
tally.filters = [bezier_filter]
tally.scores = ['flux']
tally.estimator = 'tracklength'

# The tally will produce (3+1)*(3+1) = 16 bins
# representing Bezier expansion coefficients
```

## Contact

For questions or issues, please open an issue on the OpenMC GitHub repository.
