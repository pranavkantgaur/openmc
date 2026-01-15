# OpenMC Literature Knowledge Base Service

This service automatically monitors academic literature for research papers and ideas that could potentially accelerate OpenMC simulations or improve its multiphysics capabilities. When relevant papers are found, the service automatically creates GitHub issues for review and potential implementation.

## Overview

The Literature Knowledge Base Service provides:

1. **Automated Literature Monitoring**: Periodically searches academic databases (arXiv, etc.) for relevant papers
2. **Intelligent Filtering**: Uses keyword matching and relevance scoring to identify promising papers
3. **GitHub Integration**: Automatically creates feature request issues for high-relevance papers
4. **Knowledge Base**: Maintains a database of all tracked papers to prevent duplicates
5. **Scheduled Execution**: Runs weekly via GitHub Actions to continuously discover new research

## Architecture

### Components

- **`literature_monitor.py`**: Core module containing:
  - `Paper`: Data class for paper metadata
  - `PaperDatabase`: JSON-based database for tracking papers
  - `ArXivSearcher`: Interface to arXiv API
  - `RelevanceScorer`: Scoring algorithm for paper relevance
  
- **`run_literature_scan.py`**: Main script that orchestrates:
  - Paper searching
  - Relevance scoring
  - GitHub issue creation
  - Database management
  
- **`config.yaml`**: Configuration file defining:
  - Search keywords and categories
  - Data sources (arXiv, etc.)
  - Filtering criteria
  - GitHub settings
  
- **`papers_database.json`**: JSON database tracking:
  - All discovered papers
  - Relevance scores
  - Created GitHub issues
  - Metadata and timestamps

## Configuration

### Search Keywords

The service searches for papers using keywords defined in `config.yaml`:

```yaml
search_keywords:
  primary:
    - "Monte Carlo particle transport"
    - "OpenMC"
    
  acceleration_techniques:
    - "variance reduction"
    - "GPU acceleration"
    - "weight window"
    
  multiphysics:
    - "thermal hydraulics coupling"
    - "multiphysics simulation"
```

Keywords are organized by category for easier maintenance.

### Data Sources

Currently supported:
- **arXiv**: Nuclear theory and computational physics categories
- Future: Google Scholar, PubMed, IEEE Xplore (requires API keys)

### Filtering Criteria

Papers are filtered based on:
- **Relevance score**: Calculated from keyword matches (configurable threshold)
- **Publication date**: Only recent papers (default: last 365 days)
- **Duplication**: Automatically excluded if already in database

## Usage

### Manual Execution

Run the literature scan locally:

```bash
cd tools/knowledge_base

# Basic usage (dry run)
python run_literature_scan.py --dry-run

# With custom parameters
python run_literature_scan.py \
  --min-score 0.7 \
  --max-issues 3

# Real run (requires GitHub token)
export GITHUB_TOKEN=your_token_here
export GITHUB_REPOSITORY=owner/repo
python run_literature_scan.py
```

### Options

- `--config`: Path to configuration file (default: `config.yaml`)
- `--dry-run`: Run without creating GitHub issues
- `--min-score`: Minimum relevance score (overrides config)
- `--max-issues`: Maximum number of issues to create per run

### Automated Execution via GitHub Actions

The workflow `.github/workflows/literature-monitor.yml` runs automatically:

- **Schedule**: Every Monday at 9:00 UTC (configurable)
- **Manual Trigger**: Via GitHub Actions UI with custom parameters
  - Dry run mode
  - Custom relevance threshold
  - Maximum issues limit

#### Manual Workflow Trigger

1. Go to repository Actions tab
2. Select "Literature Knowledge Base Monitor"
3. Click "Run workflow"
4. Configure options:
   - Enable dry-run mode to preview without creating issues
   - Adjust min-score threshold (0.0-1.0)
   - Set max-issues limit

## GitHub Integration

### Authentication

The service requires a GitHub token with `repo` scope:

- **GitHub Actions**: Uses `${{ secrets.GITHUB_TOKEN }}` automatically
- **Local execution**: Set `GITHUB_TOKEN` environment variable

### Issue Creation

For each relevant paper, the service creates a GitHub issue with:

- **Title**: `[Literature] Paper Title`
- **Label**: `literature-enhancement`
- **Body**: Includes:
  - Paper metadata (title, authors, arXiv link, PDF)
  - Abstract
  - Matched keywords and relevance score
  - Suggested next steps for evaluation

### Issue Template

A custom issue template is provided at `.github/ISSUE_TEMPLATE/literature_enhancement.md` for manual literature-based feature requests.

## Database Management

### Structure

The `papers_database.json` stores papers as:

```json
{
  "2401.12345": {
    "arxiv_id": "2401.12345",
    "title": "Paper Title",
    "authors": ["Author 1", "Author 2"],
    "abstract": "Paper abstract...",
    "published_date": "2024-01-15T00:00:00Z",
    "categories": ["nucl-th"],
    "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
    "relevance_score": 0.85,
    "keywords_matched": ["Monte Carlo", "GPU acceleration"],
    "issue_url": "https://github.com/owner/repo/issues/123"
  }
}
```

### Maintenance

The database is automatically:
- Updated on each run
- Committed back to the repository via GitHub Actions
- Used to prevent duplicate issue creation

## Customization

### Adding New Keywords

Edit `config.yaml` to add keywords:

```yaml
search_keywords:
  my_category:
    - "new keyword 1"
    - "new keyword 2"
```

### Adjusting Relevance Scoring

The relevance score is calculated in `RelevanceScorer.score_paper()`:
- Base score from keyword density
- Bonus for OpenMC-specific mentions
- Configurable threshold in `config.yaml`

### Adding Data Sources

To add new sources (e.g., Google Scholar):

1. Implement a new searcher class (like `ArXivSearcher`)
2. Add configuration in `config.yaml`
3. Update `run_literature_scan.py` to use the new source

## Development

### Requirements

```bash
pip install pyyaml
```

No additional dependencies required - uses Python standard library for HTTP requests and XML parsing.

### Testing

Test the system in dry-run mode:

```bash
# Test search and scoring without creating issues
python run_literature_scan.py --dry-run --min-score 0.5

# Test with very low threshold to see all results
python run_literature_scan.py --dry-run --min-score 0.1
```

### Debugging

The script provides verbose output:
- Number of papers found
- Relevance scores
- Matched keywords
- Issue creation status

## Example Workflow

1. **Monday 9:00 UTC**: GitHub Action triggers automatically
2. **Search Phase**: Queries arXiv for papers matching keywords
3. **Scoring Phase**: Calculates relevance scores for all papers
4. **Filtering Phase**: Selects top 5 papers above threshold
5. **Issue Creation**: Creates GitHub issues for new papers
6. **Database Update**: Commits updated database to repository
7. **Result**: New issues appear labeled `literature-enhancement`

## Benefits

- **Continuous Discovery**: Never miss relevant research
- **Time Savings**: Automated monitoring vs. manual searches
- **Traceability**: All papers tracked in database
- **Collaboration**: Issues enable team discussion
- **Knowledge Base**: Growing repository of relevant research

## Future Enhancements

Potential improvements:
- [ ] Support for additional academic databases
- [ ] ML-based relevance scoring
- [ ] Citation tracking
- [ ] Author notification
- [ ] Integration with project roadmap
- [ ] Periodic digest emails
- [ ] Paper similarity clustering

## Troubleshooting

### No papers found

- Check arXiv API availability
- Verify keywords match paper abstracts
- Reduce `min_relevance_score` threshold
- Increase `exclude_older_than_days`

### Issues not created

- Verify `GITHUB_TOKEN` has `repo` scope
- Check GitHub API rate limits
- Ensure `GITHUB_REPOSITORY` format is correct
- Look for error messages in workflow logs

### Database corruption

If `papers_database.json` becomes corrupted:
1. Backup current file
2. Reset to empty: `{}`
3. Re-run scan to rebuild

## Contributing

To contribute to the Literature Knowledge Base Service:

1. Test changes in dry-run mode
2. Ensure backwards compatibility with existing database
3. Update documentation for new features
4. Add relevant keywords for better coverage

## License

This service is part of the OpenMC project and follows the same MIT license.
