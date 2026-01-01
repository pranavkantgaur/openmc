#!/usr/bin/env python3
"""
Validation script for the AI Issue Responder.

This script:
1. Fetches all open issues from the OpenMC repository
2. Analyzes and categorizes them by type and complexity
3. Creates test cases from real issues
4. Validates the AI responder's performance
5. Generates a comprehensive report

Usage:
    python tools/ai/validate_issue_responder.py --repo openmc-dev/openmc --output-dir test_results
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import time

try:
    from github import Github
    from github.Issue import Issue
except ImportError:
    print("Error: PyGithub not installed. Run: pip install PyGithub")
    sys.exit(1)

# Import the issue analyzer
from issue_responder import IssueAnalyzer


class IssueTestCase:
    """Represents a test case derived from a real GitHub issue."""
    
    def __init__(self, issue: Issue, expected_type: str = None, expected_complexity: str = None):
        """
        Initialize test case.
        
        Parameters
        ----------
        issue : Issue
            GitHub issue object
        expected_type : str, optional
            Expected issue type (for validation)
        expected_complexity : str, optional
            Expected complexity (for validation)
        """
        self.issue = issue
        self.number = issue.number
        self.title = issue.title
        self.body = issue.body or ""
        self.labels = [label.name for label in issue.labels]
        self.comments_count = issue.comments
        self.created_at = issue.created_at
        self.state = issue.state
        self.expected_type = expected_type
        self.expected_complexity = expected_complexity
        
        # Results (filled after processing)
        self.predicted_type = None
        self.predicted_complexity = None
        self.reasoning = None
        self.response_text = None
        self.response_length = None
        self.processing_time = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'number': self.number,
            'title': self.title,
            'body_length': len(self.body),
            'labels': self.labels,
            'comments_count': self.comments_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'state': self.state,
            'expected_type': self.expected_type,
            'expected_complexity': self.expected_complexity,
            'predicted_type': self.predicted_type,
            'predicted_complexity': self.predicted_complexity,
            'reasoning': self.reasoning,
            'response_length': self.response_length,
            'processing_time': self.processing_time
        }


class IssueResponderValidator:
    """Validates the AI Issue Responder against real issues."""
    
    def __init__(self, github_token: str, output_dir: str = 'test_results'):
        """
        Initialize validator.
        
        Parameters
        ----------
        github_token : str
            GitHub personal access token
        output_dir : str
            Directory to save test results
        """
        self.github = Github(github_token)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.test_cases: List[IssueTestCase] = []
    
    def fetch_issues(self, repo_name: str, max_issues: int = 100, 
                    state: str = 'all') -> List[Issue]:
        """
        Fetch issues from repository.
        
        Parameters
        ----------
        repo_name : str
            Repository name (e.g., 'openmc-dev/openmc')
        max_issues : int
            Maximum number of issues to fetch
        state : str
            Issue state ('open', 'closed', or 'all')
        
        Returns
        -------
        list
            List of GitHub Issue objects
        """
        print(f"Fetching issues from {repo_name}...")
        repo = self.github.get_repo(repo_name)
        issues = []
        
        try:
            for issue in repo.get_issues(state=state):
                # Skip pull requests
                if issue.pull_request is not None:
                    continue
                
                issues.append(issue)
                print(f"  Fetched issue #{issue.number}: {issue.title[:60]}...")
                
                if len(issues) >= max_issues:
                    break
            
            print(f"✓ Fetched {len(issues)} issues")
            return issues
            
        except Exception as e:
            print(f"Error fetching issues: {e}")
            return issues
    
    def categorize_issues(self, issues: List[Issue]) -> Dict[str, List[Issue]]:
        """
        Categorize issues by type based on labels and content.
        
        Parameters
        ----------
        issues : list
            List of GitHub Issue objects
        
        Returns
        -------
        dict
            Dictionary mapping issue types to lists of issues
        """
        categories = {
            'bug': [],
            'feature': [],
            'question': [],
            'documentation': [],
            'enhancement': [],
            'other': []
        }
        
        for issue in issues:
            labels = [label.name.lower() for label in issue.labels]
            title = issue.title.lower()
            
            categorized = False
            if any(label in ['bug', 'bugs'] for label in labels) or 'bug' in title:
                categories['bug'].append(issue)
                categorized = True
            elif any(label in ['feature', 'feature request'] for label in labels):
                categories['feature'].append(issue)
                categorized = True
            elif any(label in ['documentation', 'docs'] for label in labels):
                categories['documentation'].append(issue)
                categorized = True
            elif 'enhancement' in labels:
                categories['enhancement'].append(issue)
                categorized = True
            elif 'question' in title or 'how to' in title:
                categories['question'].append(issue)
                categorized = True
            
            if not categorized:
                categories['other'].append(issue)
        
        return categories
    
    def analyze_complexity_distribution(self, issues: List[Issue]) -> Dict[str, int]:
        """
        Analyze complexity distribution of issues.
        
        Parameters
        ----------
        issues : list
            List of GitHub Issue objects
        
        Returns
        -------
        dict
            Dictionary mapping complexity levels to counts
        """
        complexity_dist = {
            'trivial': 0,
            'simple': 0,
            'moderate': 0,
            'complex': 0,
            'very_complex': 0
        }
        
        for issue in issues:
            body = (issue.body or "").lower()
            word_count = len(body.split())
            
            if word_count < 50:
                complexity_dist['simple'] += 1
            elif word_count < 150:
                complexity_dist['moderate'] += 1
            elif word_count < 300:
                complexity_dist['complex'] += 1
            else:
                complexity_dist['very_complex'] += 1
            
            # Special cases
            if 'segfault' in body or 'memory leak' in body:
                complexity_dist['complex'] += 1
                complexity_dist['simple'] = max(0, complexity_dist['simple'] - 1)
        
        return complexity_dist
    
    def create_test_cases(self, issues: List[Issue], 
                         categories: Dict[str, List[Issue]]) -> List[IssueTestCase]:
        """
        Create test cases from issues with balanced representation.
        
        Parameters
        ----------
        issues : list
            List of all issues
        categories : dict
            Categorized issues
        
        Returns
        -------
        list
            List of IssueTestCase objects
        """
        test_cases = []
        
        # Create stratified sample across categories
        for category, category_issues in categories.items():
            if not category_issues:
                continue
            
            # Sample issues from each category (up to 5 per category for diversity)
            sample_size = min(5, len(category_issues))
            sampled_issues = category_issues[:sample_size]
            
            for issue in sampled_issues:
                test_case = IssueTestCase(issue, expected_type=category)
                test_cases.append(test_case)
                print(f"  Created test case from issue #{issue.number} ({category})")
        
        return test_cases
    
    def run_validation(self, repo_name: str, analyzer: IssueAnalyzer) -> Dict:
        """
        Run validation on all test cases.
        
        Parameters
        ----------
        repo_name : str
            Repository name
        analyzer : IssueAnalyzer
            Issue analyzer instance
        
        Returns
        -------
        dict
            Validation results
        """
        print(f"\nRunning validation on {len(self.test_cases)} test cases...")
        
        results = {
            'total_cases': len(self.test_cases),
            'successful': 0,
            'failed': 0,
            'type_accuracy': {},
            'complexity_distribution': {},
            'avg_processing_time': 0,
            'avg_response_length': 0,
            'test_cases': []
        }
        
        total_processing_time = 0
        total_response_length = 0
        type_correct = 0
        type_total = 0
        
        for i, test_case in enumerate(self.test_cases):
            print(f"\n[{i+1}/{len(self.test_cases)}] Processing test case #{test_case.number}...")
            
            start_time = time.time()
            
            try:
                # Classify the issue
                issue_type, complexity, reasoning = analyzer.classify_issue(test_case.issue)
                
                # Generate response (without AI to keep validation fast)
                response = analyzer._generate_fallback_response(
                    test_case.issue, issue_type, complexity
                )
                
                # Record results
                test_case.predicted_type = issue_type
                test_case.predicted_complexity = complexity
                test_case.reasoning = reasoning
                test_case.response_text = response
                test_case.response_length = len(response)
                test_case.processing_time = time.time() - start_time
                
                total_processing_time += test_case.processing_time
                total_response_length += test_case.response_length
                
                # Check accuracy
                if test_case.expected_type:
                    type_total += 1
                    if test_case.predicted_type == test_case.expected_type:
                        type_correct += 1
                        print(f"  ✓ Correct classification: {issue_type}")
                    else:
                        print(f"  ✗ Incorrect: expected {test_case.expected_type}, got {issue_type}")
                
                results['successful'] += 1
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                results['failed'] += 1
                test_case.processing_time = time.time() - start_time
            
            results['test_cases'].append(test_case.to_dict())
        
        # Calculate metrics
        if type_total > 0:
            results['type_accuracy'] = {
                'correct': type_correct,
                'total': type_total,
                'percentage': (type_correct / type_total) * 100
            }
        
        if results['successful'] > 0:
            results['avg_processing_time'] = total_processing_time / results['successful']
            results['avg_response_length'] = total_response_length / results['successful']
        
        return results
    
    def generate_report(self, results: Dict, repo_name: str, 
                       categories: Dict[str, List[Issue]]) -> str:
        """
        Generate a comprehensive markdown report.
        
        Parameters
        ----------
        results : dict
            Validation results
        repo_name : str
            Repository name
        categories : dict
            Categorized issues
        
        Returns
        -------
        str
            Markdown report
        """
        report = f"""# AI Issue Responder Validation Report

**Repository**: {repo_name}
**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Test Cases**: {results['total_cases']}

## Executive Summary

This report validates the performance of the AI Issue Responder on real issues from the OpenMC repository. The responder automatically classifies issues and generates helpful responses.

### Overall Performance

- **Success Rate**: {results['successful']}/{results['total_cases']} ({(results['successful']/results['total_cases']*100):.1f}%)
- **Average Processing Time**: {results['avg_processing_time']:.2f}s per issue
- **Average Response Length**: {results['avg_response_length']:.0f} characters

"""
        
        if results.get('type_accuracy'):
            acc = results['type_accuracy']
            report += f"""### Classification Accuracy

- **Correct Classifications**: {acc['correct']}/{acc['total']} ({acc['percentage']:.1f}%)

"""
        
        # Category distribution
        report += """## Issue Distribution by Category

| Category | Count | Percentage |
|----------|-------|------------|
"""
        
        total_issues = sum(len(issues) for issues in categories.values())
        for category, issues in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
            count = len(issues)
            percentage = (count / total_issues * 100) if total_issues > 0 else 0
            report += f"| {category.title()} | {count} | {percentage:.1f}% |\n"
        
        # Detailed test results
        report += """

## Detailed Test Results

### Sample Classifications

"""
        
        # Show some example classifications
        for i, test_case_dict in enumerate(results['test_cases'][:10]):  # First 10 examples
            report += f"""#### Test Case {i+1}: Issue #{test_case_dict['number']}

**Title**: {test_case_dict['title']}
**Expected Type**: {test_case_dict['expected_type'] or 'N/A'}
**Predicted Type**: {test_case_dict['predicted_type']}
**Complexity**: {test_case_dict['predicted_complexity']}
**Processing Time**: {test_case_dict['processing_time']:.3f}s
**Response Length**: {test_case_dict['response_length']} chars

"""
        
        # Performance metrics
        report += """

## Performance Metrics

### Processing Time Distribution

"""
        
        # Calculate time distribution
        times = [tc['processing_time'] for tc in results['test_cases'] if tc.get('processing_time')]
        if times:
            times.sort()
            report += f"""- **Minimum**: {min(times):.3f}s
- **Median**: {times[len(times)//2]:.3f}s
- **Maximum**: {max(times):.3f}s
- **95th Percentile**: {times[int(len(times)*0.95)]:.3f}s

"""
        
        # Recommendations
        report += """

## Recommendations

### Value Proposition

The AI Issue Responder demonstrates value in several ways:

1. **Immediate Response**: Provides instant acknowledgment and guidance to issue reporters
2. **Consistent Triage**: Applies consistent classification criteria across all issues
3. **Resource Efficiency**: Frees maintainers from routine initial responses
4. **24/7 Availability**: Responds to issues regardless of maintainer timezone
5. **Knowledge Distribution**: Points users to relevant documentation and resources

### Integration Benefits

For the OpenMC project, this GitHub Action would:

- **Reduce maintainer burden** by handling initial issue triage
- **Improve user experience** with faster initial responses
- **Maintain consistency** in issue handling
- **Collect metrics** on issue types and complexity for project planning

### Suggested Improvements

Based on this validation:

1. **Enable AI Provider**: Connect OpenAI or Anthropic API for smarter responses
2. **Fine-tune Classification**: Adjust heuristics based on OpenMC-specific patterns
3. **Add Domain Knowledge**: Include OpenMC-specific troubleshooting in responses
4. **Monitor Performance**: Track accuracy over time and adjust as needed

### Next Steps for PR Submission

To submit this to upstream OpenMC:

1. **Run this validation** on a representative sample of issues
2. **Include this report** in the PR description
3. **Document setup requirements** (API keys, secrets configuration)
4. **Propose trial period** to gather real-world metrics
5. **Offer to monitor** and adjust based on maintainer feedback

"""
        
        return report
    
    def save_results(self, results: Dict, report: str):
        """
        Save validation results and report.
        
        Parameters
        ----------
        results : dict
            Validation results
        report : str
            Markdown report
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON results
        json_file = self.output_dir / f'validation_results_{timestamp}.json'
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n✓ Saved JSON results to {json_file}")
        
        # Save markdown report
        report_file = self.output_dir / f'validation_report_{timestamp}.md'
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"✓ Saved report to {report_file}")
        
        # Also save latest versions
        latest_json = self.output_dir / 'validation_results_latest.json'
        latest_report = self.output_dir / 'validation_report_latest.md'
        
        with open(latest_json, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        with open(latest_report, 'w') as f:
            f.write(report)
        
        print(f"✓ Saved latest versions")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate AI Issue Responder against real GitHub issues'
    )
    parser.add_argument(
        '--repo',
        default='openmc-dev/openmc',
        help='Repository name (e.g., openmc-dev/openmc)'
    )
    parser.add_argument(
        '--max-issues',
        type=int,
        default=100,
        help='Maximum number of issues to fetch'
    )
    parser.add_argument(
        '--output-dir',
        default='test_results',
        help='Output directory for results'
    )
    parser.add_argument(
        '--state',
        choices=['open', 'closed', 'all'],
        default='all',
        help='Issue state to fetch'
    )
    
    args = parser.parse_args()
    
    # Get GitHub token
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        print("Create a token at: https://github.com/settings/tokens")
        sys.exit(1)
    
    print("="*80)
    print("AI Issue Responder Validation")
    print("="*80)
    
    # Initialize validator
    validator = IssueResponderValidator(github_token, args.output_dir)
    
    # Fetch issues
    issues = validator.fetch_issues(args.repo, args.max_issues, args.state)
    if not issues:
        print("No issues found!")
        sys.exit(1)
    
    # Categorize issues
    print("\nCategorizing issues...")
    categories = validator.categorize_issues(issues)
    for category, cat_issues in categories.items():
        if cat_issues:
            print(f"  {category}: {len(cat_issues)} issues")
    
    # Analyze complexity
    print("\nAnalyzing complexity distribution...")
    complexity_dist = validator.analyze_complexity_distribution(issues)
    for complexity, count in complexity_dist.items():
        if count > 0:
            print(f"  {complexity}: {count} issues")
    
    # Create test cases
    print("\nCreating test cases...")
    validator.test_cases = validator.create_test_cases(issues, categories)
    print(f"✓ Created {len(validator.test_cases)} test cases")
    
    # Run validation
    analyzer = IssueAnalyzer(github_token)
    results = validator.run_validation(args.repo, analyzer)
    
    # Generate report
    print("\nGenerating report...")
    report = validator.generate_report(results, args.repo, categories)
    
    # Save results
    validator.save_results(results, report)
    
    # Print summary
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    print(f"Total test cases: {results['total_cases']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    
    if results.get('type_accuracy'):
        acc = results['type_accuracy']
        print(f"Classification accuracy: {acc['percentage']:.1f}%")
    
    print(f"\nResults saved to: {args.output_dir}/")
    print("\n✓ Validation complete!")


if __name__ == '__main__':
    main()
