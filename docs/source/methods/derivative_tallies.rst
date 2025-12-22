.. _methods_derivative_tallies:

===================
Derivative Tallies
===================

Overview
========

OpenMC implements first-order derivative tallies that compute sensitivities of
tally scores with respect to material perturbations. These derivatives are
computed during particle transport by propagating weight derivatives through
the Monte Carlo simulation, allowing users to obtain both a tally value and
its derivative with respect to various material parameters in a single run.

The derivative tally capability was introduced in version 0.9.0 and enables
efficient sensitivity and uncertainty quantification, as well as
derivative-accelerated criticality searches and depletion calculations.

Implemented Derivative Methods
===============================

OpenMC currently implements three types of material perturbation derivatives:

1. **Density Derivatives** (``'density'``)
2. **Nuclide Density Derivatives** (``'nuclide_density'``)
3. **Temperature Derivatives** (``'temperature'``)

Each derivative type computes how tally scores change with respect to a
specific material property perturbation. The derivatives are computed as
**logarithmic derivatives**: :math:`\frac{1}{R} \frac{\partial R}{\partial x}`,
where :math:`R` is a reaction rate and :math:`x` is the perturbation variable.

1. Density Derivatives
-----------------------

**Description**

Computes the derivative of tally scores with respect to material mass density in
units of g/cm³. This represents how scores change when the overall material
density is perturbed while maintaining constant composition ratios.

**Mathematical Form**

For a material with mass density :math:`\rho`:

.. math::

   \frac{\partial R}{\partial \rho} = \frac{\partial R}{\partial N} \frac{\partial N}{\partial \rho}

where :math:`N` is the total atom density and :math:`R` is a reaction rate.

**Supported Scores**

- Flux (``'flux'``)
- Total cross section (``'total'``)
- Scatter (``'scatter'``)
- Absorption (``'absorption'``)
- Fission (``'fission'``)
- Nu-fission (``'nu-fission'``)

**Supported Estimators**

- Analog estimator
- Collision estimator

**Usage Example**

.. code-block:: python

   import openmc

   # Create a density derivative for material 1
   deriv = openmc.TallyDerivative(derivative_id=1)
   deriv.variable = 'density'
   deriv.material = 1

   # Apply to a tally
   tally = openmc.Tally()
   tally.scores = ['flux', 'fission']
   tally.filters = [openmc.MaterialFilter([1])]
   tally.derivative = deriv

**Pros**

- Simple to implement and interpret
- Applicable to all materials (fissile and non-fissile)
- No special nuclear data requirements
- Works with standard cross section libraries
- Useful for material densification/swelling studies

**Cons**

- Cannot distinguish between different nuclides in a material
- Less useful for detailed composition sensitivity studies
- Changes all nuclides proportionally (may not be physically realistic)

**Applications**

- Fuel densification/swelling analysis
- Material density optimization
- Reactivity coefficient calculations
- Uncertainty quantification for manufacturing tolerances

--------

2. Nuclide Density Derivatives
-------------------------------

**Description**

Computes the derivative of tally scores with respect to a specific nuclide's
atom density in units of atoms/(barn·cm). This allows sensitivity analysis for
individual isotopes within a material.

**Mathematical Form**

For a nuclide with atom density :math:`N_i`:

.. math::

   \frac{\partial R}{\partial N_i} = \frac{\partial \phi}{\partial N_i} \sigma_i N_i + 
   \phi \sigma_i

where :math:`\phi` is the neutron flux and :math:`\sigma_i` is the microscopic
cross section for nuclide :math:`i`.

**Supported Scores**

- Flux (``'flux'``)
- Total cross section (``'total'``)
- Scatter (``'scatter'``)
- Absorption (``'absorption'``)
- Fission (``'fission'``)
- Nu-fission (``'nu-fission'``)

**Supported Estimators**

- Analog estimator
- Collision estimator

**Usage Example**

.. code-block:: python

   import openmc

   # Create a nuclide density derivative for B-10 in material 3
   deriv = openmc.TallyDerivative(derivative_id=2)
   deriv.variable = 'nuclide_density'
   deriv.material = 3
   deriv.nuclide = 'B10'

   # Apply to a tally
   tally = openmc.Tally()
   tally.scores = ['absorption', 'nu-fission']
   tally.filters = [openmc.MaterialFilter([3])]
   tally.derivative = deriv

**Pros**

- Isotope-specific sensitivity information
- Essential for criticality searches (e.g., boron concentration)
- Useful for fuel cycle optimization
- Can track individual fission products or actinides
- Enables selective derivative computation (computational efficiency)

**Cons**

- Requires specification of individual nuclides
- More complex to set up for many nuclides
- May need unit conversions (e.g., ppm to atoms/barn-cm)
- Computational overhead scales with number of tracked nuclides

**Applications**

- Critical boron concentration search
- Xenon/Samarium worth calculations
- Reactivity coefficient determination
- Fuel composition optimization
- Depletion calculations with self-shielding correction
- Burnable poison optimization

--------

3. Temperature Derivatives
---------------------------

**Description**

Computes the derivative of tally scores with respect to material temperature
in units of Kelvin. This captures Doppler broadening effects on cross sections
in the resolved resonance range.

**Mathematical Form**

For a material at temperature :math:`T`:

.. math::

   \frac{\partial R}{\partial T} = \frac{\partial \phi}{\partial T} \sigma(T) N + 
   \phi \frac{\partial \sigma(T)}{\partial T} N

where the cross section derivative :math:`\frac{\partial \sigma(T)}{\partial T}`
is computed using windowed multipole (WMP) data.

**Supported Scores**

- Flux (``'flux'``)
- Total cross section (``'total'``)
- Scatter (``'scatter'``)
- Absorption (``'absorption'``)
- Fission (``'fission'``)
- Nu-fission (``'nu-fission'``)

**Supported Estimators**

- Analog estimator
- Collision estimator

**Usage Example**

.. code-block:: python

   import openmc

   # Create a temperature derivative for material 1
   deriv = openmc.TallyDerivative(derivative_id=3)
   deriv.variable = 'temperature'
   deriv.material = 1

   # Enable windowed multipole
   settings.temperature['multipole'] = True

   # Apply to a tally
   tally = openmc.Tally()
   tally.scores = ['flux', 'fission']
   tally.filters = [openmc.MaterialFilter([1])]
   tally.derivative = deriv

**Pros**

- Captures physics of Doppler broadening
- Important for reactor safety analysis
- Useful for temperature coefficient calculations
- Can predict reactivity feedback effects

**Cons**

- **REQUIRES windowed multipole (WMP) data** - standard tabulated cross sections do not support analytical temperature derivatives
- **Limited energy range** - only valid in resolved resonance range (~1 eV to ~10 keV)
- **Sparse data availability** - few nuclides have WMP data in standard libraries
- **Does NOT account for**:
  
  - Thermal expansion (geometry changes)
  - S(α,β) thermal scattering changes
  - Resonance scattering temperature dependence  
  - Unresolved resonance Doppler broadening
  
- **Not compatible with temperature interpolation** - if using ``settings.temperature_method = 'interpolation'``, derivatives are not computed from interpolation
- **Approximate scattering treatment** - assumes :math:`\frac{\partial P(E' \to E)}{\partial T} = 0`, which introduces 2-5% errors near resonances

**Applications**

- Doppler coefficient calculations (with significant limitations)
- Temperature feedback analysis (resolved resonance range only)
- Reactor kinetics studies (limited applicability)

**Important Note**

Due to the severe limitations listed above, temperature derivatives are **NOT
recommended for practical k-eff searches or most reactor applications**. Use
density or nuclide density derivatives instead for temperature-related searches
by parameterizing material properties as functions of temperature.

Implementation Details
======================

Flux Derivative Propagation
----------------------------

OpenMC propagates flux derivatives through particle histories by tracking how
perturbations affect:

1. **Transport (tracking)**: During particle flight, derivatives are updated based on how cross sections change:

   .. math::
   
      \frac{\partial \phi}{\partial x} \rightarrow \frac{\partial \phi}{\partial x} - 
      \phi \frac{\partial \Sigma_t}{\partial x} \Delta s

   where :math:`\Delta s` is the path length and :math:`\Sigma_t` is the total macroscopic cross section.

2. **Collisions (scattering)**: After scattering events, derivatives are updated based on scattering cross section changes:

   .. math::
   
      \frac{\partial \phi}{\partial x} \rightarrow \frac{\partial \phi}{\partial x} + 
      \phi \frac{\partial \Sigma_s}{\partial x} / \Sigma_s

3. **Score adjustments**: When tallying, scores are multiplied by :math:`1 + \frac{\partial c}{\partial x}`, where :math:`c` is the score-specific cross section.

This approach follows the methodology described in:

- Harper, S. M. (2016). "Calculating Reaction Rate Derivatives in Monte Carlo Neutron Transport." MIT Master's Thesis.

Computational Cost
------------------

Derivative tally overhead consists of:

- **Memory**: ~1.5-2× per derivative tally (stores flux derivatives)
- **Runtime**: Minimal additional cost (~5-15% overhead for typical cases)
- **Parallel efficiency**: Excellent scaling with MPI (derivatives are local)

For full-core problems with selective derivatives (tracking only strong absorbers
like Xe-135, Sm-149, and actinides), expect ~10-20% total overhead.

Limitations and Restrictions
=============================

General Limitations
-------------------

1. **Multi-group mode not supported** - derivatives only work in continuous-energy mode
2. **Estimator restrictions** - only analog and collision estimators are supported (no tracklength)
3. **Small perturbation assumption** - assumes perturbations don't significantly change fission source distribution
4. **Limited score support** - not all tally scores have derivative implementations
5. **Single material perturbation** - each derivative perturbs one material at a time

Score-Specific Limitations
---------------------------

Not all scores support derivatives. Currently **unsupported** scores include:

- Current tallies
- Energy deposition (``'heating'``)
- Damage energy (``'damage-energy'``)
- Photon production scores
- Custom scores via ``'(n,x)'`` MT reactions (other than standard reactions)

Estimator Requirements
----------------------

- **Tracklength estimator**: NOT supported for derivatives
- **Analog estimator**: Fully supported
- **Collision estimator**: Fully supported

Comparison with Perturbation Methods
=====================================

Derivative tallies provide an alternative to traditional perturbation methods:

+--------------------------+---------------------------+---------------------------+
| Feature                  | Derivative Tallies        | Finite Difference         |
+==========================+===========================+===========================+
| Accuracy                 | Exact (within MC          | O(Δx) or O(Δx²)           |
|                          | statistics)               |                           |
+--------------------------+---------------------------+---------------------------+
| Number of runs           | 1 run                     | 2-3 runs                  |
+--------------------------+---------------------------+---------------------------+
| Computational cost       | ~1.1-1.2× base cost       | 2-3× base cost            |
+--------------------------+---------------------------+---------------------------+
| Multiple parameters      | Need derivative per       | Need run per parameter    |
|                          | parameter                 |                           |
+--------------------------+---------------------------+---------------------------+
| Small perturbations      | Exact                     | Can have cancellation     |
|                          |                           | errors                    |
+--------------------------+---------------------------+---------------------------+
| Large perturbations      | Linear approximation      | More accurate             |
|                          | only                      |                           |
+--------------------------+---------------------------+---------------------------+
| Implementation           | Requires code support     | No code changes needed    |
|                          |                           |                           |
+--------------------------+---------------------------+---------------------------+

Practical Applications
======================

1. K-effective Search (Criticality Search)
-------------------------------------------

Derivative tallies enable gradient-based search algorithms that converge faster
than traditional methods:

.. code-block:: python

   # Example: Find critical boron concentration
   model.keff_search(
       func=lambda x: set_boron_concentration(x, model),
       x0=500.0,           # Initial guess (ppm)
       target=1.0,         # Target k-eff
       use_derivative_tallies=True,
       deriv_variable='nuclide_density',
       deriv_material=coolant_id,
       deriv_nuclide='B10'
   )

**Speedup**: Typically 2-3× faster convergence compared to derivative-free methods.

See: ``examples/keff_search_derivatives/`` for complete examples.

2. Depletion Acceleration
--------------------------

Use derivatives to correct reaction rates during depletion, enabling larger
timesteps while maintaining accuracy:

- Predict how flux changes as nuclide densities evolve
- Correct for self-shielding effects (e.g., Xe-135, Sm-149)
- Take 2-5× larger timesteps with <1% error increase

**Implementation Status**: 

- Core algorithm: ✅ Fully implemented in ``openmc.deplete``
- Tested for: Xe-135, Sm-149, U-235, Pu-239
- Production ready: Selective derivative mode for efficiency

See: ``examples/derivative_depletion/`` for complete examples.

3. Sensitivity and Uncertainty Quantification
----------------------------------------------

Derivatives provide exact sensitivities for uncertainty propagation:

.. math::

   \sigma_R^2 = \sum_{i,j} \frac{\partial R}{\partial x_i} 
   \text{Cov}(x_i, x_j) \frac{\partial R}{\partial x_j}

This enables:

- Manufacturing tolerance analysis
- Nuclear data uncertainty quantification
- Design optimization with uncertainty constraints

4. Reactivity Coefficients
---------------------------

Direct computation of reactivity coefficients:

.. math::

   \alpha_x = \frac{1}{k} \frac{\partial k}{\partial x}

Examples:

- Doppler coefficient: :math:`\alpha_T = \frac{1}{k} \frac{\partial k}{\partial T}`
- Void coefficient: :math:`\alpha_\rho = \frac{1}{k} \frac{\partial k}{\partial \rho}`
- Boron worth: :math:`\frac{\partial k}{\partial C_B}`

Best Practices
==============

1. **Choose the Right Derivative Type**

   - Use ``nuclide_density`` for isotope-specific studies (boron, Xe, actinides)
   - Use ``density`` for material-level perturbations (densification, swelling)
   - **Avoid** ``temperature`` derivatives unless you have WMP data and understand limitations

2. **Selective Derivative Computation**

   For large problems, compute derivatives only for important nuclides:
   
   - Strong absorbers: Xe-135, Sm-149, Gd-155/157
   - Actinides: U-235, Pu-239/240/241 (high burnup regions only)
   - Burnable absorbers: B-10, Er-167 (if present)

3. **Verify Linearity Assumptions**

   Derivatives assume small perturbations. Verify by comparing:
   
   - Derivative prediction: :math:`R(x + \Delta x) \approx R(x) + \frac{\partial R}{\partial x} \Delta x`
   - Actual perturbed value: Run with perturbed input
   
   If error >5%, perturbation may be too large for linear approximation.

4. **Unit Conversions**

   Be careful with units, especially for ``nuclide_density``:
   
   - OpenMC computes: :math:`\frac{\partial R}{\partial N}` in [barn·cm / atom]
   - For ppm searches: Convert using material composition
   - Example: B-10 in 1000 ppm B in water requires density-to-ppm conversion

5. **Statistical Considerations**

   - Derivative tallies have uncertainty like regular tallies
   - May need more particles for good derivative statistics
   - Use correlation between base and derivative tallies for efficiency

References
==========

1. Harper, S. M. (2016). "Calculating Reaction Rate Derivatives in Monte Carlo 
   Neutron Transport." Master's Thesis, Massachusetts Institute of Technology.

2. Romano, P. K., et al. (2015). "OpenMC: A state-of-the-art Monte Carlo code 
   for research and development." *Annals of Nuclear Energy*, 82, 90-97.

3. OpenMC Documentation: https://docs.openmc.org

4. OpenMC Examples:
   
   - ``examples/keff_search_derivatives/``
   - ``examples/derivative_depletion/``

See Also
========

- :ref:`io_tallies` - XML specification for derivative tallies
- :class:`openmc.TallyDerivative` - Python API documentation
- :ref:`usersguide_tallies` - General tally usage guide
