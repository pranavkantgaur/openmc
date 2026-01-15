#!/usr/bin/env python3
"""
Manual Paper Submission Tool

Use this script to manually add papers you've found to the knowledge base
and optionally create GitHub issues for them.
"""

import argparse
import os
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
from knowledge_base.run_literature_scan import create_github_issue, load_config


def interactive_paper_entry():
    """Interactively collect paper information from user."""
    print("\n" + "="*60)
    print("Manual Paper Submission")
    print("="*60)
    print("\nPlease enter the paper details:\n")
    
    arxiv_id = input("arXiv ID (e.g., 2401.12345): ").strip()
    if not arxiv_id:
        print("Error: arXiv ID is required")
        return None
    
    title = input("Title: ").strip()
    if not title:
        print("Error: Title is required")
        return None
    
    authors_str = input("Authors (comma-separated): ").strip()
    authors = [a.strip() for a in authors_str.split(',')] if authors_str else ["Unknown"]
    
    abstract = input("Abstract (press Enter twice when done):\n")
    lines = [abstract]
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    abstract = ' '.join(lines).strip()
    
    if not abstract:
        abstract = "No abstract provided."
    
    categories_str = input("Categories (comma-separated, e.g., nucl-th,physics.comp-ph): ").strip()
    categories = [c.strip() for c in categories_str.split(',')] if categories_str else ["unknown"]
    
    # Get date or use today
    from datetime import datetime
    published_date = input(f"Published date (YYYY-MM-DD, default=today): ").strip()
    if not published_date:
        published_date = datetime.now().isoformat() + 'Z'
    else:
        published_date = published_date + 'T00:00:00Z'
    
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    return Paper(
        arxiv_id=arxiv_id,
        title=title,
        authors=authors,
        abstract=abstract,
        published_date=published_date,
        categories=categories,
        pdf_url=pdf_url
    )


def main():
    parser = argparse.ArgumentParser(
        description='Manually add papers to the Literature Knowledge Base'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Interactive mode: enter paper details via prompts'
    )
    parser.add_argument(
        '--arxiv-id',
        type=str,
        help='arXiv ID of the paper'
    )
    parser.add_argument(
        '--title',
        type=str,
        help='Paper title'
    )
    parser.add_argument(
        '--authors',
        type=str,
        help='Authors (comma-separated)'
    )
    parser.add_argument(
        '--abstract',
        type=str,
        help='Paper abstract'
    )
    parser.add_argument(
        '--categories',
        type=str,
        default='nucl-th',
        help='arXiv categories (comma-separated)'
    )
    parser.add_argument(
        '--create-issue',
        action='store_true',
        help='Create a GitHub issue for this paper'
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=Path(__file__).parent / 'config.yaml',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    # Get paper details
    if args.interactive:
        paper = interactive_paper_entry()
        if not paper:
            sys.exit(1)
    else:
        # Validate required arguments
        if not args.arxiv_id or not args.title:
            print("Error: --arxiv-id and --title are required (or use --interactive)")
            sys.exit(1)
        
        authors = [a.strip() for a in args.authors.split(',')] if args.authors else ["Unknown"]
        categories = [c.strip() for c in args.categories.split(',')]
        
        from datetime import datetime
        paper = Paper(
            arxiv_id=args.arxiv_id,
            title=args.title,
            authors=authors,
            abstract=args.abstract or "No abstract provided.",
            published_date=datetime.now().isoformat() + 'Z',
            categories=categories,
            pdf_url=f"https://arxiv.org/pdf/{args.arxiv_id}.pdf"
        )
    
    # Load configuration and database
    config = load_config(args.config)
    db_path = Path(__file__).parent.parent.parent / config['database']['path']
    db = PaperDatabase(db_path)
    
    # Score the paper
    scorer = RelevanceScorer(config['search_keywords'])
    score = scorer.score_paper(paper)
    
    print("\n" + "="*60)
    print("Paper Summary")
    print("="*60)
    print(f"Title: {paper.title}")
    print(f"Authors: {', '.join(paper.authors)}")
    print(f"arXiv ID: {paper.arxiv_id}")
    print(f"Relevance Score: {score:.2f}")
    print(f"Matched Keywords: {', '.join(paper.keywords_matched) if paper.keywords_matched else 'None'}")
    print("="*60)
    
    # Check if already exists
    existing = db.get_paper(paper.arxiv_id)
    if existing:
        print(f"\n⚠️  Paper already in database!")
        if existing.issue_url:
            print(f"   Issue: {existing.issue_url}")
        else:
            print(f"   No issue created yet")
        
        response = input("\nOverwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return
    
    # Add to database
    db.add_paper(paper)
    db.save()
    print(f"\n✓ Added to database: {db_path}")
    
    # Create issue if requested
    if args.create_issue:
        github_token = os.environ.get('GITHUB_TOKEN')
        github_repo = os.environ.get('GITHUB_REPOSITORY')
        
        if not github_token or not github_repo:
            print("\nError: Cannot create issue")
            print("Required environment variables:")
            print("  GITHUB_TOKEN: GitHub personal access token")
            print("  GITHUB_REPOSITORY: Repository in owner/repo format")
            sys.exit(1)
        
        print("\nCreating GitHub issue...")
        try:
            title = format_issue_title(paper)
            body = format_issue_body(paper)
            label = config['github']['issue_label']
            
            issue_url = create_github_issue(
                title=title,
                body=body,
                label=label,
                token=github_token,
                repo=github_repo
            )
            
            db.mark_issue_created(paper.arxiv_id, issue_url)
            db.save()
            
            print(f"✓ Issue created: {issue_url}")
        
        except Exception as e:
            print(f"✗ Failed to create issue: {e}")
            sys.exit(1)
    else:
        print("\nTo create a GitHub issue later, run:")
        print(f"  python add_paper.py --arxiv-id {paper.arxiv_id} --create-issue")


if __name__ == '__main__':
    main()
