#!/usr/bin/env python3
"""
Example: Using the Literature Knowledge Base Service

This example demonstrates how to use the service programmatically.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_base.literature_monitor import (
    Paper,
    PaperDatabase,
    RelevanceScorer,
    format_issue_body,
    format_issue_title
)


def example_manual_paper_entry():
    """Example: Manually add a paper you found to the knowledge base."""
    print("Example 1: Adding a paper manually")
    print("-" * 60)
    
    # Create a paper object for a paper you found
    paper = Paper(
        arxiv_id="2310.12345",  # arXiv ID
        title="Novel Variance Reduction Techniques for OpenMC",
        authors=["Research Team"],
        abstract="This paper proposes new variance reduction methods...",
        published_date="2023-10-15T00:00:00Z",
        categories=["nucl-th"],
        pdf_url="https://arxiv.org/pdf/2310.12345.pdf"
    )
    
    # Load database
    db_path = Path(__file__).parent / "papers_database.json"
    db = PaperDatabase(db_path)
    
    # Add paper
    if db.add_paper(paper):
        print(f"✓ Added new paper: {paper.title}")
        db.save()
    else:
        print(f"Paper already in database: {paper.title}")
    
    print()


def example_scoring():
    """Example: Score papers for relevance."""
    print("Example 2: Scoring papers for relevance")
    print("-" * 60)
    
    # Define your keywords
    keywords_config = {
        'primary': ['Monte Carlo', 'neutron transport', 'OpenMC'],
        'acceleration': ['GPU', 'parallel', 'variance reduction']
    }
    
    scorer = RelevanceScorer(keywords_config)
    
    # Create sample papers
    papers = [
        Paper(
            arxiv_id="test1",
            title="GPU Acceleration for OpenMC Monte Carlo Simulations",
            authors=["Author A"],
            abstract="We present GPU techniques for OpenMC neutron transport with variance reduction.",
            published_date="2024-01-01T00:00:00Z",
            categories=["nucl-th"],
            pdf_url="https://example.com/test1.pdf"
        ),
        Paper(
            arxiv_id="test2",
            title="Machine Learning for Reactor Design",
            authors=["Author B"],
            abstract="Machine learning methods for reactor optimization.",
            published_date="2024-01-01T00:00:00Z",
            categories=["cs.LG"],
            pdf_url="https://example.com/test2.pdf"
        ),
    ]
    
    # Score each paper
    for paper in papers:
        score = scorer.score_paper(paper)
        print(f"Paper: {paper.title}")
        print(f"  Score: {score:.2f}")
        print(f"  Matched keywords: {', '.join(paper.keywords_matched)}")
        print()


def example_issue_preview():
    """Example: Preview what a GitHub issue would look like."""
    print("Example 3: Preview GitHub issue format")
    print("-" * 60)
    
    paper = Paper(
        arxiv_id="2401.54321",
        title="Advanced Domain Decomposition for Parallel Monte Carlo",
        authors=["Jane Researcher", "John Scientist"],
        abstract="We propose a novel domain decomposition method for parallel Monte Carlo simulations...",
        published_date="2024-01-20T00:00:00Z",
        categories=["physics.comp-ph"],
        pdf_url="https://arxiv.org/pdf/2401.54321.pdf",
        relevance_score=0.82,
        keywords_matched=["parallel", "Monte Carlo", "domain decomposition"]
    )
    
    title = format_issue_title(paper)
    body = format_issue_body(paper)
    
    print(f"Issue Title:\n  {title}\n")
    print(f"Issue Body Preview (first 500 chars):")
    print("-" * 60)
    print(body[:500] + "...")
    print()


def example_database_query():
    """Example: Query the database for papers."""
    print("Example 4: Querying the database")
    print("-" * 60)
    
    db_path = Path(__file__).parent / "papers_database.json"
    db = PaperDatabase(db_path)
    
    print(f"Total papers in database: {len(db.papers)}")
    
    # Find papers with issues created
    papers_with_issues = [
        (id, paper) for id, paper in db.papers.items()
        if paper.issue_url is not None
    ]
    print(f"Papers with GitHub issues: {len(papers_with_issues)}")
    
    # Find high-scoring papers
    high_score_papers = [
        (id, paper) for id, paper in db.papers.items()
        if paper.relevance_score > 0.7
    ]
    print(f"Papers with score > 0.7: {len(high_score_papers)}")
    
    if high_score_papers:
        print("\nTop papers:")
        for id, paper in sorted(high_score_papers, 
                               key=lambda x: x[1].relevance_score, 
                               reverse=True)[:3]:
            print(f"  - {paper.title} (score: {paper.relevance_score:.2f})")
    
    print()


def main():
    """Run all examples."""
    print("=" * 60)
    print("OpenMC Literature Knowledge Base - Usage Examples")
    print("=" * 60)
    print()
    
    example_manual_paper_entry()
    example_scoring()
    example_issue_preview()
    example_database_query()
    
    print("=" * 60)
    print("✓ Examples completed")
    print("=" * 60)
    print("\nFor automated scanning, use: python run_literature_scan.py --dry-run")


if __name__ == '__main__':
    main()
