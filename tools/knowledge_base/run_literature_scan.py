#!/usr/bin/env python3
"""
Main script for OpenMC Literature Knowledge Base Service

This script:
1. Searches academic databases for relevant papers
2. Scores papers based on relevance to OpenMC acceleration
3. Creates GitHub issues for promising papers
4. Maintains a database of tracked papers
"""

import argparse
import os
import sys
from pathlib import Path
import yaml

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_base.literature_monitor import (
    PaperDatabase,
    ArXivSearcher,
    RelevanceScorer,
    format_issue_body,
    format_issue_title
)


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def create_github_issue(title: str, body: str, label: str, token: str, repo: str) -> str:
    """
    Create a GitHub issue using the GitHub API.
    
    Args:
        title: Issue title
        body: Issue body (markdown)
        label: Label to apply to issue
        token: GitHub API token
        repo: Repository in format 'owner/repo'
        
    Returns:
        URL of created issue
    """
    import json
    import urllib.request
    
    url = f"https://api.github.com/repos/{repo}/issues"
    
    data = {
        'title': title,
        'body': body,
        'labels': [label]
    }
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['html_url']
    except urllib.error.HTTPError as e:
        print(f"Error creating GitHub issue: {e}")
        print(f"Response: {e.read().decode('utf-8')}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description='OpenMC Literature Knowledge Base Service'
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=Path(__file__).parent / 'config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without creating GitHub issues'
    )
    parser.add_argument(
        '--min-score',
        type=float,
        help='Minimum relevance score (overrides config)'
    )
    parser.add_argument(
        '--max-issues',
        type=int,
        default=5,
        help='Maximum number of issues to create in one run'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    print("Loading configuration...")
    config = load_config(args.config)
    
    # Get GitHub configuration
    github_token = os.environ.get('GITHUB_TOKEN')
    github_repo = os.environ.get('GITHUB_REPOSITORY')
    
    if not args.dry_run:
        if not github_token:
            print("Error: GITHUB_TOKEN environment variable not set")
            print("Set it to a GitHub personal access token with 'repo' scope")
            sys.exit(1)
        if not github_repo:
            print("Error: GITHUB_REPOSITORY environment variable not set")
            print("Set it to 'owner/repo' format")
            sys.exit(1)
    
    # Initialize database
    db_path = Path(__file__).parent.parent.parent / config['database']['path']
    db = PaperDatabase(db_path)
    print(f"Loaded database with {len(db.papers)} papers")
    
    # Initialize searcher and scorer
    arxiv_config = config['data_sources']['arxiv']
    if not arxiv_config['enabled']:
        print("arXiv search is disabled in configuration")
        return
    
    searcher = ArXivSearcher(
        categories=arxiv_config['categories'],
        max_results=arxiv_config['max_results']
    )
    
    scorer = RelevanceScorer(config['search_keywords'])
    
    # Collect all keywords for searching
    all_keywords = []
    for category_keywords in config['search_keywords'].values():
        if isinstance(category_keywords, list):
            all_keywords.extend(category_keywords)
    
    # Search for papers
    print(f"Searching arXiv with {len(all_keywords)} keywords...")
    papers = searcher.search(
        keywords=all_keywords,
        exclude_older_than_days=config['filters']['exclude_older_than_days']
    )
    print(f"Found {len(papers)} papers")
    
    # Score papers and filter
    min_score = args.min_score if args.min_score is not None else config['filters']['min_relevance_score']
    relevant_papers = []
    
    for paper in papers:
        score = scorer.score_paper(paper)
        if score >= min_score:
            relevant_papers.append(paper)
    
    print(f"Found {len(relevant_papers)} papers with relevance score >= {min_score}")
    
    # Sort by relevance score
    relevant_papers.sort(key=lambda p: p.relevance_score, reverse=True)
    
    # Filter out papers already in database
    new_papers = [p for p in relevant_papers if not db.get_paper(p.arxiv_id)]
    print(f"Found {len(new_papers)} new papers not in database")
    
    # Create issues for top papers
    issues_created = 0
    label = config['github']['issue_label']
    
    for paper in new_papers[:args.max_issues]:
        print(f"\nPaper: {paper.title}")
        print(f"  Score: {paper.relevance_score:.2f}")
        print(f"  Keywords: {', '.join(paper.keywords_matched)}")
        
        # Add to database
        db.add_paper(paper)
        
        if not args.dry_run:
            try:
                title = format_issue_title(paper)
                body = format_issue_body(paper)
                
                print(f"  Creating GitHub issue...")
                issue_url = create_github_issue(
                    title=title,
                    body=body,
                    label=label,
                    token=github_token,
                    repo=github_repo
                )
                
                # Update database with issue URL
                db.mark_issue_created(paper.arxiv_id, issue_url)
                
                print(f"  ✓ Created: {issue_url}")
                issues_created += 1
            except Exception as e:
                print(f"  ✗ Failed to create issue: {e}")
        else:
            print(f"  [DRY RUN] Would create issue")
            issues_created += 1
    
    # Save database
    db.save()
    print(f"\n✓ Database saved to {db_path}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Papers searched: {len(papers)}")
    print(f"  Relevant papers: {len(relevant_papers)}")
    print(f"  New papers: {len(new_papers)}")
    print(f"  Issues created: {issues_created}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
