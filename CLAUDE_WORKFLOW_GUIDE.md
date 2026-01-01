# AI-Assisted Development Workflow for OpenMC

This guide explains how to leverage AI assistants (like Claude or GitHub Copilot) to perform comprehensive development activities on the OpenMC repository, similar to the workflow described in the nanochat experiments.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Core Development Activities](#core-development-activities)
3. [Debugging and Testing](#debugging-and-testing)
4. [Monitoring and Profiling](#monitoring-and-profiling)
5. [PR Management](#pr-management)
6. [Documentation and Tracking](#documentation-and-tracking)
7. [Best Practices](#best-practices)

## Prerequisites

### Environment Setup
Before starting AI-assisted development, ensure your environment is properly configured:

```bash
# 1. Clone the repository
git clone https://github.com/openmc-dev/openmc.git
cd openmc

# 2. Download nuclear data (required for tests)
bash tools/ci/download-xs.sh
export OPENMC_CROSS_SECTIONS=$HOME/nndc_hdf5/cross_sections.xml

# 3. Set OpenMP threads (prevents test failures)
export OMP_NUM_THREADS=2

# 4. Build the C++ library
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Debug -DOPENMC_BUILD_TESTS=ON
make -j
cd ..

# 5. Install Python package in development mode
pip install -e .
```

### Understanding the Codebase
Familiarize yourself with:
- **AGENTS.md**: Comprehensive guide for AI agents working on OpenMC
- **CONTRIBUTING.md**: Contribution guidelines
- **README.md**: Project overview
- **docs/source/**: User and developer documentation

## Core Development Activities

### 1. Writing Implementations

#### For Python Features
When implementing new Python features:

```python
# Example: Adding a new tally feature
# 1. Define the class with proper validation
import openmc.checkvalue as cv

class MyNewTally(openmc.Tally):
    """Custom tally implementation
    
    Parameters
    ----------
    my_param : float
        Description of parameter
        
    Attributes
    ----------
    my_param : float
        Description of attribute
    """
    
    def __init__(self, my_param=None):
        super().__init__()
        self._my_param = None
        if my_param is not None:
            self.my_param = my_param
    
    @property
    def my_param(self):
        return self._my_param
    
    @my_param.setter
    def my_param(self, value):
        cv.check_type('my_param', value, Real)
        cv.check_greater_than('my_param', value, 0.0)
        self._my_param = value
```

**AI Assistant Tasks:**
- Generate boilerplate code following OpenMC conventions
- Implement proper input validation using `openmc.checkvalue`
- Create XML serialization methods (`to_xml_element`, `from_xml_element`)
- Write numpydoc-formatted docstrings

#### For C++ Features
When implementing new C++ features:

```cpp
// Example: Adding a new geometry feature
// Use OpenMC containers, not std:: directly
#include "openmc/vector.h"
#include "openmc/memory.h"

namespace openmc {

class MyNewGeometry {
private:
  vector<unique_ptr<Cell>> cells_;  // Use openmc::vector
  double parameter_;
  
public:
  MyNewGeometry(double param) : parameter_(param) {}
  
  // Follow snake_case for methods
  void add_cell(unique_ptr<Cell> cell);
  const vector<unique_ptr<Cell>>& cells() const { return cells_; }
};

} // namespace openmc
```

**AI Assistant Tasks:**
- Follow C++17 standards and OpenMC naming conventions
- Use OpenMC container types (`openmc::vector`, not `std::vector`)
- Add proper Doxygen comments
- Implement RAII patterns
- Handle optional features with `#ifdef` guards (MPI, DAGMC, etc.)

### 2. Debugging with Toy Examples

Create minimal reproducible examples to test features:

```python
# test_toy_example.py
import openmc

def test_minimal_case():
    """Minimal example to verify feature works"""
    # Create simple geometry
    mat = openmc.Material()
    mat.add_nuclide('U235', 1.0)
    mat.set_density('g/cm3', 10.0)
    
    surf = openmc.Sphere(r=10.0, boundary_type='vacuum')
    cell = openmc.Cell(fill=mat, region=-surf)
    
    # Test your feature here
    geometry = openmc.Geometry([cell])
    settings = openmc.Settings()
    settings.particles = 100
    settings.batches = 5
    
    model = openmc.Model(geometry=geometry, settings=settings)
    # Run or test specific functionality
```

**AI Assistant Tasks:**
- Generate toy examples for quick iteration
- Modify examples to exercise edge cases
- Debug failures by examining traceback and adjusting code
- Incrementally build complexity

## Debugging and Testing

### 3. Writing and Running Tests

#### Unit Tests
Fast tests that don't require running simulations:

```python
# tests/unit_tests/test_my_feature.py
import pytest
import openmc

def test_my_feature_creation():
    """Test object creation"""
    obj = openmc.MyNewFeature()
    assert obj is not None

def test_my_feature_validation():
    """Test input validation"""
    obj = openmc.MyNewFeature()
    with pytest.raises(TypeError):
        obj.parameter = "invalid"  # Should be numeric
    
    with pytest.raises(ValueError):
        obj.parameter = -1.0  # Should be positive

def test_my_feature_xml():
    """Test XML serialization"""
    obj = openmc.MyNewFeature()
    obj.parameter = 1.5
    elem = obj.to_xml_element()
    assert elem is not None
    
    # Round-trip test
    obj2 = openmc.MyNewFeature.from_xml_element(elem)
    assert obj2.parameter == obj.parameter
```

**Run unit tests:**
```bash
pytest tests/unit_tests/test_my_feature.py -v
```

#### Regression Tests
Tests that compare simulation output against reference data:

```python
# tests/regression_tests/my_test/test.py
from openmc.examples import pwr_pin_cell
from tests.testing_harness import PyAPITestHarness

def test_my_feature():
    """Test new feature with full simulation"""
    model = pwr_pin_cell()
    
    # Modify model to use your feature
    model.settings.particles = 1000
    model.settings.batches = 10
    
    # Use test harness
    harness = PyAPITestHarness('statepoint.10.h5', model)
    harness.main()
```

**Generate reference data:**
```bash
cd tests/regression_tests/my_test
pytest test.py --update
```

**Run regression test:**
```bash
pytest tests/regression_tests/my_test/test.py
```

**AI Assistant Tasks:**
- Generate comprehensive test cases
- Create fixtures for common test scenarios
- Debug test failures by examining output
- Update reference data when code changes are correct
- Run subsets of tests to validate changes incrementally

### 4. Making Tests Pass/Fail Intentionally

Use test-driven development:

```python
# 1. Write a failing test first
def test_new_feature_not_implemented():
    """This should fail until feature is implemented"""
    with pytest.raises(NotImplementedError):
        result = openmc.my_new_feature()

# 2. Implement the feature
def my_new_feature():
    # Implementation here
    return result

# 3. Update test to verify correct behavior
def test_new_feature_works():
    """Now test the actual functionality"""
    result = openmc.my_new_feature()
    assert result is not None
    assert result.some_property == expected_value
```

**AI Assistant Tasks:**
- Write tests that define expected behavior before implementation
- Iterate between failing and passing tests
- Ensure tests catch regressions

## Monitoring and Profiling

### 5. Launching and Monitoring Runs

For long-running simulations:

```bash
# Launch simulation in background
python my_simulation.py > output.log 2>&1 &
PID=$!

# Monitor progress
tail -f output.log

# Check if still running
ps -p $PID
```

**AI Assistant Tasks:**
- Launch simulations with appropriate parameters
- Monitor log files for errors or warnings
- Track progress through output
- Detect when simulations hang or fail

### 6. Profiling and Optimization

#### Python Profiling
```python
import cProfile
import pstats
from pstats import SortKey

# Profile your code
cProfile.run('my_function()', 'profile_stats')

# Analyze results
p = pstats.Stats('profile_stats')
p.strip_dirs()
p.sort_stats(SortKey.CUMULATIVE)
p.print_stats(20)  # Top 20 functions
```

#### C++ Profiling
```bash
# Build with profiling enabled
cmake .. -DOPENMC_ENABLE_PROFILE=ON
make -j

# Run with profiling
./build/bin/openmc

# Analyze with gprof or perf
gprof ./build/bin/openmc gmon.out > analysis.txt
```

**AI Assistant Tasks:**
- Identify performance bottlenecks
- Suggest optimization strategies
- Implement optimizations
- Measure performance improvements
- Compare before/after metrics

### 7. Measuring Improvements

Create benchmarking scripts:

```python
# benchmark.py
import time
import openmc
from openmc.examples import pwr_pin_cell

def benchmark_simulation():
    """Benchmark simulation performance"""
    model = pwr_pin_cell()
    model.settings.particles = 10000
    model.settings.batches = 100
    
    start = time.time()
    # Run simulation
    model.run()
    end = time.time()
    
    return end - start

# Run multiple times and average
times = [benchmark_simulation() for _ in range(5)]
avg_time = sum(times) / len(times)
print(f"Average time: {avg_time:.2f} seconds")
```

**AI Assistant Tasks:**
- Create reproducible benchmarks
- Run before/after comparisons
- Generate performance reports
- Visualize performance metrics

## PR Management

### 8. Analyzing and Categorizing PRs

Use GitHub CLI or API:

```bash
# List open PRs
gh pr list --state open --limit 50

# Get details about specific PR
gh pr view <PR_NUMBER>

# Check CI status
gh pr checks <PR_NUMBER>
```

**AI Assistant Tasks:**
- Review all open PRs
- Categorize by type (bug fix, feature, documentation, etc.)
- Identify priority based on:
  - Number of comments/reactions
  - Age of PR
  - Complexity
  - Dependencies on other PRs
- Suggest review order

### 9. Prioritizing PRs

Create a prioritization matrix:

| PR # | Title | Type | Age | Complexity | Priority |
|------|-------|------|-----|------------|----------|
| 123  | Fix memory leak | Bug | 2 weeks | Low | High |
| 124  | Add new feature | Feature | 1 month | High | Medium |
| 125  | Update docs | Docs | 3 days | Low | Low |

**Prioritization Criteria:**
1. **Critical bugs** - highest priority
2. **Breaking changes** - need immediate attention
3. **Performance improvements** - high value
4. **New features** - medium priority
5. **Documentation** - ongoing
6. **Code cleanup** - lower priority

**AI Assistant Tasks:**
- Generate prioritization matrix
- Identify dependencies between PRs
- Highlight PRs that are blocking others
- Track review status

### 10. Making Commits Against PRs

When working on PRs:

```bash
# Checkout PR branch
gh pr checkout <PR_NUMBER>

# Make changes
# ... edit files ...

# Run tests
pytest tests/unit_tests/

# Commit with clear message
git add .
git commit -m "Fix: Resolve issue with X
- Address code review comment
- Update tests
- Add documentation"

# Push to PR branch
git push
```

**AI Assistant Tasks:**
- Review PR diff and understand changes
- Identify issues or improvements
- Make targeted fixes
- Ensure tests pass
- Write clear commit messages

## Documentation and Tracking

### 11. Maintaining Running Documentation

Create a development log:

```markdown
# Development Log - My Feature

## 2026-01-01

### Completed
- [x] Implemented basic MyNewFeature class
- [x] Added input validation
- [x] Created unit tests (10/10 passing)

### In Progress
- [ ] Add XML serialization
- [ ] Write regression tests

### Issues Found
- Memory leak in C++ implementation (fixed in commit abc123)
- Test failure on MPI builds (investigating)

### Performance Notes
- Initial benchmark: 45.2s
- After optimization: 32.8s (27% improvement)

### Next Steps
1. Complete XML serialization
2. Add C API bindings
3. Update documentation
```

**AI Assistant Tasks:**
- Generate daily summaries
- Track completed vs. pending work
- Note important findings
- Document design decisions
- Record performance metrics

### 12. Recording Runs and Results

Create a structured results log:

```markdown
# Experiment Results

## Run 1: Baseline Configuration
- **Date**: 2026-01-01
- **Commit**: abc123
- **Config**: 10k particles, 100 batches
- **Result**: k-eff = 1.18456 ± 0.00023
- **Time**: 45.2s
- **Notes**: Baseline performance

## Run 2: Optimized Version
- **Date**: 2026-01-01
- **Commit**: def456
- **Config**: 10k particles, 100 batches
- **Result**: k-eff = 1.18458 ± 0.00023
- **Time**: 32.8s
- **Notes**: 27% faster, results match within statistical uncertainty

## Comparison Table
| Run | k-eff | Uncertainty | Time (s) | Speedup |
|-----|-------|-------------|----------|---------|
| 1   | 1.18456 | 0.00023 | 45.2 | 1.00x |
| 2   | 1.18458 | 0.00023 | 32.8 | 1.38x |
```

**AI Assistant Tasks:**
- Parse simulation output
- Extract key metrics
- Generate comparison tables
- Create visualizations
- Track experiments systematically

### 13. Presenting Results in Tables

Use markdown tables for clarity:

```markdown
# Performance Comparison

## Memory Usage
| Component | Before | After | Reduction |
|-----------|--------|-------|-----------|
| Geometry  | 2.3 GB | 1.8 GB | 21.7% |
| Tallies   | 890 MB | 890 MB | 0% |
| Cross-sec | 1.2 GB | 1.2 GB | 0% |
| **Total** | **4.4 GB** | **3.9 GB** | **11.4%** |

## Execution Time Breakdown
| Phase | Before | After | Speedup |
|-------|--------|-------|---------|
| Initialization | 2.3s | 2.1s | 1.10x |
| Transport | 38.7s | 27.5s | 1.41x |
| Tallying | 3.2s | 2.4s | 1.33x |
| Output | 1.0s | 0.8s | 1.25x |
| **Total** | **45.2s** | **32.8s** | **1.38x** |
```

**AI Assistant Tasks:**
- Generate formatted tables
- Calculate derived metrics (speedup, percentage changes)
- Highlight significant changes
- Create summary visualizations

## Best Practices

### Working Effectively with AI Assistants

1. **Be Specific**: Provide clear, detailed instructions
   - ❌ "Make it faster"
   - ✅ "Profile the transport loop and optimize the hot path identified"

2. **Iterate Incrementally**: Make small, testable changes
   - Don't try to implement entire features in one go
   - Test each change before moving forward

3. **Verify AI Output**: AI can make mistakes
   - Review generated code carefully
   - Run tests frequently
   - Check that implementations follow OpenMC conventions

4. **Provide Context**: Share relevant information
   - Link to related code sections
   - Mention constraints or requirements
   - Note any previous attempts or known issues

5. **Use AI for Tedious Tasks**: Leverage automation
   - Generating boilerplate code
   - Writing repetitive tests
   - Formatting documentation
   - Analyzing logs and metrics

6. **Keep Humans in the Loop**: Don't blindly accept
   - Review design decisions
   - Question unusual patterns
   - Validate performance claims
   - Ensure code quality

### Handling AI "Brain Farts"

AI assistants can get confused or make errors:

**Signs of AI Confusion:**
- Contradictory statements
- Ignoring previous context
- Generating invalid code
- Hallucinating features that don't exist

**How to Handle:**
1. **Stop and reset**: "Let's start over with this specific issue"
2. **Simplify**: Break down complex tasks into smaller pieces
3. **Provide examples**: Show the AI what you want
4. **Verify incrementally**: Test small changes before proceeding

### Collaboration Model

Think of AI as a **capable but inexperienced junior developer**:

**AI Strengths:**
- Fast code generation
- Tireless execution of repetitive tasks
- Good at following patterns
- Can work on multiple things simultaneously
- Never gets bored with tedious work

**AI Weaknesses:**
- Can make subtle logical errors
- May miss important edge cases
- Doesn't understand broader project context without prompting
- Can suggest overly complex or poorly coupled designs
- May not follow best practices without guidance

**Your Role:**
- Provide direction and priorities
- Review and validate AI output
- Catch design issues early
- Make architectural decisions
- Ensure quality and maintainability

## Example Workflow: Adding a New Feature

Here's a complete workflow for adding a new feature with AI assistance:

### Phase 1: Planning (5-10 minutes)
```
You: "I want to add support for custom tallies in OpenMC. Can you:
1. Review existing tally implementation
2. Identify what needs to be modified
3. Create a plan with specific steps"

AI: [Generates detailed plan]

You: [Review plan, make adjustments]
```

### Phase 2: Implementation (30-60 minutes)
```
You: "Implement step 1 from the plan: Create CustomTally class"

AI: [Generates code]

You: [Review, suggest improvements]

You: "Add unit tests for CustomTally"

AI: [Generates tests]

You: "Run the tests"

AI: [Runs pytest, reports results]

You: [Fix any issues identified]
```

### Phase 3: Integration (20-40 minutes)
```
You: "Add C API bindings for CustomTally"

AI: [Modifies capi.h and openmc/lib/]

You: "Create a regression test"

AI: [Creates test using PyAPITestHarness]

You: "Generate reference data"

AI: [Runs pytest --update]
```

### Phase 4: Documentation (10-20 minutes)
```
You: "Update documentation to include CustomTally"

AI: [Modifies docs/source/]

You: "Add example usage"

AI: [Creates example in docs/source/examples/]
```

### Phase 5: Validation (15-30 minutes)
```
You: "Run full test suite"

AI: [Executes pytest, reports failures]

You: [Review failures, identify issues]

You: "Fix the MPI test failure"

AI: [Makes targeted fix]

You: "Re-run tests"

AI: [Confirms all pass]
```

### Phase 6: Review (10-15 minutes)
```
You: "Create a summary of changes with performance metrics"

AI: [Generates markdown document with tables]

You: "Run clang-format on C++ files"

AI: [Formats code]

You: "Create PR description"

AI: [Generates description based on changes]
```

**Total Time**: 90-175 minutes for a complete feature

## Monitoring Integration

### Setting Up Continuous Monitoring

Create monitoring scripts:

```python
# monitor.py
import time
import subprocess
import sys

def monitor_simulation(process, interval=10):
    """Monitor running simulation"""
    while process.poll() is None:
        # Check for new output
        output = process.stdout.readline()
        if output:
            print(output.strip())
            
            # Look for specific patterns
            if "ERROR" in output:
                print("⚠️  Error detected!")
            elif "Generation" in output:
                print("✓ Progress update")
        
        time.sleep(interval)
    
    # Get final output
    stdout, stderr = process.communicate()
    return process.returncode

# Use it
proc = subprocess.Popen(
    ['python', 'simulation.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True
)

exit_code = monitor_simulation(proc)
sys.exit(exit_code)
```

**AI Assistant Tasks:**
- Monitor long-running simulations
- Alert on errors or anomalies
- Track progress metrics
- Restart failed runs
- Aggregate results

## Conclusion

This workflow enables you to leverage AI assistants to:
- **Accelerate development** through rapid prototyping and implementation
- **Improve quality** through comprehensive testing and validation
- **Maintain organization** with structured documentation and tracking
- **Optimize performance** through profiling and iterative improvements
- **Manage complexity** by breaking down large tasks into manageable pieces

The key is maintaining oversight while delegating routine tasks to AI, creating a collaborative workflow that combines human judgment with AI capabilities.

## Additional Resources

- **OpenMC Documentation**: https://docs.openmc.org
- **AGENTS.md**: Detailed guide for AI agents
- **CONTRIBUTING.md**: Contribution guidelines
- **GitHub Discussions**: https://openmc.discourse.group/
- **CI Workflows**: `.github/workflows/ci.yml`

## Getting Help

When you encounter issues:
1. Check documentation first
2. Search existing GitHub issues
3. Ask on the discussion forum
4. Use AI assistants to debug systematically
5. Consult with human experts when AI gets stuck
