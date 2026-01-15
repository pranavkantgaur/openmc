#!/usr/bin/env python3
"""
Literature Knowledge Base Dashboard

Simple command-line viewer for the papers database.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_base.literature_monitor import PaperDatabase


def format_date(date_str):
    """Format ISO date string to readable format."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except:
        return date_str


def display_summary(db):
    """Display database summary statistics."""
    print("\n" + "="*80)
    print("LITERATURE KNOWLEDGE BASE - DASHBOARD")
    print("="*80)
    
    total = len(db.papers)
    with_issues = sum(1 for p in db.papers.values() if p.issue_url)
    high_score = sum(1 for p in db.papers.values() if p.relevance_score >= 0.7)
    medium_score = sum(1 for p in db.papers.values() if 0.5 <= p.relevance_score < 0.7)
    low_score = sum(1 for p in db.papers.values() if p.relevance_score < 0.5)
    
    print(f"\n📊 STATISTICS")
    print(f"  Total Papers:          {total}")
    print(f"  GitHub Issues Created: {with_issues}")
    print(f"  High Relevance (≥0.7): {high_score}")
    print(f"  Med Relevance (0.5-0.7): {medium_score}")
    print(f"  Low Relevance (<0.5):  {low_score}")


def display_papers(db, sort_by='score', limit=None):
    """Display papers in the database."""
    papers = list(db.papers.values())
    
    # Sort papers
    if sort_by == 'score':
        papers.sort(key=lambda p: p.relevance_score, reverse=True)
    elif sort_by == 'date':
        papers.sort(key=lambda p: p.published_date, reverse=True)
    elif sort_by == 'title':
        papers.sort(key=lambda p: p.title.lower())
    
    if limit:
        papers = papers[:limit]
    
    print(f"\n📚 PAPERS (sorted by {sort_by})")
    print("-"*80)
    
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}" + (" et al." if len(paper.authors) > 3 else ""))
        print(f"   arXiv: {paper.arxiv_id} | Published: {format_date(paper.published_date)}")
        print(f"   Score: {paper.relevance_score:.2f} | Keywords: {', '.join(paper.keywords_matched[:5])}")
        if paper.issue_url:
            print(f"   Issue: {paper.issue_url}")
        print(f"   PDF: {paper.pdf_url}")


def display_top_keywords(db):
    """Display most frequently matched keywords."""
    from collections import Counter
    
    all_keywords = []
    for paper in db.papers.values():
        all_keywords.extend(paper.keywords_matched)
    
    if not all_keywords:
        return
    
    counter = Counter(all_keywords)
    top = counter.most_common(10)
    
    print(f"\n🔑 TOP KEYWORDS")
    print("-"*80)
    for keyword, count in top:
        print(f"  {keyword:40s} {count:3d} papers")


def display_categories(db):
    """Display paper distribution by category."""
    from collections import Counter
    
    all_categories = []
    for paper in db.papers.values():
        all_categories.extend(paper.categories)
    
    if not all_categories:
        return
    
    counter = Counter(all_categories)
    
    print(f"\n📂 CATEGORIES")
    print("-"*80)
    for category, count in sorted(counter.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category:30s} {count:3d} papers")


def display_detailed_paper(db, arxiv_id):
    """Display detailed information about a specific paper."""
    paper = db.get_paper(arxiv_id)
    
    if not paper:
        print(f"\nError: Paper {arxiv_id} not found in database")
        return
    
    print("\n" + "="*80)
    print("PAPER DETAILS")
    print("="*80)
    
    print(f"\nTitle: {paper.title}")
    print(f"\nAuthors: {', '.join(paper.authors)}")
    print(f"\narXiv ID: {paper.arxiv_id}")
    print(f"Published: {format_date(paper.published_date)}")
    print(f"Categories: {', '.join(paper.categories)}")
    print(f"\nRelevance Score: {paper.relevance_score:.2f}")
    print(f"Matched Keywords: {', '.join(paper.keywords_matched) if paper.keywords_matched else 'None'}")
    
    if paper.issue_url:
        print(f"\nGitHub Issue: {paper.issue_url}")
    else:
        print(f"\nGitHub Issue: Not created")
    
    print(f"\nPDF: {paper.pdf_url}")
    print(f"arXiv Link: https://arxiv.org/abs/{paper.arxiv_id}")
    
    print(f"\nAbstract:")
    print("-"*80)
    print(paper.abstract)
    print("-"*80)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='View the Literature Knowledge Base'
    )
    parser.add_argument(
        '--db',
        type=Path,
        default=Path(__file__).parent / 'papers_database.json',
        help='Path to database file'
    )
    parser.add_argument(
        '--sort',
        choices=['score', 'date', 'title'],
        default='score',
        help='Sort papers by score, date, or title'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of papers shown'
    )
    parser.add_argument(
        '--paper',
        type=str,
        help='Show details for specific paper by arXiv ID'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Show only summary statistics'
    )
    
    args = parser.parse_args()
    
    # Load database
    if not args.db.exists():
        print(f"Error: Database not found at {args.db}")
        print("Run a literature scan first to populate the database.")
        sys.exit(1)
    
    db = PaperDatabase(args.db)
    
    if len(db.papers) == 0:
        print("\n📭 Database is empty")
        print("Run a literature scan to populate it:")
        print("  python run_literature_scan.py --dry-run")
        return
    
    # Show specific paper
    if args.paper:
        display_detailed_paper(db, args.paper)
        return
    
    # Show summary
    display_summary(db)
    
    if not args.stats_only:
        display_papers(db, sort_by=args.sort, limit=args.limit)
        display_top_keywords(db)
        display_categories(db)
    
    print("\n" + "="*80)
    print("\nTip: Use --paper ARXIV_ID to see detailed information")
    print("     Use --sort date|title|score to change sorting")
    print("     Use --limit N to show only N papers")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
