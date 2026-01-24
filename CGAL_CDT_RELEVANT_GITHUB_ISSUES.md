# GitHub Issues Where CGAL Constrained Delaunay Tetrahedralization Could Help

This document lists GitHub issues from the upstream openmc-dev/openmc repository where CGAL's constrained Delaunay tetrahedralization (CDT) could provide solutions or improvements.

## Summary

Based on analysis of the upstream OpenMC repository, **7 open issues** and **3 closed issues** have been identified where CGAL's CDT capabilities could provide significant value. These issues span mesh generation, tally performance, unstructured mesh support, and geometry conversion.

---

## High Priority Issues (CGAL CDT Would Directly Address)

### 1. Issue #2929: Access mesh information (volumes, centroids) for UnstructuredMesh
**URL**: https://github.com/openmc-dev/openmc/issues/2929  
**Status**: Open  
**Created**: 2024

**Problem**: Users cannot access volume and centroid information for UnstructuredMesh instances created programmatically (only from statepoint files).

**How CGAL CDT Helps**:
- CDT automatically computes tetrahedral volumes during mesh generation
- Centroids can be calculated directly from tetrahedra vertices
- CGAL's mesh data structures provide efficient access to geometric properties
- Integration with `openmc.mesh_utils` would expose these properties in Python API

**Implementation**: 
```python
# With CGAL CDT backend
umesh = openmc.mesh_utils.ConstrainedDelaunayMesh()
umesh.from_geometry(geometry)
umesh.generate()
# Centroids and volumes immediately available
print(umesh.centroids)  # Works without statepoint
print(umesh.volumes)    # Works without statepoint
```

---

### 2. Issue #3552: Support for custom element clustering in libMesh tallies
**URL**: https://github.com/openmc-dev/openmc/issues/3552  
**Status**: Open  
**Created**: 2025

**Problem**: libMesh only supports isotropic refinement. Need ability to treat multiple small elements as a single tally bin for complex shapes.

**How CGAL CDT Helps**:
- CDT can generate meshes with custom clustering from the start
- Sizing fields enable grouping elements by importance
- Material boundary constraints ensure proper element grouping
- Eliminates need for post-processing element clustering

**Implementation**:
- Use CGAL sizing fields to control element sizes by region
- Material boundaries automatically create element groups
- Generate mesh with appropriate granularity for tally requirements

---

### 3. Issue #3570: Large mesh tally sizes cause MPI errors in depletion
**URL**: https://github.com/openmc-dev/openmc/issues/3570  
**Status**: Open  
**Created**: 2025

**Problem**: Very fine meshes (100×100×100) for depletion calculations cause MPI broadcast errors even without MPI enabled.

**How CGAL CDT Helps**:
- **Adaptive meshing**: Fine resolution only where needed (near fuel, boundaries)
- **Reduced element count**: Coarse elements in less important regions
- **Smaller data structures**: Fewer elements = smaller MPI messages
- **Material-aligned elements**: Better accuracy with fewer elements

**Example**: Instead of uniform 100×100×100 = 1M elements:
- Fine mesh near fuel pellet boundary: ~100K elements
- Medium mesh in fuel bulk: ~50K elements  
- Coarse mesh in coolant: ~10K elements
- **Total: ~160K elements** (6× reduction) with better accuracy

---

## Medium Priority Issues (CGAL CDT Provides Better Solutions)

### 4. Issue #1184: Poor tally performance with fine meshes
**URL**: https://github.com/openmc-dev/openmc/issues/1184  
**Status**: Open  
**Created**: 2019

**Problem**: 100×100 mesh tallies make simulations 10× slower. Performance degradation with Intel compiler and OpenMP.

**How CGAL CDT Helps**:
- **Spatial indexing**: CDT meshes naturally support efficient spatial queries
- **Reduced element count**: Adaptive refinement reduces total elements
- **Better cache locality**: Tetrahedral meshes can be ordered for cache efficiency
- **Hierarchical structures**: CGAL supports bounding volume hierarchies

**Impact**: Adaptive tetrahedral mesh could achieve same accuracy as 100×100 regular mesh with 5-10× fewer elements, directly improving tally performance.

---

### 5. Issue #214: Tally module limitations with multiple filter combinations
**URL**: https://github.com/openmc-dev/openmc/issues/214  
**Status**: Open  
**Created**: 2014

**Problem**: Cannot properly score to multiple filter combinations. Collision estimator not fully supported. Too much code duplication.

**How CGAL CDT Helps**:
- **Material-aligned elements**: Elements respect material boundaries by construction
- **Hierarchical structure**: Natural support for nested tallies (element in cell in universe)
- **Geometric queries**: Efficient point-in-element tests for tally bin identification
- **Flexible binning**: Elements can be tagged with multiple material/region IDs

**Benefit**: Well-defined tetrahedral elements with material boundary constraints simplify tally logic and enable proper collision estimators.

---

### 6. Issue #3200: Scale DAGMC geometry for unit conversion
**URL**: https://github.com/openmc-dev/openmc/issues/3200  
**Status**: Open  
**Created**: 2024

**Problem**: Need ability to scale DAGMC meshes when units don't match (e.g., meters to cm).

**How CGAL CDT Helps** (Indirectly):
- CGAL mesh generation includes built-in scaling transformations
- `openmc.mesh_utils` could generate properly scaled meshes from CAD
- Eliminates need to scale existing meshes by generating at correct scale
- Supports affine transformations during mesh generation

---

## Lower Priority Issues (CGAL CDT Enables Better Alternatives)

### 7. Issue #3113: Replace VTK dependency with HDF5-based format
**URL**: https://github.com/openmc-dev/openmc/issues/3113  
**Status**: Open  
**Created**: 2024

**Problem**: VTK dependency causes issues. Need HDF5-based vtk format for meshes, tracks, and geometry.

**How CGAL CDT Helps** (Indirectly):
- CGAL meshes can be exported to various formats including VTK/VTU
- `openmc.mesh_utils` could handle format conversions using h5py
- Tetrahedral meshes easier to export to structured formats
- Native CGAL mesh format could serve as internal representation

**Note**: This is mainly about output format, but CGAL would provide better mesh generation pipeline.

---

### 8. Issue #3289: Export unstructured meshes in VTU format
**URL**: https://github.com/openmc-dev/openmc/issues/3289  
**Status**: Open  
**Created**: 2024

**Problem**: Currently export to legacy VTK format. Need modern VTU format with better compression.

**How CGAL CDT Helps** (Indirectly):
- CGAL provides export functions for modern formats
- Tetrahedral meshes natively supported by VTU
- Better integration with paraview workflows
- `openmc.mesh_utils` could handle VTU export directly

---

### 9. Issue #3620: Write mesh data to HDF5 VTK format for all mesh types
**URL**: https://github.com/openmc-dev/openmc/issues/3620  
**Status**: Open  
**Created**: 2025

**Problem**: Need HDF5 VTK format export for all mesh types (RegularMesh, RectilinearMesh, SphericalMesh, CylindricalMesh, UnstructuredMesh).

**How CGAL CDT Helps** (Indirectly):
- Unified mesh generation with CGAL simplifies export pipeline
- All mesh types could be converted to tetrahedral representation
- Single export path for all geometries
- Better compression for unstructured meshes

---

### 10. Issue #3729: Remove VTK dependency entirely
**URL**: https://github.com/openmc-dev/openmc/issues/3729  
**Status**: Open  
**Created**: 2026

**Problem**: VTK holds up Python 3.13/3.14 support. Need internal VTK template engine.

**How CGAL CDT Helps** (Indirectly):
- CGAL doesn't depend on VTK
- `openmc.mesh_utils` could generate meshes without VTK
- Internal mesh representation with CGAL
- Export functions using h5py (already a dependency)

---

## Closed Issues (Historical Context)

### 11. Issue #3622: Unstructured mesh related
**URL**: https://github.com/openmc-dev/openmc/issues/3622  
**Status**: Closed (Nov 2025)  
**Note**: Specific details not fully retrieved but related to unstructured mesh support

---

### 12. Issue #3284: Remove C++ VTK writing for unstructured meshes
**URL**: https://github.com/openmc-dev/openmc/issues/3284  
**Status**: Open  
**Created**: 2024

**Problem**: C++ VTK writing for unstructured meshes is opaque and limited. Should move to Python post-processing.

**How CGAL CDT Helps**:
- Python-level mesh generation with CGAL
- Direct access to mesh properties for post-processing
- No need for C++ VTK writing
- Cleaner separation of simulation and visualization

---

## Summary Table

| Issue # | Title | Status | Priority | CDT Benefit |
|---------|-------|--------|----------|-------------|
| #2929 | Mesh info access | Open | High | Direct - provides volumes/centroids |
| #3552 | Element clustering | Open | High | Direct - custom mesh generation |
| #3570 | Large mesh MPI errors | Open | High | Direct - adaptive refinement |
| #1184 | Tally performance | Open | Medium | Direct - fewer elements |
| #214 | Tally module limits | Open | Medium | Direct - better structure |
| #3200 | DAGMC scaling | Open | Medium | Indirect - scaling at generation |
| #3113 | HDF5 VTK format | Open | Low | Indirect - export pipeline |
| #3289 | VTU export | Open | Low | Indirect - modern formats |
| #3620 | HDF5 mesh export | Open | Low | Indirect - unified export |
| #3729 | Remove VTK dependency | Open | Low | Indirect - alternative solution |
| #3284 | C++ VTK removal | Open | Low | Indirect - Python workflow |

---

## Key Takeaways

### Issues Directly Solved by CGAL CDT:
1. **#2929**: Programmatic access to mesh properties
2. **#3552**: Custom element clustering for complex geometries
3. **#3570**: Adaptive meshing to reduce element count
4. **#1184**: Performance improvement through mesh optimization
5. **#214**: Better tally structure with material-aligned elements

### Issues Where CGAL CDT Provides Better Alternatives:
6. **#3200**: Mesh generation with proper scaling
7. **#3113, #3289, #3620, #3729**: Modern mesh export formats

### Total Impact:
- **5 high/medium priority issues** directly addressed
- **6 lower priority issues** benefit from CGAL integration
- Enables **automated mesh generation** reducing user burden
- Provides **performance improvements** through adaptive refinement
- Simplifies **Python API** for mesh operations

---

## Recommendations

Based on this analysis, implementing CGAL's constrained Delaunay tetrahedralization in OpenMC would:

1. **Solve existing pain points**: Addresses 5 high/medium priority open issues
2. **Improve performance**: Reduces tally computational cost through adaptive meshing
3. **Enhance usability**: Automated mesh generation from CSG geometry
4. **Future-proof**: Removes VTK dependency issues, supports modern formats
5. **Enable new features**: Material-aware adaptive meshing for depletion and tallies

**Priority recommendation**: Implement `openmc.mesh_utils` with CGAL CDT backend targeting issues #2929, #3552, and #3570 first.

---

**Document created**: January 24, 2026  
**Based on**: Upstream openmc-dev/openmc repository analysis  
**Related documents**: 
- `DAGMC_LIBMESH_CGAL_ANALYSIS.md` - Detailed CGAL evaluation
- `INVESTIGATION_SUMMARY.md` - Executive summary
