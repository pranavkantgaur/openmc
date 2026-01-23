# Investigation Summary: DAGMC, libMesh, MOAB, and CGAL

## Problem Statement
Investigate:
1. How DAGMC (an OpenMC dependency) relies on libmesh package
2. Whether libmesh is used for mesh generation
3. Whether CGAL can add value as an alternative to libmesh for OpenMC

## Executive Summary

### 🔍 Critical Finding
**The premise of the investigation was incorrect:**

> **DAGMC does NOT rely on libmesh. DAGMC relies on MOAB.**

DAGMC and libMesh are **completely independent, optional features** in OpenMC that serve different purposes at different stages of the simulation.

### Key Conclusions

1. **DAGMC Dependencies**:
   - DAGMC → **MOAB** (Mesh-Oriented datABase)
   - Used for CAD-based geometry representation
   - Particle tracking through surface meshes
   - Files: `.h5m` (HDF5 mesh format)

2. **libMesh Purpose**:
   - Completely independent from DAGMC
   - Used for unstructured mesh **tallies** (result collection)
   - Element-by-element scoring
   - Files: `.e` (Exodus), `.vtu` (VTK), etc.

3. **Mesh Generation**:
   - **Neither DAGMC nor libMesh generate meshes**
   - Both **consume** pre-generated meshes from external tools:
     - DAGMC: CAD tools (Cubit, Trelis) → `.h5m`
     - libMesh: Mesh generators (Gmsh, etc.) → Exodus/VTK

4. **CGAL Assessment**:
   - ❌ Not suitable as replacement for MOAB (DAGMC is external)
   - ❌ Not suitable as replacement for libMesh (different purpose)
   - ✅ **Highly valuable as complement** for mesh generation utilities

## Detailed Analysis

### Architecture Overview

```
OpenMC Core (CSG Geometry)
    │
    ├─── Optional: DAGMC
    │         │
    │         └─── Requires: MOAB
    │                  │
    │                  └─── Surface mesh database
    │                       CAD geometry tracking
    │
    └─── Optional: libMesh
              │
              └─── Unstructured mesh tallies
                   Result collection
```

### Feature Comparison

| Aspect | DAGMC (with MOAB) | libMesh |
|--------|-------------------|---------|
| **Purpose** | Geometry definition | Tally accumulation |
| **Stage** | Particle tracking | Result collection |
| **Mesh Type** | Surface (triangulated) | Volume (tet/hex) |
| **Dependency** | MOAB | libMesh library |
| **CMake Flag** | `OPENMC_USE_DAGMC` | `OPENMC_USE_LIBMESH` |
| **Independent?** | Yes | Yes |
| **Work together?** | Yes | Yes |
| **Generate mesh?** | No | No |

### What is MOAB?

**MOAB** (Mesh-Oriented datABase) is the actual dependency of DAGMC:
- Hierarchical mesh data structure
- Entity handles (vertices, edges, surfaces, volumes)
- Efficient spatial queries for ray-tracing
- Metadata and tagging system
- Developed at Argonne National Laboratory

From OpenMC's `include/openmc/dagmc.h`:
```cpp
class DAGSurface : public Surface {
  std::shared_ptr<moab::DagMC> dagmc_ptr_;  // Uses MOAB
  moab::EntityHandle mesh_handle() const;
};
```

### CGAL Evaluation Results

Evaluated 4 scenarios:

#### ❌ Scenario 1: Replace MOAB in DAGMC
- **Feasibility**: Low
- **Why not**: DAGMC is external to OpenMC, MOAB deeply integrated
- **Conclusion**: Not practical for OpenMC project

#### ❌ Scenario 2: Replace libMesh
- **Feasibility**: Medium
- **Why not**: Wrong tool; libMesh designed for FEM, CGAL for geometry
- **Conclusion**: Not recommended

#### ✅ Scenario 3: Complement for Mesh Generation (RECOMMENDED)
- **Feasibility**: High
- **Value**: Medium to High
- **Benefits**:
  - Open-source mesh generation
  - Python API enhancement
  - Reduce commercial CAD dependence
  - Pre-processing utilities
  - CSG to mesh conversion

**Potential Implementation**:
```python
import openmc.mesh_utils  # New module with CGAL

# Generate DAGMC mesh from CSG
converter = openmc.mesh_utils.CSGToDAGMC()
converter.from_cells([cell1, cell2])
converter.export('geometry.h5m')

# Generate volume mesh for tallies
vol_mesh = openmc.mesh_utils.VolumeMeshGenerator()
vol_mesh.from_stl('part.stl', max_size=1.0)
vol_mesh.export_exodus('tally.e')
```

#### ✅ Scenario 4: New Advanced Features
- **Feasibility**: High
- **Value**: Medium
- **Potential features**:
  - Automatic CSG to mesh conversion
  - Geometry analysis utilities
  - Mesh-based variance reduction
  - Enhanced visualization

## Recommendations

### 🎯 Priority 1: Documentation (Immediate - 1-2 weeks)
**Update OpenMC documentation to clarify:**
- DAGMC uses MOAB, not libMesh
- DAGMC and libMesh are independent
- Mesh generation happens externally
- Architecture diagrams

**Impact**: Reduces confusion, improves understanding

### 🎯 Priority 2: CGAL as Mesh Generation Tool (Medium-term - 3-6 months)
**Add optional CGAL integration:**
```cmake
-DOPENMC_USE_CGAL=ON  # Optional mesh utilities
```

**Deliverables**:
- `openmc.mesh_utils` Python module
- CSG → DAGMC mesh converter
- Geometry → libMesh mesh converter
- Documentation and examples

**Impact**: Enhanced capabilities, reduced commercial tool dependence

### 🎯 Priority 3: Advanced Features (Long-term - Research)
**Evaluate**:
- Automatic mesh adaptation
- Geometry analysis tools
- Advanced visualization
- Mesh quality metrics

**Impact**: Cutting-edge capabilities

## Evidence from Codebase

### CMake Configuration
```cmake
# From CMakeLists.txt

option(OPENMC_USE_DAGMC "Enable support for DAGMC (CAD) geometry" OFF)
option(OPENMC_USE_LIBMESH "Enable support for libMesh unstructured mesh tallies" OFF)

if(OPENMC_USE_DAGMC)
  find_package(DAGMC REQUIRED)  # DAGMC brings MOAB
endif()

if(OPENMC_USE_LIBMESH)
  find_package(LIBMESH REQUIRED)  # Independent
endif()
```

### Installation Documentation
From `docs/source/usersguide/install.rst`:

> "OpenMC supports particle tracking in CAD-based geometries via the Direct Accelerated Geometry Monte Carlo (DAGMC) toolkit. For use in OpenMC, only the **MOAB_DIR** and BUILD_TALLY variables need to be specified in the CMake configuration step when building DAGMC."

> "This optional dependency enables support for unstructured mesh tally filters using **libMesh** meshes."

### Code Headers
- `include/openmc/dagmc.h`: References `moab::DagMC`, `moab::EntityHandle`
- `include/openmc/mesh.h`: Separate `#ifdef OPENMC_LIBMESH_ENABLED` section

## Common Misconceptions Corrected

| ❌ Misconception | ✅ Reality |
|------------------|-----------|
| DAGMC relies on libMesh | DAGMC relies on **MOAB** |
| DAGMC generates meshes | DAGMC **consumes** pre-made .h5m files |
| libMesh is for geometry | libMesh is for **tallies** only |
| MOAB and libMesh are related | Completely different libraries |
| Must choose DAGMC or libMesh | Can use **both simultaneously** |
| Mesh generation is built-in | Mesh generation is **external** |

## Documents Delivered

### 1. DAGMC_LIBMESH_CGAL_ANALYSIS.md (14 KB)
Comprehensive technical analysis containing:
- Detailed DAGMC/MOAB relationship explanation
- libMesh independent role clarification
- Code evidence from OpenMC
- 4 CGAL scenarios evaluated
- Prioritized recommendations
- Implementation pathways

### 2. QUICK_REFERENCE.md (6 KB)
Quick reference guide with:
- Architecture diagrams
- Feature comparison tables
- Workflow visualizations
- Configuration examples
- Common misconceptions debunked
- Next steps

## Workflow Examples

### Current Workflow: DAGMC
```
1. Create CAD model in Cubit/Trelis
2. Imprint and merge surfaces
3. Export to .h5m file (MOAB format)
4. Configure OpenMC with DAGMC enabled
5. OpenMC reads .h5m via MOAB
6. DAGMC provides geometry queries
7. Particles tracked through CAD geometry
```

### Current Workflow: libMesh
```
1. Generate mesh with Gmsh or similar
2. Export to Exodus (.e) or VTK format
3. Configure OpenMC with libMesh enabled
4. OpenMC reads mesh via libMesh
5. Define mesh tally filter
6. Run simulation
7. Tallies accumulated per element
```

### Proposed Workflow with CGAL
```
1. Define geometry in OpenMC (CSG or simple CAD)
2. Use openmc.mesh_utils (with CGAL) to generate mesh
3. Export to .h5m (DAGMC) or Exodus (libMesh)
4. Continue with standard workflows
5. No external mesh tools needed for simple cases
```

## Technical Details

### MOAB in DAGMC
- **Entity handles**: Unique identifiers for mesh entities
- **Mesh sets**: Hierarchical organization (volumes, surfaces, etc.)
- **Ray-fire queries**: Efficient particle tracking
- **Metadata**: Material assignments, boundary conditions
- **File format**: HDF5-based .h5m files

### libMesh in OpenMC
- **Equation systems**: Store tally data per element
- **Element types**: TET4, TET10, HEX8, HEX20, etc.
- **Parallel**: MPI-based mesh partitioning
- **I/O**: Exodus, VTK, Gmsh formats
- **DOF mapping**: Degrees of freedom per element

## Implementation Roadmap for CGAL Integration

### Phase 1: Foundation (Month 1-2)
- Add CMake option `OPENMC_USE_CGAL`
- Create `openmc/mesh_utils/` directory structure
- Implement basic CGAL mesh data structures
- Add unit tests

### Phase 2: Converters (Month 2-4)
- CSG → surface mesh converter
- Surface mesh → .h5m writer (DAGMC format)
- Surface mesh → volume mesh converter
- Volume mesh → Exodus writer (libMesh format)

### Phase 3: Python API (Month 4-5)
- Python bindings via pybind11
- `openmc.mesh_utils` module
- Examples and tutorials
- Documentation

### Phase 4: Advanced Features (Month 5-6)
- Mesh quality improvement
- Automatic refinement
- Boolean operations
- Geometry analysis tools

## Conclusion

The investigation revealed that:

1. **DAGMC relies on MOAB, not libMesh** - This is the critical clarification
2. **Both are for consuming meshes, not generating them** - External tools required
3. **CGAL is not a replacement** - Different purposes
4. **CGAL as a complement has high value** - Fills mesh generation gap

### Answer to Original Questions:

**Q1: How does DAGMC rely on libmesh?**
- **A**: It doesn't. DAGMC relies on **MOAB**.

**Q2: Is it for mesh generation?**
- **A**: No. Neither DAGMC nor libMesh generate meshes. Both consume pre-generated meshes.

**Q3: Can CGAL add value as an alternative?**
- **A**: Not as an alternative, but as a **complement**. CGAL can fill the mesh generation gap by providing utilities to create meshes that DAGMC and libMesh consume.

### Recommended Action
Implement CGAL as an optional mesh generation toolkit in OpenMC's Python API, complementing (not replacing) existing DAGMC/MOAB and libMesh capabilities.

---
**Investigation completed**: January 23, 2026  
**Documents**: 2 comprehensive guides created  
**Code changes**: None (documentation only)  
**Next step**: Review recommendations and decide on CGAL integration
