"""
OpenMC Literature Knowledge Base Service

Automated monitoring of academic literature for OpenMC acceleration ideas.
"""

__version__ = "1.0.0"

from .literature_monitor import (
    Paper,
    PaperDatabase,
    ArXivSearcher,
    RelevanceScorer,
    format_issue_body,
    format_issue_title
)

__all__ = [
    'Paper',
    'PaperDatabase', 
    'ArXivSearcher',
    'RelevanceScorer',
    'format_issue_body',
    'format_issue_title'
]
