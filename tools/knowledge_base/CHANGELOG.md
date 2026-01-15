# Changelog - Literature Knowledge Base Service

All notable changes to the Literature Knowledge Base Service will be documented in this file.

## [1.0.0] - 2024-01-15

### Added
- Initial implementation of Literature Knowledge Base Service
- arXiv integration for automated paper discovery
- Keyword-based relevance scoring algorithm
- JSON database for persistent paper storage
- GitHub issue automation via API
- GitHub Actions workflow for scheduled scanning
- Custom GitHub issue template for literature-based features
- Comprehensive configuration via YAML
- Command-line interface with multiple options
- Dry-run mode for testing without creating issues
- Deduplication logic to prevent duplicate issues
- Comprehensive test suite with all tests passing
- Example usage script demonstrating API
- Full documentation (README, QUICKSTART, CONTRIBUTING)

### Features
- **Automated Scanning**: Weekly scheduled runs via GitHub Actions
- **Manual Triggers**: Run on-demand with custom parameters
- **Intelligent Filtering**: Score-based paper relevance
- **Database Management**: Track all discovered papers
- **Issue Creation**: Automatic GitHub issue generation
- **Error Handling**: Graceful failure with informative messages

### Documentation
- README.md: Complete user guide
- QUICKSTART.md: Quick start guide for new users
- CONTRIBUTING.md: Contribution guidelines
- CHANGELOG.md: This file
- Inline code documentation and docstrings

### Configuration
- 21 search keywords across multiple categories
- arXiv categories: nucl-th, physics.comp-ph
- Relevance threshold: 0.6 (configurable)
- Time window: Last 365 days (configurable)
- Max issues per run: 5 (configurable)

### Dependencies
- Python 3.11+
- pyyaml (only external dependency)
- Standard library only for core functionality

## Future Releases

### Planned for [1.1.0]
- [ ] Google Scholar integration
- [ ] Machine learning-based relevance scoring
- [ ] Paper summary generation
- [ ] Citation tracking
- [ ] Email digest notifications

### Planned for [1.2.0]
- [ ] Multi-language support
- [ ] Paper clustering by topic
- [ ] Author tracking
- [ ] Implementation complexity scoring
- [ ] Integration with project management tools

### Ideas for Future Versions
- Web dashboard for browsing papers
- Slack/Discord notifications
- PDF full-text analysis
- Automated paper reviews using AI
- Collaboration network visualization
- Priority scoring based on impact factor
- Integration with reference managers (Zotero, Mendeley)

## Versioning

This project follows [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: New features (backwards compatible)
- PATCH: Bug fixes (backwards compatible)

## Release Process

1. Update version in `__init__.py`
2. Update CHANGELOG.md
3. Create git tag: `git tag -a v1.0.0 -m "Release 1.0.0"`
4. Push tag: `git push origin v1.0.0`
5. Create GitHub release with notes

## Support

For issues or questions about specific versions:
- Create a GitHub issue
- Tag with version number
- Include reproduction steps
