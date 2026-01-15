# Architecture Overview

## System Components

```
┌────────────────────────────────────────────────────────────────────────┐
│                    Literature Knowledge Base Service                    │
└────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │   arXiv API  │    │ Google Scholar│    │  IEEE Xplore │             │
│  │   (Active)   │    │   (Planned)   │    │   (Planned)  │             │
│  └──────┬───────┘    └──────────────┘    └──────────────┘             │
│         │                                                                │
└─────────┼────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           CORE PROCESSING                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────┐         ┌────────────────────┐                 │
│  │  ArXivSearcher     │         │  RelevanceScorer   │                 │
│  ├────────────────────┤         ├────────────────────┤                 │
│  │ - Query API        │────────▶│ - Keyword matching │                 │
│  │ - Parse XML        │         │ - Score calculation│                 │
│  │ - Filter by date   │         │ - Threshold filter │                 │
│  │ - Extract metadata │         └────────┬───────────┘                 │
│  └────────────────────┘                  │                              │
│                                           ▼                              │
│                              ┌────────────────────┐                     │
│                              │   PaperDatabase    │                     │
│                              ├────────────────────┤                     │
│                              │ - Store papers     │                     │
│                              │ - Check duplicates │                     │
│                              │ - Track issues     │                     │
│                              │ - JSON persistence │                     │
│                              └────────┬───────────┘                     │
│                                       │                                  │
└───────────────────────────────────────┼──────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              OUTPUT                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────┐         ┌────────────────────┐                 │
│  │  GitHub Issues     │         │  Database (JSON)   │                 │
│  ├────────────────────┤         ├────────────────────┤                 │
│  │ - Auto-created     │         │ - papers_database  │                 │
│  │ - Label applied    │         │ - Searchable       │                 │
│  │ - Formatted body   │         │ - Version tracked  │                 │
│  │ - Linked to paper  │         │ - Git committed    │                 │
│  └────────────────────┘         └────────────────────┘                 │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Execution Modes

### 1. Automated (GitHub Actions)

```
┌──────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                    │
│                (literature-monitor.yml)                       │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  Trigger: Schedule (cron) or Manual                          │
│           └─ Weekly: Monday 9:00 UTC                         │
│           └─ Manual: workflow_dispatch                       │
│                                                                │
│  Steps:                                                       │
│  1. Checkout repository                                       │
│  2. Setup Python 3.11                                         │
│  3. Install dependencies (pyyaml)                            │
│  4. Run literature scan                                       │
│     └─ GITHUB_TOKEN (automatic)                              │
│     └─ GITHUB_REPOSITORY (automatic)                         │
│  5. Commit database updates                                   │
│     └─ Add papers_database.json                              │
│     └─ Push to repository                                    │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

### 2. Manual (Local)

```
┌──────────────────────────────────────────────────────────────┐
│                    Local Execution                            │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  Option A: Automated Scan                                     │
│  $ python run_literature_scan.py [options]                   │
│    ├─ --dry-run: Test without creating issues               │
│    ├─ --min-score: Custom threshold                         │
│    └─ --max-issues: Limit issues                            │
│                                                                │
│  Option B: Manual Paper Entry                                │
│  $ python add_paper.py [options]                             │
│    ├─ --interactive: Guided input                           │
│    ├─ --arxiv-id: Direct entry                              │
│    └─ --create-issue: Create GitHub issue                   │
│                                                                │
│  Option C: View Database                                      │
│  $ python view_database.py [options]                         │
│    ├─ --sort: Sort by score/date/title                      │
│    ├─ --limit: Limit results                                │
│    └─ --paper: View specific paper                          │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Input: Search Keywords (config.yaml)
  │
  ├─ Primary: ["Monte Carlo", "OpenMC", ...]
  ├─ Acceleration: ["GPU", "variance reduction", ...]
  └─ Multiphysics: ["coupling", "thermal hydraulics", ...]
  │
  ▼
Query arXiv API
  │
  ├─ Categories: nucl-th, physics.comp-ph
  ├─ Time window: Last 365 days
  └─ Max results: 50 per query
  │
  ▼
Parse & Extract
  │
  ├─ Title, Authors, Abstract
  ├─ arXiv ID, Categories
  └─ Publication Date, PDF URL
  │
  ▼
Score Relevance
  │
  ├─ Keyword density (base score)
  ├─ OpenMC mention (bonus)
  └─ Multiple keywords (bonus)
  │
  ▼
Filter (score >= threshold)
  │
  ├─ Default: 0.6
  └─ Configurable via CLI or config
  │
  ▼
Check Database
  │
  ├─ New paper? → Continue
  └─ Duplicate? → Skip
  │
  ▼
Store in Database
  │
  ├─ Add paper metadata
  ├─ Store relevance score
  └─ Track matched keywords
  │
  ▼
Create GitHub Issue (if not dry-run)
  │
  ├─ Format title: [Literature] Paper Title
  ├─ Format body: Metadata + Abstract + Score
  ├─ Apply label: literature-enhancement
  └─ Link issue URL in database
  │
  ▼
Output: Database + GitHub Issues
```

## Relevance Scoring Algorithm

```python
def score_paper(paper):
    score = 0.0
    matches = []
    
    # 1. Count keyword matches
    for keyword in all_keywords:
        if keyword in (title + abstract).lower():
            matches.append(keyword)
    
    # 2. Base score from keyword density
    score = min(len(matches) / 10.0, 1.0)
    
    # 3. Bonus for OpenMC mention
    if 'openmc' in text:
        score = min(score + 0.3, 1.0)
    
    # 4. Store results
    paper.relevance_score = score
    paper.keywords_matched = matches
    
    return score
```

Score Interpretation:
- **0.8-1.0**: Highly relevant (OpenMC-specific)
- **0.6-0.8**: Relevant (multiple keywords)
- **0.4-0.6**: Possibly relevant (few keywords)
- **0.0-0.4**: Low relevance

## Configuration Structure

```yaml
config.yaml
├── search_keywords
│   ├── primary: [...]
│   ├── acceleration_techniques: [...]
│   └── multiphysics: [...]
├── data_sources
│   └── arxiv
│       ├── enabled: true
│       ├── categories: [...]
│       └── max_results: 50
├── github
│   ├── issue_label: "literature-enhancement"
│   └── issue_template: "literature_feature_request"
├── database
│   └── path: "papers_database.json"
└── filters
    ├── min_relevance_score: 0.6
    └── exclude_older_than_days: 365
```

## Database Schema

```json
{
  "arxiv_id": {
    "arxiv_id": "2401.12345",
    "title": "Paper Title",
    "authors": ["Author1", "Author2"],
    "abstract": "Paper abstract...",
    "published_date": "2024-01-15T00:00:00Z",
    "categories": ["nucl-th"],
    "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
    "relevance_score": 0.85,
    "keywords_matched": ["keyword1", "keyword2"],
    "issue_url": "https://github.com/owner/repo/issues/123"
  }
}
```

## Error Handling

```
Network Error → Log error, continue with next query
Parse Error → Skip paper, continue
API Rate Limit → Wait and retry (not implemented yet)
GitHub API Error → Log error, paper still added to database
Database Corruption → Backup and reset to empty {}
```

## Future Enhancements

1. **Additional Sources**: Google Scholar, IEEE, PubMed
2. **ML Scoring**: Use machine learning for better relevance
3. **Citation Tracking**: Monitor paper citations over time
4. **Full-text Analysis**: PDF parsing for deeper insights
5. **Notification System**: Email/Slack digests
6. **Web Dashboard**: Browser-based interface
7. **Collaborative Filtering**: Team voting on relevance
