# How to Use the Mathematical Analysis Documents

## Quick Start

This repository contains comprehensive mathematical analysis for the derivative tally-enhanced k-eff search method (PR #3690). Here's how to use these documents:

## For Updating PR #3690

### Option 1: Markdown Summary (Recommended)
Copy the executive summary to the PR description:

```bash
cat docs/derivative_tally_keff_search_summary.md
```

This provides:
- Core mathematical formulation
- Key equations in LaTeX
- Performance comparison table
- Usage recommendations
- References

### Option 2: Plain Text
For plain text comments or emails:

```bash
cat docs/derivative_tally_keff_search_plain.txt
```

Same content as summary, but ASCII-formatted.

## For Code Reviewers

Direct reviewers to the full analysis for detailed mathematics:

> For complete mathematical derivations and proofs, see:  
> `docs/derivative_tally_keff_search_analysis.md`

This includes:
- 11 sections covering all aspects
- Rigorous proofs (Propositions 6.1, 6.2)
- Convergence analysis
- 446 lines of detailed mathematics

## For Developers

### During Implementation
Use the quick reference:

```bash
cat docs/derivative_tally_keff_search_equations.md
```

Contains all key equations in one place.

### For Understanding Context
Read the top-level summary:

```bash
cat MATHEMATICAL_ANALYSIS_SUMMARY.md
```

Provides overview and usage guidance.

## Document Structure

```
Repository Root
├── MATHEMATICAL_ANALYSIS_SUMMARY.md  ← Start here
├── HOW_TO_USE_ANALYSIS.md           ← This file
├── VERIFICATION.md                   ← Quality checklist
│
└── docs/
    ├── README_derivative_tally_analysis.md        ← Document guide
    ├── derivative_tally_keff_search_analysis.md   ← Full analysis (20KB)
    ├── derivative_tally_keff_search_summary.md    ← Executive summary (5KB)
    ├── derivative_tally_keff_search_plain.txt     ← Plain text (5KB)
    └── derivative_tally_keff_search_equations.md  ← Quick reference (4KB)
```

## Common Use Cases

### 1. "I need to update the PR description"
→ Use `docs/derivative_tally_keff_search_summary.md`

### 2. "I need to explain this to reviewers"
→ Reference `docs/derivative_tally_keff_search_analysis.md`

### 3. "I need the key equations quickly"
→ Use `docs/derivative_tally_keff_search_equations.md`

### 4. "I need plain text for an email"
→ Use `docs/derivative_tally_keff_search_plain.txt`

### 5. "I want to understand what was done"
→ Read `MATHEMATICAL_ANALYSIS_SUMMARY.md`

### 6. "I need to verify completeness"
→ Check `VERIFICATION.md`

## Key Sections by Audience

### For Managers/Decision Makers
Read:
1. MATHEMATICAL_ANALYSIS_SUMMARY.md (overview)
2. Section "Performance Gains" in summary.md

### For Researchers
Read:
1. Full analysis (analysis.md) - all sections
2. References at end

### For Developers
Read:
1. Quick reference (equations.md)
2. Section "Implementation Details" in analysis.md
3. Section "Numerical Stability" in analysis.md

### For Users
Read:
1. Section "When to Use" in summary.md
2. Examples in equations.md

## Suggested PR Description Template

```markdown
## Mathematical Foundation

This PR extends the GRSecant algorithm with derivative tallies, achieving 
37-52% reduction in Monte Carlo evaluations. The method is mathematically 
rigorous and theoretically sound.

### Core Innovation: Gradient-Augmented Least Squares

[Copy from summary.md, Section 2]

### Performance Gains

[Copy table from summary.md]

### Theoretical Grounding

[Copy from summary.md, Section "Rigorous Foundation"]

### Full Mathematical Analysis

For complete derivations, proofs, and convergence analysis, see:
`docs/derivative_tally_keff_search_analysis.md`

### References

[Copy from summary.md]
```

## Tips

1. **For GitHub**: Use .md files (LaTeX renders)
2. **For emails**: Use .txt file (no formatting needed)
3. **For presentations**: Extract equations from equations.md
4. **For papers**: Cite analysis.md and original papers

## Questions?

If you need:
- Different format → Refer to README_derivative_tally_analysis.md
- More detail → Read full analysis.md
- Less detail → Use summary.md
- Just equations → Use equations.md

## Verification

To verify all documents are present and correct:

```bash
cat VERIFICATION.md
```

---

**Last Updated**: January 2026  
**Related PR**: https://github.com/openmc-dev/openmc/pull/3690
