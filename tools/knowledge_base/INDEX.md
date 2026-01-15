# Literature Knowledge Base - Documentation Index

Welcome! This directory contains a complete Literature Knowledge Base Service for automatically tracking relevant research papers and creating GitHub issues.

## 🚀 Getting Started

**New to this system?** Start here:

1. **[QUICKSTART.md](QUICKSTART.md)** ← START HERE
   - Quick installation and first run
   - 5-minute guide to get you up and running
   - Basic commands and examples

2. **[README.md](README.md)**
   - Complete user guide
   - All features explained in detail
   - Configuration reference

## 📚 Documentation Guide

### For Users

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [QUICKSTART.md](QUICKSTART.md) | Get started fast | First time using the system |
| [README.md](README.md) | Complete reference | When you need detailed info |
| [FAQ.md](FAQ.md) | Common questions | When you have a question |

### For Developers

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design | Understanding how it works |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development guide | Want to contribute |
| [CHANGELOG.md](CHANGELOG.md) | Version history | Track changes and roadmap |

## 📖 Document Details

### [QUICKSTART.md](QUICKSTART.md) (5.6 KB)
**The fastest way to start using the system**
- What it does
- How to test it
- Basic configuration
- Common commands
- Troubleshooting tips

**Read this if:** You want to start using the system in 5 minutes

### [README.md](README.md) (8.4 KB)
**The complete user manual**
- System overview
- All components explained
- Configuration reference
- Usage instructions
- GitHub integration
- Database management
- Advanced features

**Read this if:** You need comprehensive information about any feature

### [FAQ.md](FAQ.md) (8.4 KB)
**60+ frequently asked questions**
- General questions
- Setup & configuration
- Usage & operations
- Understanding results
- GitHub integration
- Database management
- Troubleshooting
- Advanced usage

**Read this if:** You have a specific question about the system

### [ARCHITECTURE.md](ARCHITECTURE.md) (10.5 KB)
**Technical architecture and design**
- System components diagram
- Data flow visualization
- Execution modes
- Relevance scoring algorithm
- Configuration structure
- Database schema
- Error handling

**Read this if:** You want to understand how the system works internally

### [CONTRIBUTING.md](CONTRIBUTING.md) (4.8 KB)
**Guide for contributors**
- Ways to contribute
- Development workflow
- Testing guidelines
- Code style
- Pull request process
- Feature request process

**Read this if:** You want to contribute improvements

### [CHANGELOG.md](CHANGELOG.md) (3.0 KB)
**Version history and roadmap**
- Current version (1.0.0)
- Features by version
- Planned features
- Future roadmap

**Read this if:** You want to know what's new or coming next

## 🎯 Quick Reference

### Essential Commands
```bash
# Test the system
python run_literature_scan.py --dry-run

# Add a paper manually
python add_paper.py --interactive

# View database
python view_database.py

# Run tests
python test_literature_monitor.py

# See examples
python example_usage.py
```

### Key Configuration Files
- **config.yaml** - Main configuration (keywords, thresholds, etc.)
- **papers_database.json** - Database of tracked papers
- **.github/workflows/literature-monitor.yml** - Automation workflow

### Important Directories
- **tools/knowledge_base/** - All source code and documentation
- **.github/ISSUE_TEMPLATE/** - GitHub issue templates
- **.github/workflows/** - GitHub Actions workflows

## 🔍 Finding Information

### By Task
- **First time setup** → [QUICKSTART.md](QUICKSTART.md)
- **Customize keywords** → [README.md](README.md#configuration)
- **Run manually** → [README.md](README.md#usage)
- **View papers** → [README.md](README.md#database-management)
- **Troubleshoot issue** → [FAQ.md](FAQ.md#troubleshooting)
- **Understand scoring** → [ARCHITECTURE.md](ARCHITECTURE.md#relevance-scoring-algorithm)
- **Add new source** → [CONTRIBUTING.md](CONTRIBUTING.md#add-new-data-sources)

### By Question
- "How do I...?" → [QUICKSTART.md](QUICKSTART.md) or [FAQ.md](FAQ.md)
- "What does...?" → [README.md](README.md) or [ARCHITECTURE.md](ARCHITECTURE.md)
- "Why is...?" → [FAQ.md](FAQ.md)
- "Can I...?" → [FAQ.md](FAQ.md) or [CONTRIBUTING.md](CONTRIBUTING.md)

## 💡 Pro Tips

1. **Start with QUICKSTART.md** - Don't skip this, it will save you time
2. **Use dry-run mode** - Always test with `--dry-run` first
3. **Check FAQ first** - Your question is probably already answered
4. **Keep docs open** - Bookmark this index for quick reference
5. **Customize keywords** - The default keywords are starting points

## 📞 Getting Help

1. **Check documentation** - Use this index to find the right doc
2. **Search FAQ** - 60+ questions already answered
3. **Run examples** - `python example_usage.py`
4. **Ask questions** - Create GitHub issue with 'question' label
5. **Report bugs** - Create GitHub issue with bug report template

## 📈 Documentation Stats

- **Total documents**: 7
- **Total size**: ~45 KB
- **Total content**: ~20,000 words
- **Coverage**: All features documented
- **Examples**: 50+ code examples
- **Questions answered**: 60+

## 🎓 Learning Path

**Beginner Path:**
1. Read QUICKSTART.md (5 min)
2. Run `python run_literature_scan.py --dry-run` (2 min)
3. Try `python view_database.py` (1 min)
4. Skim FAQ.md for common patterns (10 min)

**Advanced Path:**
1. Read README.md thoroughly (20 min)
2. Study ARCHITECTURE.md (15 min)
3. Review CONTRIBUTING.md (10 min)
4. Experiment with customization (30 min)

**Developer Path:**
1. Read ARCHITECTURE.md (15 min)
2. Study the code (30 min)
3. Read CONTRIBUTING.md (10 min)
4. Run and modify tests (20 min)

## ✨ Best Practices

- ✅ Start with dry-run mode
- ✅ Customize keywords for your needs
- ✅ Review generated issues regularly
- ✅ Keep documentation bookmarked
- ✅ Update when new features arrive

## 🎯 Document Purpose Summary

| Doc | Size | Purpose | Audience |
|-----|------|---------|----------|
| QUICKSTART | 5.6 KB | Fast start | Everyone |
| README | 8.4 KB | Complete guide | Users |
| FAQ | 8.4 KB | Q&A | Everyone |
| ARCHITECTURE | 10.5 KB | Design docs | Developers |
| CONTRIBUTING | 4.8 KB | Dev guide | Contributors |
| CHANGELOG | 3.0 KB | History | Everyone |
| INDEX (this) | 6 KB | Navigation | Everyone |

---

**Happy literature hunting! 📚🚀**

*Last updated: January 15, 2026*
