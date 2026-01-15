# Frequently Asked Questions (FAQ)

## General Questions

### Q: What is the Literature Knowledge Base Service?
**A:** An automated system that monitors academic literature (currently arXiv) for papers related to OpenMC acceleration and multiphysics simulation. It automatically scores papers for relevance and creates GitHub issues for promising research.

### Q: Why was this created?
**A:** To help the OpenMC community stay current with relevant research without manually searching papers. It saves time and ensures we don't miss potentially valuable optimization ideas.

### Q: Is this only for OpenMC core developers?
**A:** No! Anyone can use it to track research relevant to their OpenMC work. Fork the repo and customize the keywords for your specific interests.

## Setup & Configuration

### Q: How do I get started?
**A:** 
1. Read the [QUICKSTART.md](QUICKSTART.md) guide
2. Run a dry-run test: `python run_literature_scan.py --dry-run`
3. Customize keywords in `config.yaml`
4. Enable the GitHub Actions workflow

### Q: Do I need an API key?
**A:** No! arXiv's API is free and doesn't require authentication. If you add other sources (Google Scholar, etc.) in the future, they may require keys.

### Q: How do I customize the search keywords?
**A:** Edit `config.yaml` and add keywords to existing categories or create new ones:
```yaml
search_keywords:
  my_area:
    - "my keyword 1"
    - "my keyword 2"
```

### Q: Can I change how often it runs?
**A:** Yes! Edit `.github/workflows/literature-monitor.yml` and change the cron schedule:
```yaml
schedule:
  - cron: '0 9 * * 1'  # Currently Monday 9:00 UTC
```

## Usage

### Q: How do I test without creating issues?
**A:** Use the `--dry-run` flag:
```bash
python run_literature_scan.py --dry-run
```

### Q: How do I manually add a paper I found?
**A:** Use the `add_paper.py` script:
```bash
python add_paper.py --interactive
```

### Q: How do I view what's in the database?
**A:** Use the viewer script:
```bash
python view_database.py
```

### Q: Can I change the relevance threshold?
**A:** Yes, either in `config.yaml` or via command line:
```bash
python run_literature_scan.py --min-score 0.7
```

## Understanding Results

### Q: What do the relevance scores mean?
**A:** Scores range from 0.0 to 1.0:
- **0.8-1.0**: Highly relevant (mentions OpenMC specifically)
- **0.6-0.8**: Relevant (several matching keywords)
- **0.4-0.6**: Possibly relevant (few matching keywords)
- **0.0-0.4**: Low relevance

### Q: Why did a paper get a low score?
**A:** Common reasons:
- Keywords don't appear in title or abstract
- Paper is tangentially related but not directly applicable
- You may need to add more specific keywords for that topic

### Q: Can I adjust the scoring algorithm?
**A:** Yes! Edit `RelevanceScorer.score_paper()` in `literature_monitor.py`. The algorithm is simple and documented.

### Q: How many papers does it track?
**A:** It searches up to 50 papers per keyword query by default. You can increase this in `config.yaml`:
```yaml
data_sources:
  arxiv:
    max_results: 100  # Increase from 50
```

## GitHub Integration

### Q: Why aren't issues being created?
**A:** Check:
1. `GITHUB_TOKEN` environment variable is set
2. Token has `repo` scope permissions
3. `GITHUB_REPOSITORY` is in `owner/repo` format
4. You're not in `--dry-run` mode

### Q: Can I customize the issue format?
**A:** Yes! Edit `format_issue_body()` and `format_issue_title()` in `literature_monitor.py`.

### Q: Can I change the issue label?
**A:** Yes! Edit `config.yaml`:
```yaml
github:
  issue_label: "my-custom-label"
```

### Q: How do I avoid duplicate issues?
**A:** The system automatically tracks created issues in the database and won't create duplicates for the same arXiv ID.

## Database

### Q: Where is the database stored?
**A:** `tools/knowledge_base/papers_database.json`

### Q: What format is it?
**A:** JSON format with one entry per paper, indexed by arXiv ID.

### Q: Can I edit the database manually?
**A:** Yes, but be careful with JSON syntax. It's safer to use the provided scripts.

### Q: What if the database gets corrupted?
**A:** Backup your current file, then reset to `{}` and re-run the scan.

### Q: Is the database version controlled?
**A:** Yes! The GitHub Actions workflow automatically commits database updates.

## Troubleshooting

### Q: I get "No papers found" - why?
**A:** Possible reasons:
1. No internet connection (if running locally)
2. arXiv API is down (rare)
3. No papers match your keywords in the time window
4. Relevance threshold is too high

Try:
- Reduce `min_relevance_score` to 0.3
- Increase `exclude_older_than_days` to 730
- Add broader keywords

### Q: The script is slow - normal?
**A:** Yes. It makes multiple API calls (one per keyword × category). Each call can take 5-10 seconds. With 21 keywords and 2 categories, expect 3-5 minutes total.

### Q: Can I speed it up?
**A:** Yes:
- Reduce number of keywords
- Reduce `max_results` per query
- Remove categories you don't need
- (Future) Implement parallel queries

### Q: I get HTTP errors - what to do?
**A:** 
- Check internet connection
- Verify arXiv API is up: http://export.arxiv.org/api/query
- Try again in a few minutes (might be temporary)

## Advanced Usage

### Q: Can I add other data sources besides arXiv?
**A:** Yes! Implement a new searcher class (like `ArXivSearcher`) and integrate it into the main script. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Q: Can I use machine learning for scoring?
**A:** Yes! Replace the `RelevanceScorer` algorithm with your ML model. The interface is simple - just return a score between 0 and 1.

### Q: Can I integrate this with other tools?
**A:** Yes! The Python API is documented and can be imported:
```python
from knowledge_base import PaperDatabase, ArXivSearcher
```

### Q: Can I use this for other projects?
**A:** Yes! The code is MIT licensed. Customize the keywords and GitHub settings for your project.

### Q: How do I contribute improvements?
**A:** See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. We welcome:
- New data sources
- Better scoring algorithms
- UI improvements
- Documentation enhancements

## Performance

### Q: How much disk space does it use?
**A:** Minimal. Each paper is ~2-3 KB in JSON. Even 1000 papers is only ~3 MB.

### Q: Does it use a lot of API calls?
**A:** Moderate. With default settings: 21 keywords × 2 categories = 42 API calls per run. arXiv has no strict rate limits for reasonable usage.

### Q: Can it handle thousands of papers?
**A:** Yes, but viewing might get slow. The JSON format scales to ~10,000 papers easily. For more, consider moving to SQLite or PostgreSQL.

## Privacy & Security

### Q: Does it store sensitive data?
**A:** No. Only public metadata from arXiv (titles, authors, abstracts, IDs).

### Q: What about the GitHub token?
**A:** Store it as a GitHub secret, not in code. The workflow uses `${{ secrets.GITHUB_TOKEN }}` automatically.

### Q: Can others see my database?
**A:** If your repository is public, yes. The database only contains public arXiv metadata though.

## Getting Help

### Q: Where can I get help?
**A:** 
1. Check this FAQ
2. Read [README.md](README.md) and [QUICKSTART.md](QUICKSTART.md)
3. Run the example: `python example_usage.py`
4. Create a GitHub issue with the `question` label
5. Ask on the OpenMC discussion forum

### Q: How do I report bugs?
**A:** Create a GitHub issue with:
- Description of the problem
- Steps to reproduce
- Error messages
- Your configuration (with secrets removed)

### Q: Can I request features?
**A:** Yes! Create a GitHub issue with:
- Feature description
- Use case / motivation
- Expected behavior

## Miscellaneous

### Q: Why only arXiv?
**A:** It's free, has an open API, and covers most relevant physics/computing papers. Other sources can be added.

### Q: What about papers not on arXiv?
**A:** Use `add_paper.py` to manually add papers from any source.

### Q: Can I turn off automatic runs?
**A:** Yes. Just don't enable the GitHub Actions workflow, or comment out the schedule trigger.

### Q: Is there a web interface?
**A:** Not yet, but it's on the roadmap! For now, use `view_database.py` for CLI viewing.

### Q: How often is it updated?
**A:** The system runs weekly by default. The code is updated as needed.

---

**Have a question not listed here?** Open a GitHub issue with the `question` label!
