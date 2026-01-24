# OpenMC DAGMC/libMesh/CGAL Investigation

## Overview

This directory contains a comprehensive investigation into the relationship between DAGMC, libMesh, MOAB, and the potential value of CGAL for the OpenMC Monte Carlo particle transport code.

## Quick Answer

**Critical Finding**: DAGMC relies on **MOAB**, NOT libmesh. They are independent optional features.

- **DAGMC** (with MOAB): CAD-based geometry for particle tracking
- **libMesh**: Unstructured mesh tallies for result collection
- **Neither generates meshes**: Both consume pre-generated meshes from external tools
- **CGAL**: Valuable as a **complement** for mesh generation, not a replacement

## Documents in This Investigation

### 📄 Start Here: [INVESTIGATION_SUMMARY.md](INVESTIGATION_SUMMARY.md)
**Executive summary for decision-makers**

Read this first for:
- Clear answers to original questions
- Key findings and evidence
- Recommendations and next steps
- Implementation roadmap

**Size**: ~11 KB | **Lines**: 337

---

### 📘 Deep Dive: [DAGMC_LIBMESH_CGAL_ANALYSIS.md](DAGMC_LIBMESH_CGAL_ANALYSIS.md)
**Comprehensive technical analysis**

Read this for:
- Detailed explanation of each component
- Code evidence from OpenMC codebase
- CGAL evaluation (4 scenarios)
- Use cases and dependencies
- Prioritized recommendations

**Size**: ~14 KB | **Lines**: 403

---

### 📋 Quick Reference: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
**Visual guide and cheat sheet**

Read this for:
- Architecture diagrams
- Feature comparison tables
- Configuration examples
- Common misconceptions
- Workflow visualizations

**Size**: ~6 KB | **Lines**: 184

---

## Key Findings at a Glance

### Architecture
```
OpenMC Core (CSG)
    ├─── DAGMC (optional) → MOAB (required)
    └─── libMesh (optional) → libMesh library
```

### Feature Comparison

| Feature | DAGMC + MOAB | libMesh |
|---------|--------------|---------|
| Purpose | Geometry definition | Tally collection |
| Stage | Particle tracking | Result scoring |
| Mesh | Surface (triangles) | Volume (tet/hex) |
| Format | .h5m (HDF5) | .e (Exodus), .vtu |
| Independent | Yes | Yes |

### CGAL Assessment

✅ **Recommended**: Add as optional mesh generation tool
- Implement `openmc.mesh_utils` Python module
- Generate meshes for DAGMC and libMesh
- CSG to mesh conversion
- Reduce commercial tool dependence

❌ **Not Recommended**: Replace MOAB or libMesh
- Wrong use case
- DAGMC is external to OpenMC
- libMesh well-suited for current purpose

## Original Questions Answered

### Q1: How does DAGMC rely on libmesh package?
**A**: It doesn't. DAGMC relies on MOAB (Mesh-Oriented datABase), not libmesh.

DAGMC and libMesh are completely independent optional features that can be enabled separately.

### Q2: Is it for mesh generation?
**A**: No. Neither DAGMC nor libMesh generate meshes.

- **DAGMC**: Consumes `.h5m` files created by CAD tools (Cubit, Trelis)
- **libMesh**: Consumes Exodus/VTK files created by mesh generators (Gmsh, etc.)

### Q3: Can CGAL add value as an alternative to libmesh?
**A**: Not as an alternative, but as a **complement** for mesh generation.

CGAL can fill the gap by providing utilities to create meshes that DAGMC and libMesh consume, reducing dependence on external commercial tools.

## Recommendations

### Priority 1: Documentation (1-2 weeks) ⚡
Update OpenMC documentation to clarify:
- DAGMC uses MOAB, not libMesh
- Both are independent optional features
- Mesh generation happens externally

### Priority 2: CGAL Integration (3-6 months) 🚀
Implement optional CGAL support:
```cmake
cmake .. -DOPENMC_USE_CGAL=ON
```

Features:
- `openmc.mesh_utils` Python module
- CSG → DAGMC mesh converter
- Geometry → libMesh mesh converter
- Mesh quality tools

### Priority 3: Advanced Features (Research) 🔬
Evaluate:
- Automatic mesh adaptation
- Geometry analysis utilities
- Enhanced visualization
- Mesh-based variance reduction

## Evidence Sources

- **OpenMC Codebase**: C++ headers, CMake configuration, Python API
- **Documentation**: User's guide, installation instructions
- **Dependencies**: DAGMC, MOAB, libMesh official docs
- **Code Analysis**: 924 lines of analysis across 3 documents

## Implementation Roadmap (CGAL)

**Phase 1** (Month 1-2): Foundation
- Add CMake option
- Basic data structures
- Unit tests

**Phase 2** (Month 2-4): Converters
- CSG → surface mesh
- Surface → .h5m (DAGMC)
- Volume mesh generation
- Volume → Exodus (libMesh)

**Phase 3** (Month 4-5): Python API
- Python bindings
- `openmc.mesh_utils` module
- Examples and tutorials

**Phase 4** (Month 5-6): Advanced
- Mesh quality tools
- Refinement algorithms
- Boolean operations

## Usage Examples (Proposed with CGAL)

### Generate DAGMC Mesh from CSG
```python
import openmc.mesh_utils

# Create mesh from OpenMC cells
converter = openmc.mesh_utils.CSGToDAGMC()
converter.add_cells([cell1, cell2, cell3])
converter.export('geometry.h5m')

# Use in OpenMC
dag_univ = openmc.DAGMCUniverse('geometry.h5m')
```

### Generate Tally Mesh
```python
# From STL file
vol_mesh = openmc.mesh_utils.VolumeMeshFromSTL('part.stl')
vol_mesh.refine(max_size=1.0)
vol_mesh.export_exodus('tally.e')

# Use in OpenMC
mesh = openmc.LibMesh('tally.e')
mesh_filter = openmc.MeshFilter(mesh)
```

## Configuration Examples

### Build with DAGMC (uses MOAB internally)
```bash
cmake .. -DOPENMC_USE_DAGMC=ON \
         -DCMAKE_PREFIX_PATH=/path/to/dagmc
```

### Build with libMesh
```bash
cmake .. -DOPENMC_USE_LIBMESH=ON \
         -DCMAKE_PREFIX_PATH=/path/to/libmesh
```

### Build with Both
```bash
cmake .. -DOPENMC_USE_DAGMC=ON \
         -DOPENMC_USE_LIBMESH=ON \
         -DCMAKE_PREFIX_PATH="/path/to/dagmc;/path/to/libmesh"
```

### Future: Build with CGAL (hypothetical)
```bash
cmake .. -DOPENMC_USE_CGAL=ON  # For mesh generation utilities
```

## Common Misconceptions Corrected

| ❌ Wrong | ✅ Correct |
|---------|----------|
| DAGMC uses libMesh | DAGMC uses MOAB |
| DAGMC generates meshes | DAGMC consumes .h5m files |
| libMesh is for geometry | libMesh is for tallies |
| MOAB and libMesh are related | Independent libraries |
| Must choose DAGMC OR libMesh | Can use both together |

## Related Links

- **DAGMC**: https://svalinn.github.io/DAGMC/
- **MOAB**: https://sigma.mcs.anl.gov/moab-library/
- **libMesh**: https://libmesh.github.io/
- **CGAL**: https://www.cgal.org/
- **OpenMC**: https://docs.openmc.org/

## Investigation Metadata

- **Date**: January 23, 2026
- **Total Lines of Analysis**: 924 lines
- **Documents**: 3 comprehensive guides
- **Code Changes**: None (documentation only)
- **Branch**: `copilot/check-dagmc-libmesh-relationship`

## How to Read This Investigation

1. **For quick overview**: Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
2. **For decision-making**: Read [INVESTIGATION_SUMMARY.md](INVESTIGATION_SUMMARY.md)
3. **For implementation**: Read [DAGMC_LIBMESH_CGAL_ANALYSIS.md](DAGMC_LIBMESH_CGAL_ANALYSIS.md)
4. **For ongoing reference**: Bookmark [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---

**Status**: ✅ Investigation Complete  
**Next Steps**: Review recommendations and decide on CGAL integration
