"""
OpenMC Literature Knowledge Base Service

This module provides functionality for monitoring academic literature
for potential OpenMC acceleration techniques and automatically creating
GitHub issues for promising ideas.
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET


@dataclass
class Paper:
    """Represents a research paper with metadata."""
    
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    published_date: str
    categories: List[str]
    pdf_url: str
    relevance_score: float = 0.0
    keywords_matched: List[str] = None
    issue_url: Optional[str] = None
    
    def __post_init__(self):
        if self.keywords_matched is None:
            self.keywords_matched = []
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Paper':
        """Create Paper from dictionary."""
        return cls(**data)


class PaperDatabase:
    """Manages the database of tracked papers."""
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.papers: Dict[str, Paper] = {}
        self.load()
    
    def load(self):
        """Load papers from JSON database."""
        if self.db_path.exists():
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                self.papers = {
                    paper_id: Paper.from_dict(paper_data)
                    for paper_id, paper_data in data.items()
                }
    
    def save(self):
        """Save papers to JSON database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, 'w') as f:
            data = {
                paper_id: paper.to_dict()
                for paper_id, paper in self.papers.items()
            }
            json.dump(data, f, indent=2)
    
    def add_paper(self, paper: Paper) -> bool:
        """Add a paper to the database. Returns True if new, False if duplicate."""
        if paper.arxiv_id in self.papers:
            return False
        self.papers[paper.arxiv_id] = paper
        return True
    
    def get_paper(self, arxiv_id: str) -> Optional[Paper]:
        """Retrieve a paper by arXiv ID."""
        return self.papers.get(arxiv_id)
    
    def mark_issue_created(self, arxiv_id: str, issue_url: str):
        """Mark that an issue has been created for this paper."""
        if arxiv_id in self.papers:
            self.papers[arxiv_id].issue_url = issue_url
            self.save()


class ArXivSearcher:
    """Search arXiv for relevant papers."""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def __init__(self, categories: List[str], max_results: int = 50):
        self.categories = categories
        self.max_results = max_results
    
    def search(self, keywords: List[str], exclude_older_than_days: int = 365) -> List[Paper]:
        """
        Search arXiv for papers matching keywords.
        
        Args:
            keywords: List of keywords to search for
            exclude_older_than_days: Only include papers from last N days
            
        Returns:
            List of Paper objects
        """
        papers = []
        cutoff_date = datetime.now() - timedelta(days=exclude_older_than_days)
        
        # Build query for each category
        for category in self.categories:
            for keyword in keywords:
                query = f'cat:{category} AND all:"{keyword}"'
                papers.extend(self._fetch_papers(query, cutoff_date))
        
        return papers
    
    def _fetch_papers(self, query: str, cutoff_date: datetime) -> List[Paper]:
        """Fetch papers from arXiv API."""
        papers = []
        
        params = {
            'search_query': query,
            'start': 0,
            'max_results': self.max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read()
            
            # Parse XML response
            root = ET.fromstring(data)
            ns = {'atom': 'http://www.w3.org/2005/Atom',
                  'arxiv': 'http://arxiv.org/schemas/atom'}
            
            for entry in root.findall('atom:entry', ns):
                paper = self._parse_entry(entry, ns, cutoff_date)
                if paper:
                    papers.append(paper)
        
        except Exception as e:
            print(f"Error fetching papers: {e}")
        
        return papers
    
    def _parse_entry(self, entry: ET.Element, ns: dict, cutoff_date: datetime) -> Optional[Paper]:
        """Parse an arXiv entry into a Paper object."""
        try:
            # Extract arXiv ID
            arxiv_id = entry.find('atom:id', ns).text.split('/abs/')[-1]
            
            # Check publication date
            published_str = entry.find('atom:published', ns).text
            published_date = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
            
            if published_date < cutoff_date:
                return None
            
            # Extract metadata
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            abstract = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
            
            authors = [
                author.find('atom:name', ns).text
                for author in entry.findall('atom:author', ns)
            ]
            
            categories = [
                cat.get('term')
                for cat in entry.findall('atom:category', ns)
            ]
            
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            return Paper(
                arxiv_id=arxiv_id,
                title=title,
                authors=authors,
                abstract=abstract,
                published_date=published_str,
                categories=categories,
                pdf_url=pdf_url
            )
        
        except Exception as e:
            print(f"Error parsing entry: {e}")
            return None


class RelevanceScorer:
    """Calculate relevance scores for papers."""
    
    def __init__(self, keywords_config: dict):
        self.keywords = self._flatten_keywords(keywords_config)
    
    def _flatten_keywords(self, config: dict) -> List[str]:
        """Flatten nested keyword configuration."""
        keywords = []
        for category, items in config.items():
            if isinstance(items, list):
                keywords.extend(items)
        return keywords
    
    def score_paper(self, paper: Paper) -> float:
        """
        Calculate relevance score for a paper.
        
        Returns:
            Float between 0 and 1 indicating relevance
        """
        text = f"{paper.title} {paper.abstract}".lower()
        
        # Count keyword matches
        matches = []
        for keyword in self.keywords:
            if keyword.lower() in text:
                matches.append(keyword)
        
        # Calculate score based on keyword density
        if not matches:
            return 0.0
        
        # Bonus for multiple unique keyword matches
        score = min(len(matches) / 10.0, 1.0)
        
        # Bonus for OpenMC specific mention
        if 'openmc' in text:
            score = min(score + 0.3, 1.0)
        
        # Store matched keywords
        paper.keywords_matched = matches
        paper.relevance_score = score
        
        return score


def format_issue_body(paper: Paper) -> str:
    """Format paper information as GitHub issue body."""
    body = f"""## Literature-Based Enhancement Proposal

### Paper Information
- **Title:** {paper.title}
- **Authors:** {', '.join(paper.authors)}
- **arXiv ID:** [{paper.arxiv_id}](https://arxiv.org/abs/{paper.arxiv_id})
- **Published:** {paper.published_date.split('T')[0]}
- **PDF:** [Download]({paper.pdf_url})

### Abstract
{paper.abstract}

### Relevance to OpenMC
This paper was identified through automated literature monitoring as potentially relevant to OpenMC acceleration.

**Matched Keywords:** {', '.join(paper.keywords_matched)}  
**Relevance Score:** {paper.relevance_score:.2f}

### Next Steps
1. Review the paper in detail
2. Assess feasibility of implementing proposed techniques in OpenMC
3. Determine if the approach could improve:
   - Simulation performance
   - Parallel scalability
   - Convergence rates
   - Memory efficiency
   - Multiphysics coupling

### Notes
This issue was automatically generated by the OpenMC Literature Knowledge Base service.
"""
    return body


def format_issue_title(paper: Paper) -> str:
    """Format paper title as GitHub issue title."""
    # Truncate if too long
    max_length = 100
    title = f"[Literature] {paper.title}"
    if len(title) > max_length:
        title = title[:max_length-3] + "..."
    return title
