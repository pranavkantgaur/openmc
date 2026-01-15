# Contributing to the Literature Knowledge Base

Thank you for your interest in improving the Literature Knowledge Base Service!

## Ways to Contribute

### 1. Improve Search Keywords

The quality of discovered papers depends on our keywords. You can help by:

**Adding keywords** for new research areas:
```yaml
# In config.yaml
search_keywords:
  your_area:
    - "relevant keyword 1"
    - "relevant keyword 2"
```

**Refining existing keywords** to be more specific or inclusive.

### 2. Add New Data Sources

Currently, we only search arXiv. You can add:
- Google Scholar
- PubMed
- IEEE Xplore
- ACM Digital Library
- ResearchGate

**Steps**:
1. Create a new searcher class (inherit pattern from `ArXivSearcher`)
2. Implement the search API integration
3. Add configuration options
4. Update the main script to use it
5. Document API key requirements

### 3. Improve Relevance Scoring

The current scoring is keyword-based. You can improve it by:

- Using NLP techniques (sentiment, topic modeling)
- Adding citation count weighting
- Considering author reputation
- Using paper categories
- Implementing machine learning models

**Location**: `RelevanceScorer.score_paper()` in `literature_monitor.py`

### 4. Enhance Issue Templates

Make the generated GitHub issues more useful by:

- Adding implementation complexity estimates
- Including code examples from papers
- Linking to related OpenMC code sections
- Suggesting reviewers based on expertise

**Location**: `format_issue_body()` in `literature_monitor.py`

### 5. Add Features

Ideas for new features:

- **Paper summaries**: Use AI to generate summaries
- **Citation tracking**: Monitor citations of important papers
- **Author monitoring**: Track specific researchers
- **Collaboration detection**: Find papers citing OpenMC
- **Digest emails**: Weekly summary of findings
- **Slack/Discord integration**: Notify team channels
- **Priority scoring**: Mark papers as high/medium/low priority
- **Implementation estimates**: Time/complexity assessment
- **Related paper clustering**: Group similar papers

### 6. Improve Documentation

- Add more examples
- Create video tutorials
- Write blog posts about findings
- Document case studies of implemented ideas
- Translate documentation

### 7. Fix Bugs

Check the issues labeled `literature-enhancement` for bugs or improvements.

## Development Workflow

### Setup

```bash
cd tools/knowledge_base

# No special dependencies needed!
# Uses Python standard library + pyyaml
pip install pyyaml
```

### Testing

```bash
# Run test suite
python test_literature_monitor.py

# Test with dry run
python run_literature_scan.py --dry-run

# Test with custom parameters
python run_literature_scan.py --dry-run --min-score 0.3
```

### Making Changes

1. **Fork and clone** the repository
2. **Create a branch** for your changes
3. **Make your changes** with clear commits
4. **Test thoroughly** - run the test suite
5. **Update documentation** as needed
6. **Submit a pull request** with description

### Code Style

- Follow existing code patterns
- Add docstrings for new functions/classes
- Include type hints where helpful
- Keep functions focused and small
- Add comments for complex logic

### Testing Your Changes

Before submitting:

```bash
# 1. Run tests
python test_literature_monitor.py

# 2. Test dry run
python run_literature_scan.py --dry-run --max-issues 1

# 3. Test example script
python example_usage.py

# 4. Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

## Submitting Contributions

### Pull Request Checklist

- [ ] Code follows existing style
- [ ] Tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Tested in dry-run mode
- [ ] No sensitive data in commits

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes Made
- Item 1
- Item 2

## Testing
How was this tested?

## Related Issues
Closes #123
```

## Feature Request Process

Have an idea but don't want to implement it yourself?

1. Create a GitHub issue
2. Use the feature request template
3. Tag it with `literature-enhancement`
4. Describe the feature and use case
5. Wait for discussion and feedback

## Getting Help

- **Questions**: Ask in GitHub discussions
- **Bugs**: Create an issue with the bug template
- **Ideas**: Start a discussion thread
- **Urgent**: Tag maintainers in the issue

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in relevant documentation

## Code of Conduct

This project follows OpenMC's Code of Conduct. Be respectful, inclusive, and constructive.

## License

All contributions are subject to the project's MIT license.

---

Thank you for helping improve OpenMC's Literature Knowledge Base! 🙏
