#!/usr/bin/env python3
"""
Test script for Literature Knowledge Base Service

This script tests the core functionality with mock data
since the sandbox environment doesn't have internet access.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_base.literature_monitor import (
    Paper,
    PaperDatabase,
    RelevanceScorer,
    format_issue_body,
    format_issue_title
)


def test_paper_creation():
    """Test Paper dataclass creation and serialization."""
    print("Testing Paper creation...")
    
    paper = Paper(
        arxiv_id="2401.12345",
        title="GPU-Accelerated Monte Carlo Methods for Nuclear Reactor Simulation",
        authors=["John Doe", "Jane Smith"],
        abstract="We present a novel GPU acceleration technique for Monte Carlo particle transport simulations in OpenMC.",
        published_date="2024-01-15T00:00:00Z",
        categories=["nucl-th", "physics.comp-ph"],
        pdf_url="https://arxiv.org/pdf/2401.12345.pdf",
        relevance_score=0.85,
        keywords_matched=["OpenMC", "GPU acceleration", "Monte Carlo"]
    )
    
    # Test serialization
    data = paper.to_dict()
    assert data['arxiv_id'] == "2401.12345"
    assert len(data['authors']) == 2
    
    # Test deserialization
    paper2 = Paper.from_dict(data)
    assert paper2.arxiv_id == paper.arxiv_id
    
    print("  ✓ Paper creation and serialization works")


def test_database_operations():
    """Test PaperDatabase operations."""
    print("Testing Database operations...")
    
    # Create temporary database
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        db_path = Path(f.name)
        f.write('{}')
    
    try:
        db = PaperDatabase(db_path)
        assert len(db.papers) == 0
        
        # Add a paper
        paper = Paper(
            arxiv_id="2401.12345",
            title="Test Paper",
            authors=["Author"],
            abstract="Abstract",
            published_date="2024-01-15T00:00:00Z",
            categories=["nucl-th"],
            pdf_url="https://arxiv.org/pdf/2401.12345.pdf"
        )
        
        is_new = db.add_paper(paper)
        assert is_new == True
        assert len(db.papers) == 1
        
        # Try to add duplicate
        is_new = db.add_paper(paper)
        assert is_new == False
        assert len(db.papers) == 1
        
        # Save and reload
        db.save()
        db2 = PaperDatabase(db_path)
        assert len(db2.papers) == 1
        assert db2.get_paper("2401.12345") is not None
        
        # Mark issue created
        db2.mark_issue_created("2401.12345", "https://github.com/owner/repo/issues/1")
        assert db2.get_paper("2401.12345").issue_url == "https://github.com/owner/repo/issues/1"
        
        print("  ✓ Database operations work correctly")
    
    finally:
        # Cleanup
        if db_path.exists():
            os.unlink(db_path)


def test_relevance_scorer():
    """Test relevance scoring algorithm."""
    print("Testing RelevanceScorer...")
    
    config = {
        'primary': ['Monte Carlo', 'OpenMC'],
        'acceleration': ['GPU acceleration', 'variance reduction']
    }
    
    scorer = RelevanceScorer(config)
    
    # High relevance paper
    paper1 = Paper(
        arxiv_id="test1",
        title="OpenMC GPU Acceleration Study",
        authors=["Author"],
        abstract="This paper presents GPU acceleration methods for OpenMC Monte Carlo simulations with variance reduction.",
        published_date="2024-01-15T00:00:00Z",
        categories=["nucl-th"],
        pdf_url="https://example.com/test1.pdf"
    )
    
    score1 = scorer.score_paper(paper1)
    assert score1 > 0.5, f"Expected high score, got {score1}"
    assert 'OpenMC' in paper1.keywords_matched
    print(f"  ✓ High relevance paper scored {score1:.2f}")
    
    # Low relevance paper
    paper2 = Paper(
        arxiv_id="test2",
        title="Quantum Computing Applications",
        authors=["Author"],
        abstract="This paper explores quantum computing for optimization problems.",
        published_date="2024-01-15T00:00:00Z",
        categories=["quant-ph"],
        pdf_url="https://example.com/test2.pdf"
    )
    
    score2 = scorer.score_paper(paper2)
    assert score2 == 0.0, f"Expected zero score, got {score2}"
    print(f"  ✓ Low relevance paper scored {score2:.2f}")


def test_issue_formatting():
    """Test GitHub issue formatting."""
    print("Testing issue formatting...")
    
    paper = Paper(
        arxiv_id="2401.12345",
        title="GPU-Accelerated Monte Carlo for OpenMC",
        authors=["John Doe", "Jane Smith"],
        abstract="We present novel GPU acceleration techniques.",
        published_date="2024-01-15T00:00:00Z",
        categories=["nucl-th"],
        pdf_url="https://arxiv.org/pdf/2401.12345.pdf",
        relevance_score=0.85,
        keywords_matched=["OpenMC", "GPU acceleration"]
    )
    
    title = format_issue_title(paper)
    assert title.startswith("[Literature]")
    assert "GPU-Accelerated" in title
    print(f"  ✓ Issue title: {title}")
    
    body = format_issue_body(paper)
    assert "2401.12345" in body
    assert "John Doe" in body
    assert "GPU acceleration" in body
    assert "0.85" in body
    print(f"  ✓ Issue body generated ({len(body)} chars)")


def main():
    """Run all tests."""
    print("="*60)
    print("OpenMC Literature Knowledge Base - Test Suite")
    print("="*60)
    print()
    
    try:
        test_paper_creation()
        test_database_operations()
        test_relevance_scorer()
        test_issue_formatting()
        
        print()
        print("="*60)
        print("✓ All tests passed!")
        print("="*60)
        return 0
    
    except AssertionError as e:
        print()
        print("="*60)
        print(f"✗ Test failed: {e}")
        print("="*60)
        return 1
    
    except Exception as e:
        print()
        print("="*60)
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("="*60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
