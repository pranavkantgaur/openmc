# Literature Knowledge Base - Quick Start Guide

## What is this?

The Literature Knowledge Base Service is an automated system that:
- 🔍 Searches academic databases for papers relevant to OpenMC acceleration
- 📊 Scores papers based on relevance to your interests
- 🤖 Automatically creates GitHub issues for promising papers
- 📚 Maintains a searchable database of all discovered papers

## Quick Start

### 1. Manual Test Run (Recommended First Step)

Test the system locally without creating any issues:

```bash
cd tools/knowledge_base
python run_literature_scan.py --dry-run --max-issues 3
```

This will:
- Search arXiv for relevant papers
- Show you what papers were found
- Display what issues would be created
- NOT actually create any GitHub issues

### 2. Customize Your Search

Edit `config.yaml` to customize:

```yaml
search_keywords:
  primary:
    - "OpenMC"
    - "Monte Carlo neutron transport"
  
  my_research_area:  # Add your own!
    - "your keyword here"
    - "another keyword"
```

### 3. Enable Automated Scanning

The system runs automatically via GitHub Actions:

**Schedule**: Every Monday at 9:00 UTC (configurable in `.github/workflows/literature-monitor.yml`)

**Manual Trigger**: 
1. Go to Actions tab in GitHub
2. Select "Literature Knowledge Base Monitor"
3. Click "Run workflow"
4. Configure options and run

### 4. Review Generated Issues

When papers are found, issues are created with:
- Label: `literature-enhancement`
- Full paper metadata and links
- Relevance score and matched keywords
- Suggested next steps

## Configuration Options

### Search Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_relevance_score` | 0.6 | Minimum score (0.0-1.0) for creating issues |
| `exclude_older_than_days` | 365 | Only search papers from last N days |
| `max_results` | 50 | Max papers per search query |

### Runtime Options

```bash
# Dry run (no issues created)
python run_literature_scan.py --dry-run

# Custom relevance threshold
python run_literature_scan.py --min-score 0.7

# Limit number of issues
python run_literature_scan.py --max-issues 2

# Combine options
python run_literature_scan.py --dry-run --min-score 0.8 --max-issues 5
```

## Understanding Relevance Scores

Scores range from 0.0 to 1.0:

- **0.8-1.0**: Highly relevant (mentions OpenMC or multiple keywords)
- **0.6-0.8**: Relevant (several matching keywords)
- **0.4-0.6**: Possibly relevant (few matching keywords)
- **0.0-0.4**: Low relevance

Papers below your threshold are not tracked.

## Database Management

### Location
`tools/knowledge_base/papers_database.json`

### Contents
- All discovered papers
- Relevance scores
- Matched keywords
- Created issue URLs
- Publication dates

### Querying

Use the example script:

```bash
cd tools/knowledge_base
python example_usage.py
```

Or programmatically:

```python
from knowledge_base import PaperDatabase
db = PaperDatabase("papers_database.json")
print(f"Total papers: {len(db.papers)}")
```

## Troubleshooting

### "No papers found"

**Cause**: Network issues or no matching papers in search period

**Solutions**:
- Check internet connectivity
- Reduce `min_relevance_score` to 0.3
- Increase `exclude_older_than_days` to 730 (2 years)
- Try broader keywords

### "Error creating GitHub issue"

**Cause**: Missing or invalid GitHub token

**Solutions**:
- Ensure `GITHUB_TOKEN` environment variable is set
- Verify token has `repo` scope
- Check `GITHUB_REPOSITORY` is in `owner/repo` format

### "Too many duplicate papers"

**Cause**: Database contains old entries

**Solution**: The database automatically prevents duplicates - no action needed!

## Advanced Usage

### Adding Custom Data Sources

Currently supports arXiv. To add more sources:

1. Implement a searcher class (like `ArXivSearcher`)
2. Add to `config.yaml`
3. Update `run_literature_scan.py`

Example sources: Google Scholar, PubMed, IEEE Xplore

### Custom Relevance Scoring

Edit `RelevanceScorer.score_paper()` in `literature_monitor.py` to implement custom scoring logic.

### Integration with Project Management

Use GitHub API to:
- Auto-assign issues to team members
- Add to project boards
- Link to roadmap items
- Create PR templates

## Best Practices

1. **Start with dry-run**: Always test before enabling auto-creation
2. **Review keywords regularly**: Update based on your research needs
3. **Adjust threshold**: Fine-tune `min_relevance_score` based on results
4. **Monitor weekly**: Check generated issues in your weekly reviews
5. **Close duplicates**: Mark as duplicate if idea already exists
6. **Link related work**: Connect to existing issues/PRs

## Examples

### Find all GPU acceleration papers
```bash
# Add to config.yaml
search_keywords:
  gpu:
    - "GPU acceleration"
    - "CUDA Monte Carlo"
    - "graphics processing unit"

# Run scan
python run_literature_scan.py --dry-run
```

### Focus on recent papers only
```bash
# Edit config.yaml
filters:
  exclude_older_than_days: 180  # Last 6 months only
```

### High-quality papers only
```bash
python run_literature_scan.py --min-score 0.9 --max-issues 1
```

## Getting Help

- **Documentation**: See `tools/knowledge_base/README.md`
- **Examples**: Run `python example_usage.py`
- **Tests**: Run `python test_literature_monitor.py`
- **Issues**: Create a GitHub issue with the `question` label

## Next Steps

1. ✅ Run a dry-run to see it in action
2. ✅ Customize keywords for your research
3. ✅ Let it run weekly and review results
4. ✅ Implement promising ideas!

Happy literature hunting! 📚🚀
