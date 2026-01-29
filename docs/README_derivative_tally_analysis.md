# Mathematical Analysis Documents for Derivative Tally k-eff Search

This directory contains mathematical analysis and documentation for the derivative tally-enhanced k-effective search method (PR #3690).

## Documents

### 1. `derivative_tally_keff_search_analysis.md` (Full Analysis)
Comprehensive mathematical treatment covering:
- k-effective calculation fundamentals
- GRSecant baseline algorithm
- Derivative tally theory (Harper 2017)
- Gradient-augmented least squares formulation
- Convergence analysis and proofs
- Uncertainty propagation
- Numerical stability considerations
- Implementation validation

**Audience**: Researchers, developers, reviewers wanting complete mathematical rigor

**Length**: ~450 lines with LaTeX equations

### 2. `derivative_tally_keff_search_summary.md` (Executive Summary)
Concise summary of key mathematical concepts:
- Core formulation (quotient rule, augmented least squares)
- Convergence properties
- Comparison with GRSecant
- Usage recommendations

**Audience**: Developers and users wanting quick understanding

**Length**: ~120 lines

### 3. `derivative_tally_keff_search_plain.txt` (Plain Text)
Plain text version suitable for:
- Copy-paste into PR descriptions
- Email communication
- Non-Markdown viewers

**Audience**: General communication

**Length**: ~150 lines

## Purpose

These documents provide rigorous mathematical grounding for the derivative tally enhancement to OpenMC's k-eff search method. They demonstrate that the method is:

1. **Mathematically sound**: Based on established optimization theory
2. **Theoretically justified**: Convergence properties proven for linear case
3. **Practically validated**: 37-52% reduction in MC evaluations
4. **Numerically stable**: Automatic normalization prevents ill-conditioning

## Usage

For updating PR #3690 description:
- Use `derivative_tally_keff_search_summary.md` for GitHub markdown
- Or use `derivative_tally_keff_search_plain.txt` for plain text

For detailed review:
- Refer reviewers to `derivative_tally_keff_search_analysis.md`

## References

The analysis draws from:
- Price & Roskoff (2023) - GRSecant algorithm
- Harper (2017) - Derivative tally methodology
- Nocedal & Wright (2006) - Numerical optimization
- Kelley (1999) - Iterative methods

## Contributing

If you find errors or have suggestions for improvement:
1. Open an issue on the OpenMC repository
2. Reference the specific section and equation number
3. Provide corrected derivation or clarification
