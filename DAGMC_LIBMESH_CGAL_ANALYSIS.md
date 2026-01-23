# Analysis: DAGMC, libMesh, MOAB, and CGAL in OpenMC

## Executive Summary

This document analyzes the relationship between DAGMC, libMesh, MOAB, and the potential value of CGAL as an alternative for OpenMC. The key finding is:

**DAGMC does NOT rely on libMesh. DAGMC relies on MOAB.**

DAGMC and libMesh are **independent, optional features** in OpenMC that serve completely different purposes:
- **DAGMC** (with MOAB): CAD-based geometry representation for particle tracking
- **libMesh**: Unstructured mesh tallies for result collection

## Detailed Analysis

### 1. DAGMC (Direct Accelerated Geometry Monte Carlo)

#### Purpose
DAGMC enables OpenMC to use **CAD-based geometries** instead of or alongside Constructive Solid Geometry (CSG). It allows particle tracking through complex geometries defined by CAD models.

#### How it Works
- Converts CAD models to **surface mesh format** (HDF5 files with `.h5m` extension)
- Represents geometry as collections of triangular surface meshes
- Uses **MOAB** (Mesh-Oriented datABase) as its underlying mesh database library
- Provides acceleration structures for efficient ray-tracing through the mesh

#### Dependencies
```
DAGMC --> MOAB (required)
       └> UWUW (optional, for material assignments)
```

**MOAB** is the critical dependency for DAGMC. From the OpenMC documentation:
> "OpenMC supports particle tracking in CAD-based geometries via the Direct Accelerated Geometry Monte Carlo (DAGMC) toolkit. For use in OpenMC, only the `MOAB_DIR` and `BUILD_TALLY` variables need to be specified in the CMake configuration step when building DAGMC."

#### What MOAB Provides
MOAB (Mesh-Oriented datABase) is a library for:
- Storing and querying mesh data structures
- Representing geometric entities (vertices, edges, surfaces, volumes)
- Providing efficient spatial queries for particle tracking
- Supporting both structured and unstructured meshes
- Managing metadata and tags associated with mesh entities

#### Code Evidence
From `include/openmc/dagmc.h`:
```cpp
#include "DagMC.hpp"  // DAGMC header
#include "dagmcmetadata.hpp"

class DAGSurface : public Surface {
  std::shared_ptr<moab::DagMC> dagmc_ptr_;  // Uses MOAB's DagMC
  moab::EntityHandle mesh_handle() const;   // MOAB entity handle
};

class DAGCell : public Cell {
  std::shared_ptr<moab::DagMC> dagmc_ptr_;  // Uses MOAB's DagMC
};
```

#### CMake Configuration
```cmake
option(OPENMC_USE_DAGMC "Enable support for DAGMC (CAD) geometry" OFF)

if(OPENMC_USE_DAGMC)
  find_package(DAGMC REQUIRED PATH_SUFFIXES lib/cmake)
  # DAGMC internally depends on MOAB
endif()
```

#### Use Cases in OpenMC
1. **Full DAGMC geometries**: Entire model defined by CAD
2. **Hybrid geometries**: DAGMC universes embedded in CSG geometry
3. **Depletion calculations**: Material differentiation in CAD cells
4. **Complex reactor components**: Fuel assemblies, coolant systems, shielding

### 2. libMesh

#### Purpose
libMesh is a **separate, optional feature** for **unstructured mesh tallies**. It enables element-by-element tally scoring on unstructured meshes during particle transport simulation.

#### How it Works
- Provides unstructured mesh data structures (tetrahedral, hexahedral elements)
- Allows tallying results on arbitrary mesh geometries
- Uses libMesh's equation systems for storing tally data
- Supports various element types and mesh formats

#### Dependencies
```
OpenMC --> libMesh (optional, independent of DAGMC)
        └> MPI (commonly required if libMesh is built with MPI)
```

#### What libMesh Provides
libMesh is a C++ library for:
- Finite element method (FEM) applications
- Unstructured mesh management
- Equation systems for solving PDEs
- Parallel mesh partitioning and distribution
- Mesh I/O (Exodus, VTK, etc.)

#### Code Evidence
From `include/openmc/mesh.h`:
```cpp
#ifdef OPENMC_LIBMESH_ENABLED
#include "libmesh/bounding_box.h"
#include "libmesh/dof_map.h"
#include "libmesh/elem.h"
#include "libmesh/equation_systems.h"
#include "libmesh/exodusII_io.h"
#include "libmesh/explicit_system.h"
#include "libmesh/libmesh.h"
#include "libmesh/mesh.h"
#include "libmesh/point.h"

class LibMesh : public UnstructuredMesh {
  // Used for tally filters on unstructured meshes
};
```

#### CMake Configuration
```cmake
option(OPENMC_USE_LIBMESH "Enable support for libMesh unstructured mesh tallies" OFF)

if(OPENMC_USE_LIBMESH)
  find_package(LIBMESH REQUIRED)
endif()
```

#### Use Cases in OpenMC
1. **Unstructured mesh tallies**: Scoring neutron flux, reaction rates on tetrahedral/hexahedral meshes
2. **Collision estimators**: Element-by-element tally accumulation
3. **Mesh-based post-processing**: Results aligned with FEM meshes
4. **Coupling with other codes**: Data transfer via libMesh formats

### 3. Key Distinctions

| Feature | DAGMC (with MOAB) | libMesh |
|---------|-------------------|---------|
| **Purpose** | Geometry representation | Tally accumulation |
| **Stage** | Particle tracking | Result collection |
| **Mesh Type** | Surface mesh (triangulated) | Volume mesh (tet/hex elements) |
| **Primary Use** | Define where particles can go | Define where to score results |
| **Dependency** | MOAB | libMesh library |
| **CMake Flag** | `OPENMC_USE_DAGMC` | `OPENMC_USE_LIBMESH` |
| **Can be used together?** | Yes | Yes |
| **Independent?** | Yes | Yes |

### 4. Relationship Summary

```
OpenMC Core (CSG Geometry)
    |
    ├─── DAGMC (optional) ──> MOAB (required for DAGMC)
    |                              └─> Surface mesh representation
    |                              └─> Particle tracking acceleration
    |
    └─── libMesh (optional) ──> libMesh library
                                └─> Unstructured mesh tallies
                                └─> Result collection
```

These features can be enabled independently:
- **Neither**: Pure CSG geometry with structured mesh tallies
- **DAGMC only**: CAD geometry with structured mesh tallies
- **libMesh only**: CSG geometry with unstructured mesh tallies
- **Both**: CAD geometry with unstructured mesh tallies

### 5. What About Mesh Generation?

**Neither DAGMC nor libMesh are primarily used for mesh generation in OpenMC:**

1. **DAGMC**:
   - **Consumes** pre-generated surface meshes (`.h5m` files)
   - Mesh generation happens **externally** using CAD tools:
     - Cubit/Coreform (commercial CAD with DAGMC plugin)
     - Trelis (similar to Cubit)
     - Other CAD tools with DAGMC export capabilities
   - The `.h5m` file is created by imprinting, merging, and converting CAD geometry
   - MOAB stores and queries this mesh, but doesn't generate it

2. **libMesh**:
   - **Consumes** pre-generated unstructured meshes
   - Mesh generation happens **externally** using:
     - Gmsh (open-source mesh generator)
     - Cubit/Coreform
     - Other mesh generation tools
   - libMesh reads these meshes (Exodus, VTK, etc.) for tally purposes
   - libMesh has some mesh generation capabilities, but OpenMC primarily uses it for tallies

**Key Insight**: OpenMC doesn't generate meshes internally. It expects:
- DAGMC: Pre-generated surface meshes from CAD tools
- libMesh: Pre-generated volume meshes from mesh generators

## CGAL (Computational Geometry Algorithms Library) Analysis

### What is CGAL?

CGAL is a comprehensive C++ library providing:
- Geometric algorithms (convex hulls, triangulations, mesh processing)
- 2D and 3D computational geometry primitives
- Mesh generation (Delaunay triangulations, advancing front, etc.)
- Boolean operations on polygonal meshes
- Surface reconstruction
- Mesh simplification and remeshing
- Spatial searching and data structures

### Could CGAL Add Value to OpenMC?

#### Scenario 1: As a Replacement for MOAB in DAGMC

**Feasibility**: Low to Medium
**Value**: Limited

**Analysis**:
- MOAB is deeply integrated into DAGMC at the source level
- Replacing MOAB would require rewriting significant portions of DAGMC
- DAGMC is an **external dependency** - OpenMC doesn't control its implementation
- Any MOAB replacement would need to happen in the **DAGMC project**, not OpenMC
- MOAB's specialized features for DAGMC:
  - Hierarchical mesh representation (volumes, surfaces, curves, vertices)
  - Metadata and tagging system
  - Ray-tracing acceleration structures
  - Tight integration with CAD kernels

**Recommendation**: This is not practical for OpenMC to pursue, as DAGMC is maintained externally.

#### Scenario 2: As a Replacement for libMesh

**Feasibility**: Medium
**Value**: Limited

**Analysis**:
- CGAL is not designed for FEM applications like libMesh
- libMesh provides:
  - Equation systems and solvers
  - Degrees of freedom management
  - Parallel mesh partitioning
  - Extensive I/O formats
- CGAL provides:
  - Mesh generation and processing
  - Geometric algorithms
  - Basic mesh data structures
- **libMesh's role in OpenMC is narrow**: primarily for mesh-based tally filters
- Replacing it with CGAL would require rebuilding this functionality

**Recommendation**: Not recommended. libMesh is well-suited for its current use case.

#### Scenario 3: As a Complementary Tool for Mesh Generation

**Feasibility**: High
**Value**: Medium to High

**Analysis**:
This is the most promising scenario. CGAL could add value by:

1. **Pre-processing for DAGMC**:
   - Generate surface meshes from CAD geometries
   - Mesh repair and cleanup operations
   - Boolean operations on surface meshes
   - Mesh quality improvement

2. **Pre-processing for libMesh tallies**:
   - Generate unstructured volume meshes
   - Mesh adaptation and refinement
   - Create meshes optimized for tally accumulation

3. **New OpenMC features**:
   - Built-in mesh generation utilities
   - Geometry import from various formats
   - Automated mesh creation for simple geometries
   - Mesh analysis and quality metrics

**Implementation Path**:
- Add optional CGAL support via `OPENMC_USE_CGAL` CMake option
- Create Python API utilities for mesh generation
- Provide pre-processing tools that output:
  - `.h5m` files for DAGMC
  - Exodus/VTK files for libMesh
- Keep existing DAGMC/libMesh workflows intact

**Example Use Cases**:
```python
import openmc.mesh_utils  # New module using CGAL

# Generate a surface mesh for DAGMC from CSG geometry
mesh_gen = openmc.mesh_utils.SurfaceMeshGenerator()
mesh_gen.from_csg_cells([cell1, cell2, cell3])
mesh_gen.export_dagmc('geometry.h5m')

# Generate a volume mesh for libMesh tallies
vol_mesh = openmc.mesh_utils.VolumeM eshGenerator()
vol_mesh.from_stl('geometry.stl', max_element_size=1.0)
vol_mesh.export_exodus('tally_mesh.e')
```

#### Scenario 4: For Hybrid/Advanced Geometry Features

**Feasibility**: High
**Value**: Medium

**Analysis**:
CGAL could enable new OpenMC features:

1. **Automatic mesh generation from CSG**:
   - Convert CSG regions to surface/volume meshes
   - Bridge CSG and mesh-based approaches

2. **Geometry analysis**:
   - Automatic bounding box computation
   - Volume calculations
   - Surface area calculations
   - Overlap detection

3. **Mesh-based variance reduction**:
   - Generate weight window meshes
   - Adapt meshes based on importance

4. **Visualization improvements**:
   - High-quality mesh generation for plotting
   - Slice plane mesh intersections

## Recommendations

### Priority 1: CGAL as a Complementary Mesh Generation Tool (Recommended)

**Action**: Add CGAL as an **optional** pre-processing tool for mesh generation.

**Benefits**:
- Provides open-source mesh generation capabilities
- Reduces dependence on commercial CAD tools for simple geometries
- Enhances Python API with mesh utilities
- Maintains compatibility with existing DAGMC/libMesh workflows

**Implementation**:
1. Add `OPENMC_USE_CGAL` CMake option
2. Create `openmc.mesh_utils` Python module
3. Implement converters:
   - CSG → surface mesh → DAGMC `.h5m`
   - CSG → volume mesh → libMesh formats
   - STL/OBJ → `.h5m`
4. Document workflows and examples

**Timeline**: Medium-term (3-6 months development)

### Priority 2: Document Current Architecture (Quick Win)

**Action**: Update OpenMC documentation to clearly explain:
- DAGMC uses MOAB (not libMesh)
- DAGMC and libMesh are independent features
- Mesh generation happens externally
- Recommended workflows for CAD → DAGMC and mesh generation → libMesh

**Benefits**:
- Reduces user confusion
- Clarifies the architecture
- Improves onboarding for new developers

**Timeline**: Short-term (1-2 weeks)

### Priority 3: Evaluate CGAL for Advanced Features (Future Work)

**Action**: Conduct detailed feasibility study for:
- Automatic CSG to mesh conversion
- Geometry analysis utilities
- Advanced visualization
- Mesh adaptation for variance reduction

**Timeline**: Long-term (research phase)

## Conclusion

1. **DAGMC relies on MOAB, not libMesh**: This is the critical clarification. MOAB provides the mesh database and acceleration structures for DAGMC's surface mesh representation.

2. **libMesh is independent**: Used solely for unstructured mesh tallies during simulation.

3. **Neither is primarily for mesh generation**: Both consume pre-generated meshes from external tools.

4. **CGAL as a replacement**: Not practical or valuable for either MOAB (external to OpenMC) or libMesh (well-suited for its purpose).

5. **CGAL as a complement**: **Highly valuable** as an optional tool for:
   - Pre-processing and mesh generation
   - Bridging CSG and mesh-based workflows
   - Reducing dependence on commercial tools
   - Enhancing Python API capabilities

**Recommended Next Steps**:
1. Update documentation to clarify DAGMC/MOAB/libMesh relationships
2. Prototype CGAL integration for mesh generation utilities
3. Gather user feedback on mesh generation pain points
4. Implement `openmc.mesh_utils` module with CGAL backend

## Addendum: Constrained Delaunay Tetrahedralization in CGAL

### What is Constrained Delaunay Tetrahedralization?

**Constrained Delaunay Tetrahedralization (CDT)** is a mesh generation technique that creates a 3D tetrahedral mesh while respecting **constraints** such as:
- Prescribed boundary surfaces
- Internal surfaces/interfaces
- Sharp features (edges and vertices)
- Material boundaries

Unlike unconstrained Delaunay, CDT ensures that specific geometric features from the input (e.g., surfaces between different materials) are preserved exactly in the output mesh.

**CGAL Implementation**: CGAL provides `CGAL::Mesh_3` package with advanced 3D mesh generation capabilities including:
- Constrained Delaunay tetrahedralization
- Sizing fields for adaptive refinement
- Quality guarantees (dihedral angles, aspect ratios)
- Multi-domain meshing with internal boundaries

### Applications for OpenMC

#### 1. **Volume Mesh Generation for libMesh Tallies** (High Value)

**Use Case**: Generate high-quality tetrahedral meshes for unstructured mesh tallies.

**Benefits**:
- **Quality guarantees**: CDT ensures well-shaped tetrahedra suitable for Monte Carlo tallying
- **Boundary preservation**: Material interfaces preserved exactly, critical for accurate tallies
- **Adaptive refinement**: Finer meshes in regions of interest (e.g., high flux gradients)
- **Multi-material support**: Automatic handling of multiple material regions

**Workflow**:
```python
import openmc.mesh_utils

# Define geometry with material boundaries
geometry = openmc.Geometry(cells)

# Generate tetrahedral mesh with constrained boundaries
mesh_gen = openmc.mesh_utils.ConstrainedDelaunayMesh()
mesh_gen.add_domain(geometry, material_boundaries=True)
mesh_gen.set_sizing_field(refinement_function)  # Adaptive sizing
mesh_gen.generate()
mesh_gen.export_exodus('tally_mesh.e')

# Use for tallies
mesh = openmc.LibMesh('tally_mesh.e')
mesh_filter = openmc.MeshFilter(mesh)
tally = openmc.Tally()
tally.filters = [mesh_filter]
```

**Specific Value**:
- **Automatic meshing**: Users specify CSG geometry, CGAL generates mesh automatically
- **Material-aligned tallies**: Tetrahedra respect material boundaries, enabling accurate per-material scoring
- **Adaptive resolution**: Refine mesh in high-importance regions (near fuel, control rods)

#### 2. **Hybrid CSG-Mesh Geometry Conversion** (Medium-High Value)

**Use Case**: Convert CSG regions to tetrahedral meshes for hybrid transport methods.

**Benefits**:
- **Bridge CSG and mesh-based methods**: Enable deterministic-Monte Carlo coupling
- **Complex geometry handling**: CSG boolean operations → tetrahedral representation
- **Random ray solver support**: Tetrahedral meshes useful for random ray method

**Example Application**:
- Convert pin cell CSG geometry to tetrahedra for random ray solver
- Preserve fuel pellet, cladding, coolant boundaries exactly
- Generate fine mesh near fuel surface, coarse in coolant

#### 3. **Weight Window Mesh Generation** (Medium Value)

**Use Case**: Generate adaptive meshes for variance reduction.

**Benefits**:
- **Importance-based refinement**: Finer mesh where particle importance changes rapidly
- **Boundary alignment**: Respect geometric features important for transport
- **Optimal mesh sizing**: Balance accuracy vs. memory/computation

**Workflow**:
```python
# Generate weight window mesh based on importance map
ww_mesh = openmc.mesh_utils.AdaptiveWeightWindowMesh()
ww_mesh.from_importance_map(importance_function)
ww_mesh.refine_near_boundaries()  # Finer at interfaces
ww_mesh.export_weight_windows('ww_mesh.h5')
```

#### 4. **Depletion Mesh Generation** (Medium Value)

**Use Case**: Generate tetrahedral meshes for fine-grained depletion calculations.

**Benefits**:
- **Spatial resolution**: Capture flux gradients within fuel elements
- **Material boundaries**: Tetrahedra align with fuel-cladding interface
- **Burnup tracking**: Per-tetrahedron burnup tracking for detailed analysis

**Example**:
- Generate tetrahedral mesh of fuel assembly
- Each tetrahedron = independent depletion zone
- Track nuclide concentrations per tetrahedron
- More accurate than uniform pin-wise depletion

#### 5. **Sensitivity and Uncertainty Analysis Meshes** (Low-Medium Value)

**Use Case**: Generate meshes for adjoint calculations and sensitivity studies.

**Benefits**:
- **Detector region meshing**: Fine tetrahedral mesh around detectors
- **Response function support**: Mesh for computing response functionals
- **Perturbation studies**: Mesh-based material perturbations

### Technical Considerations

#### Advantages of CGAL CDT for OpenMC:

1. **Quality Guarantees**:
   - Minimum dihedral angle bounds
   - Maximum radius-edge ratio
   - Prevents sliver tetrahedra that cause numerical issues

2. **Constraint Preservation**:
   - Surfaces preserved exactly (material boundaries, geometric features)
   - Critical for OpenMC: particles crossing material boundaries must see correct interface

3. **Sizing Fields**:
   - Spatially varying element size
   - Refine where needed (flux gradients, geometric detail)
   - Coarsen elsewhere (reduce memory, computation)

4. **Robustness**:
   - Handles complex geometries reliably
   - Automatic handling of near-degeneracies
   - Well-tested on industrial CAD models

5. **Performance**:
   - Efficient algorithms (O(n log n) for n points)
   - Parallel mesh generation possible
   - Suitable for large-scale problems

#### Integration Challenges:

1. **CSG to Boundary Representation**:
   - OpenMC uses CSG, CDT needs boundary surfaces
   - Need conversion: CSG → surface triangulation → CDT domain
   - Non-trivial for complex CSG with many boolean operations

2. **Quality vs. Constraint Trade-off**:
   - Enforcing constraints may reduce element quality
   - May need to relax some quality requirements
   - Balance between accuracy and mesh quality

3. **Output Format Conversion**:
   - CGAL mesh → libMesh format (Exodus, VTK)
   - Need to handle element types, node numbering, material IDs
   - Metadata transfer (material assignments, boundary conditions)

### Comparison with Alternatives

| Method | Pros | Cons |
|--------|------|------|
| **CGAL CDT** | Quality guarantees, constraint preservation, adaptive | CSG conversion needed |
| **Gmsh** | Industry standard, GUI, scripting | Less programmable, external tool |
| **TetGen** | Fast, widely used | Licensing (AGPL), fewer features |
| **Triangle+TetGen** | Open source | 2D+3D separate, more complex workflow |

**CGAL Advantage**: Tight C++ integration with OpenMC, full programmatic control, no external executables.

### Recommended Implementation Approach

**Phase 1: Proof of Concept**
1. Implement CSG → boundary surface extraction
2. Use CGAL CDT to mesh a simple pin cell
3. Export to Exodus format
4. Verify mesh in libMesh tally

**Phase 2: Production Features**
1. Support for multi-material CSG geometries
2. Adaptive sizing based on geometry features
3. Quality control parameters exposed to users
4. Integration with OpenMC Python API

**Phase 3: Advanced Capabilities**
1. Importance-driven mesh adaptation
2. Mesh refinement for depletion
3. Hybrid CSG-mesh geometries
4. Parallel mesh generation

### Example Implementation (Conceptual)

```python
import openmc
import openmc.mesh_utils  # New module with CGAL

# Define OpenMC geometry (CSG)
fuel = openmc.Material()
fuel.add_nuclide('U235', 0.04)
fuel.add_nuclide('U238', 0.96)

clad = openmc.Material()
clad.add_element('Zr', 1.0)

fuel_cyl = openmc.ZCylinder(r=0.39)
clad_cyl = openmc.ZCylinder(r=0.46)

fuel_cell = openmc.Cell(fill=fuel, region=-fuel_cyl)
gap_cell = openmc.Cell(region=+fuel_cyl & -clad_cyl)
clad_cell = openmc.Cell(fill=clad, region=+clad_cyl)

# Generate constrained Delaunay tetrahedral mesh
cdt_mesh = openmc.mesh_utils.ConstrainedDelaunayMesh()

# Extract boundary surfaces from CSG and set as constraints
cdt_mesh.add_cells([fuel_cell, gap_cell, clad_cell])
cdt_mesh.preserve_material_boundaries = True

# Set sizing parameters
cdt_mesh.set_max_element_size(0.05)  # cm
cdt_mesh.set_min_element_size(0.005)  # cm near boundaries

# Set quality criteria
cdt_mesh.set_min_dihedral_angle(10.0)  # degrees
cdt_mesh.set_max_radius_edge_ratio(3.0)

# Generate mesh
cdt_mesh.generate()

# Export for libMesh
cdt_mesh.export_exodus('pin_cell_tally.e')

# Use in OpenMC simulation
tally_mesh = openmc.LibMesh('pin_cell_tally.e')
mesh_filter = openmc.MeshFilter(tally_mesh)

tally = openmc.Tally()
tally.filters = [mesh_filter]
tally.scores = ['flux', 'fission']
```

### Conclusion: Constrained Delaunay Tetrahedralization Value

**Answer**: Yes, CGAL's constrained Delaunay tetrahedralization has **significant application value** for OpenMC:

**Primary Applications** (High Value):
1. Automatic generation of high-quality tetrahedral meshes for libMesh tallies
2. Material-boundary-preserving meshes for accurate per-region scoring
3. Adaptive mesh refinement for variance reduction and detailed analysis

**Secondary Applications** (Medium Value):
4. Hybrid CSG-mesh geometry support
5. Weight window mesh generation
6. Fine-grained depletion zone creation

**Key Advantage**: Unlike external mesh generators, CGAL integration would provide **programmatic, automated mesh generation** directly from OpenMC's native CSG geometry, eliminating the need for manual mesh creation in external tools.

**Recommended**: Include constrained Delaunay tetrahedralization as a core feature of the proposed `openmc.mesh_utils` module with CGAL backend.

## References

- DAGMC Documentation: https://svalinn.github.io/DAGMC/
- MOAB Documentation: https://sigma.mcs.anl.gov/moab-library/
- libMesh Documentation: https://libmesh.github.io/
- CGAL Documentation: https://www.cgal.org/
- CGAL Mesh_3 Package: https://doc.cgal.org/latest/Mesh_3/index.html
- OpenMC User's Guide: https://docs.openmc.org/en/stable/usersguide/

---

**Document Version**: 1.1  
**Date**: January 23, 2026  
**Author**: Analysis based on OpenMC codebase investigation  
**Addendum**: Constrained Delaunay Tetrahedralization analysis added
