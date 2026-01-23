# Quick Reference: DAGMC, libMesh, and CGAL in OpenMC

## ❗ Critical Clarification

**DAGMC RELIES ON MOAB, NOT LIBMESH**

libMesh and DAGMC are **completely independent** optional features.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      OpenMC Core                            │
│                   (CSG Geometry Base)                       │
└────────────┬────────────────────────────┬───────────────────┘
             │                            │
             │                            │
    ┌────────▼──────────┐        ┌───────▼────────────┐
    │     DAGMC         │        │     libMesh        │
    │   (Optional)      │        │    (Optional)      │
    │                   │        │                    │
    │ Purpose:          │        │ Purpose:           │
    │ - CAD geometry    │        │ - Mesh tallies     │
    │ - Particle track  │        │ - Result collect   │
    └────────┬──────────┘        └────────────────────┘
             │
             │ depends on
             │
    ┌────────▼──────────┐
    │      MOAB         │
    │  (Required for    │
    │     DAGMC)        │
    │                   │
    │ Provides:         │
    │ - Mesh database   │
    │ - Surface queries │
    │ - Entity handles  │
    └───────────────────┘
```

## Feature Comparison

| Aspect              | DAGMC + MOAB                    | libMesh                        |
|---------------------|--------------------------------|--------------------------------|
| **Purpose**         | Geometry definition            | Tally accumulation            |
| **When Used**       | During particle tracking       | During scoring                |
| **Mesh Type**       | Surface mesh (triangles)       | Volume mesh (tet/hex)         |
| **File Format**     | .h5m (HDF5)                    | .e (Exodus), .vtu, etc.       |
| **Dependencies**    | MOAB (required)                | libMesh library               |
| **CMake Flag**      | `OPENMC_USE_DAGMC=ON`          | `OPENMC_USE_LIBMESH=ON`       |
| **Can Use Alone**   | ✅ Yes                         | ✅ Yes                        |
| **Can Use Together**| ✅ Yes                         | ✅ Yes                        |
| **Generates Mesh**  | ❌ No (consumes .h5m)          | ❌ No (consumes Exodus/VTK)   |

## Mesh Generation Workflow

### For DAGMC:
```
CAD Model (Cubit/Trelis)
    ↓
Imprint & Merge surfaces
    ↓
Export to .h5m file
    ↓
MOAB reads .h5m
    ↓
DAGMC uses for geometry
    ↓
OpenMC tracks particles
```

### For libMesh:
```
Mesh Generator (Gmsh, etc.)
    ↓
Create volume mesh
    ↓
Export to Exodus/VTK
    ↓
libMesh reads mesh
    ↓
OpenMC uses for tallies
    ↓
Results per element
```

## CGAL Evaluation Summary

### ❌ Not Recommended:
1. **Replace MOAB in DAGMC**: Impractical (DAGMC is external)
2. **Replace libMesh**: Wrong tool for the job

### ✅ Recommended:
**Add CGAL as mesh generation complement**

```python
# Potential future API with CGAL integration
import openmc.mesh_utils  # New module

# Generate DAGMC mesh from CSG
converter = openmc.mesh_utils.CSGToDAGMC()
converter.add_cells([cell1, cell2, cell3])
converter.export('geometry.h5m')

# Generate tally mesh
mesh_gen = openmc.mesh_utils.VolumeM eshFromSTL('part.stl')
mesh_gen.refine(max_size=1.0)
mesh_gen.export_exodus('tally.e')
```

### Benefits:
- ✅ Open-source mesh generation
- ✅ Reduces dependence on commercial CAD
- ✅ Python API enhancement
- ✅ Maintains existing workflows
- ✅ Optional (doesn't break anything)

## Configuration Examples

### Pure CSG (no optional features):
```bash
cmake .. -DOPENMC_USE_DAGMC=OFF -DOPENMC_USE_LIBMESH=OFF
```

### With DAGMC (CAD geometry):
```bash
cmake .. -DOPENMC_USE_DAGMC=ON \
         -DCMAKE_PREFIX_PATH=/path/to/dagmc
# MOAB is automatically found through DAGMC
```

### With libMesh (unstructured tallies):
```bash
cmake .. -DOPENMC_USE_LIBMESH=ON \
         -DCMAKE_PREFIX_PATH=/path/to/libmesh
```

### With Both:
```bash
cmake .. -DOPENMC_USE_DAGMC=ON \
         -DOPENMC_USE_LIBMESH=ON \
         -DCMAKE_PREFIX_PATH="/path/to/dagmc;/path/to/libmesh"
```

### Future with CGAL (hypothetical):
```bash
cmake .. -DOPENMC_USE_CGAL=ON  # For mesh generation utilities
```

## Common Misconceptions

| Misconception | Reality |
|--------------|---------|
| "DAGMC uses libMesh" | ❌ DAGMC uses **MOAB**, not libMesh |
| "DAGMC generates meshes" | ❌ DAGMC **consumes** pre-made .h5m files |
| "libMesh is for geometry" | ❌ libMesh is for **tallies**, not geometry |
| "MOAB and libMesh are related" | ❌ Completely different libraries, different purposes |
| "CGAL should replace MOAB" | ❌ CGAL should **complement** for mesh generation |

## Recommended Next Steps

1. **Document** (Priority 1 - Quick):
   - Update OpenMC docs to clarify DAGMC/MOAB relationship
   - Add architecture diagram
   - Explain workflows clearly

2. **Prototype CGAL Integration** (Priority 2 - Medium-term):
   - Add `OPENMC_USE_CGAL` option
   - Create `openmc.mesh_utils` module
   - Implement basic converters
   - Test with simple geometries

3. **Gather User Feedback** (Priority 3 - Ongoing):
   - Identify mesh generation pain points
   - Understand user workflows
   - Prioritize CGAL features

## References

- **Full Analysis**: See `DAGMC_LIBMESH_CGAL_ANALYSIS.md`
- **DAGMC**: https://svalinn.github.io/DAGMC/
- **MOAB**: https://sigma.mcs.anl.gov/moab-library/
- **libMesh**: https://libmesh.github.io/
- **CGAL**: https://www.cgal.org/
