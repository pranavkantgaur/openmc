# OpenMC Development Tools

This directory contains various tools and utilities for OpenMC development and automation.

## Directory Structure

### `ci/` - Continuous Integration Scripts
Scripts used by GitHub Actions for automated testing:
- `download-xs.sh` - Download nuclear cross-section data
- `gha-*.sh` - GitHub Actions helper scripts
- Build and test automation

### `dev/` - Development Utilities
Tools for OpenMC developers:
- `generate_release_notes.py` - Generate release notes from git history
- `install-commit-hooks.sh` - Install pre-commit hooks for code formatting

### `knowledge_base/` - Literature Knowledge Base Service
**NEW**: Automated literature monitoring system that tracks academic papers related to OpenMC acceleration.

#### Features
- 🔍 Automatic arXiv literature scanning
- 📊 Intelligent relevance scoring
- 🤖 GitHub issue automation
- 📚 Persistent paper database
- ⏰ Scheduled weekly runs

#### Quick Start
```bash
cd knowledge_base

# Test run (no issues created)
python run_literature_scan.py --dry-run

# View database
python view_database.py

# Add paper manually
python add_paper.py --interactive
```

#### Documentation
- [README.md](knowledge_base/README.md) - Complete guide
- [QUICKSTART.md](knowledge_base/QUICKSTART.md) - Getting started
- [CONTRIBUTING.md](knowledge_base/CONTRIBUTING.md) - How to contribute

#### How It Works
```
┌─────────────────────────────────────────────────────────────┐
│                  Literature Monitoring Flow                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐      │
│  │  arXiv   │───────▶│ Keyword  │───────▶│ Relevance│      │
│  │  Search  │        │ Matching │        │  Scoring │      │
│  └──────────┘        └──────────┘        └──────────┘      │
│       │                    │                    │            │
│       │                    │                    ▼            │
│       │                    │            ┌──────────┐        │
│       │                    └───────────▶│ Database │        │
│       │                                 │  (JSON)  │        │
│       │                                 └──────────┘        │
│       │                                      │               │
│       │                                      │               │
│       ▼                                      ▼               │
│  ┌──────────┐                        ┌──────────┐          │
│  │  GitHub  │◀───────────────────────│  Create  │          │
│  │  Issues  │                        │  Issue   │          │
│  └──────────┘                        └──────────┘          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
    Runs weekly via GitHub Actions (Monday 9:00 UTC)
    or manually via workflow dispatch
```

#### Workflow Status
[![Literature Monitor](https://github.com/pranavkantgaur/openmc/actions/workflows/literature-monitor.yml/badge.svg)](https://github.com/pranavkantgaur/openmc/actions/workflows/literature-monitor.yml)

---

## Using These Tools

### For CI/Automation
The `ci/` scripts are primarily for GitHub Actions but can be run locally for testing.

### For Development
The `dev/` tools help maintain code quality and generate documentation.

### For Literature Tracking
The `knowledge_base/` service helps track relevant research:
1. Runs automatically every Monday
2. Creates GitHub issues for relevant papers
3. Maintains searchable database
4. See `knowledge_base/README.md` for details

## Contributing

To contribute to any tool:
1. Test your changes locally
2. Update relevant documentation
3. Submit a pull request
4. See individual tool READMEs for specific guidelines

## Questions?

- **CI Issues**: Check `.github/workflows/` configurations
- **Development Tools**: See individual script comments
- **Knowledge Base**: See `knowledge_base/QUICKSTART.md`
- **General**: Open a GitHub issue or discussion
