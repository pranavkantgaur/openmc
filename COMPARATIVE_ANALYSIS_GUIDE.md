# Comparative Analysis Guide: Bezier vs Zernike Functional Expansion Tallies

## Introduction

This guide outlines how to conduct a comparative analysis between Bezier-based and Zernike-based functional expansion tallies in OpenMC, as discussed in the research papers.

## Setup

### Prerequisites
```bash
# Ensure OpenMC is built with the new filters
cd /path/to/openmc
mkdir build && cd build
cmake .. -DOPENMC_USE_OPENMP=ON -DCMAKE_BUILD_TYPE=Release
make -j

# Install Python package
cd ..
pip install -e .

# Download nuclear data (if not already available)
bash tools/ci/download-xs.sh
export OPENMC_CROSS_SECTIONS=$HOME/nndc_hdf5/cross_sections.xml
```

## Test Case 1: PWR Pin Cell (Cylindrical Geometry)

### Hypothesis
Zernike should outperform Bezier in cylindrical geometry due to natural circular domain.

### Implementation

```python
import openmc
import numpy as np
import matplotlib.pyplot as plt
from openmc.filter_expansion import BezierFilter, ZernikeFilter

# Create standard PWR pin cell geometry
from openmc.examples import pwr_pin_cell
model = pwr_pin_cell()

# Set simulation parameters
model.settings.batches = 100
model.settings.inactive = 20
model.settings.particles = 10000

# Test different expansion orders
orders = [2, 3, 4, 5]
results = {'bezier': {}, 'zernike': {}}

for order in orders:
    # Bezier filter (square domain enclosing pin)
    bezier = BezierFilter(
        order_u=order, order_v=order,
        x_min=-0.65, x_max=0.65,
        y_min=-0.65, y_max=0.65
    )
    
    # Zernike filter (circular domain)
    zernike = ZernikeFilter(
        order=order,
        x=0.0, y=0.0, r=0.65
    )
    
    # Create tallies
    tally_bezier = openmc.Tally(name=f'bezier-{order}')
    tally_bezier.filters = [bezier]
    tally_bezier.scores = ['flux']
    
    tally_zernike = openmc.Tally(name=f'zernike-{order}')
    tally_zernike.filters = [zernike]
    tally_zernike.scores = ['flux']
    
    # Add to model and run
    model.tallies = [tally_bezier, tally_zernike]
    sp_file = model.run()
    
    # Extract and analyze results
    with openmc.StatePoint(sp_file) as sp:
        # Store expansion coefficients
        results['bezier'][order] = sp.get_tally(name=f'bezier-{order}').mean
        results['zernike'][order] = sp.get_tally(name=f'zernike-{order}').mean

# Analysis: Compare reconstruction quality, number of terms, etc.
```

## Test Case 2: Rectangular Assembly (Rectangular Geometry)

### Hypothesis
Bezier should perform better in rectangular geometry with sharp corners.

```python
# Create 3x3 pin assembly with rectangular outer boundary
pitch = 1.26
assembly_width = 3 * pitch

# Bezier filter matching rectangular boundary
bezier = BezierFilter(
    order_u=5, order_v=5,
    x_min=-assembly_width/2, x_max=assembly_width/2,
    y_min=-assembly_width/2, y_max=assembly_width/2
)

# Zernike with circumscribed circle
zernike = ZernikeFilter(
    order=5,
    x=0.0, y=0.0, 
    r=assembly_width/np.sqrt(2)  # Diagonal distance
)

# Compare accuracy near corners vs center
```

## Metrics for Comparison

### 1. Reconstruction Quality

Measure how well the expansion reproduces the actual flux distribution:

```python
def compute_reconstruction_error(expansion_coeffs, basis_functions, true_values):
    """
    Compute L2 error between reconstructed and true distribution.
    
    Parameters
    ----------
    expansion_coeffs : array
        Coefficients from FET
    basis_functions : callable
        Function to evaluate basis at points
    true_values : array
        Reference flux from fine mesh tally
    
    Returns
    -------
    float
        L2 norm of error
    """
    reconstructed = np.dot(expansion_coeffs, basis_functions)
    error = np.linalg.norm(reconstructed - true_values) / np.linalg.norm(true_values)
    return error
```

### 2. Number of Terms

For same accuracy, which requires fewer expansion terms?

```python
# Count non-negligible coefficients
def count_significant_terms(coeffs, threshold=0.01):
    """Count coefficients above relative threshold."""
    max_coeff = np.max(np.abs(coeffs))
    return np.sum(np.abs(coeffs) > threshold * max_coeff)
```

### 3. Computational Efficiency

```python
import time

# Measure tally time
start = time.time()
model.run()
elapsed = time.time() - start

# Compare overhead for different basis types
```

### 4. Statistical Uncertainty Propagation

```python
def analyze_uncertainty_propagation(sp, tally_name):
    """
    Analyze how statistical uncertainty in tallies propagates
    to expansion coefficients.
    """
    tally = sp.get_tally(name=tally_name)
    
    # Relative standard deviation
    rel_std = tally.std_dev / tally.mean
    
    # Coefficient of variation
    cv = np.std(rel_std) / np.mean(rel_std)
    
    return {
        'mean_rel_std': np.mean(rel_std),
        'max_rel_std': np.max(rel_std),
        'cv': cv
    }
```

## Analysis Workflow

### Step 1: Generate Reference Solution

```python
# Fine mesh tally as "truth"
mesh = openmc.RegularMesh()
mesh.lower_left = [-0.65, -0.65]
mesh.upper_right = [0.65, 0.65]
mesh.dimension = [50, 50]  # Fine mesh

mesh_filter = openmc.MeshFilter(mesh)
reference_tally = openmc.Tally(name='reference')
reference_tally.filters = [mesh_filter]
reference_tally.scores = ['flux']
```

### Step 2: Run Expansion Tallies

```python
# Run with both Bezier and Zernike
# Store expansion coefficients
```

### Step 3: Reconstruct and Compare

```python
def reconstruct_flux(coeffs, filter_type, evaluation_points):
    """
    Reconstruct flux at arbitrary points from expansion coefficients.
    
    Parameters
    ----------
    coeffs : array
        Expansion coefficients from tally
    filter_type : str
        'bezier' or 'zernike'
    evaluation_points : array (N, 2)
        Points at which to evaluate (x, y)
    
    Returns
    -------
    array
        Reconstructed flux values at points
    """
    if filter_type == 'bezier':
        # Evaluate Bernstein basis
        flux = evaluate_bernstein_expansion(coeffs, evaluation_points)
    elif filter_type == 'zernike':
        # Evaluate Zernike basis
        flux = evaluate_zernike_expansion(coeffs, evaluation_points)
    
    return flux

# Compare with reference
error_bezier = compute_error(reconstructed_bezier, reference)
error_zernike = compute_error(reconstructed_zernike, reference)
```

### Step 4: Visualization

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# Reference
axes[0, 0].imshow(reference_flux)
axes[0, 0].set_title('Reference (Fine Mesh)')

# Bezier reconstruction
axes[0, 1].imshow(bezier_reconstruction)
axes[0, 1].set_title(f'Bezier (order {order})')

# Zernike reconstruction
axes[0, 2].imshow(zernike_reconstruction)
axes[0, 2].set_title(f'Zernike (order {order})')

# Errors
axes[1, 0].imshow(np.abs(reference_flux - reference_flux))
axes[1, 1].imshow(np.abs(bezier_reconstruction - reference_flux))
axes[1, 2].imshow(np.abs(zernike_reconstruction - reference_flux))

plt.savefig('comparison.png')
```

## Expected Results

### Circular Geometry (Pin Cell)
- **Zernike**: Lower error, fewer terms needed
- **Bezier**: Higher error near boundary, more terms needed
- **Conclusion**: Zernike is superior for cylindrical geometry

### Rectangular Geometry (Assembly)
- **Bezier**: Better corner accuracy, natural domain match
- **Zernike**: Boundary artifacts, wasted terms outside circle
- **Conclusion**: Bezier is superior for rectangular geometry

### Edge Cases
- **Sharp gradients**: Bezier may have better local control
- **Smooth variations**: Legendre/Zernike orthogonality advantage
- **Mixed geometry**: Problem-dependent, need testing

## Performance Benchmarks

```python
# Create benchmark suite
benchmarks = {
    'pin_cell_zernike': {...},
    'pin_cell_bezier': {...},
    'assembly_zernike': {...},
    'assembly_bezier': {...},
}

# Run and collect timing data
for name, config in benchmarks.items():
    times = []
    for _ in range(5):  # Multiple runs
        start = time.time()
        run_simulation(config)
        times.append(time.time() - start)
    
    benchmarks[name]['time'] = {
        'mean': np.mean(times),
        'std': np.std(times)
    }
```

## Conclusion

This comparative analysis framework enables quantitative comparison of Bezier and Zernike FETs. The results should guide users in selecting the appropriate basis for their specific geometry and analysis requirements.

## Next Steps

1. Implement full test suite with multiple geometries
2. Generate publication-quality figures
3. Write technical report with results
4. Submit as OpenMC example/documentation
5. Consider publishing comparison study

## References

- INL-EXT-22-66803: "Comparison of Functional Expansion Tally Bases"
- MDPI Energies: "Functional Expansion Tallies for Reactor Physics"
- OpenMC Documentation: Filter Types
