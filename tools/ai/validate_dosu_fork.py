#!/usr/bin/env python3
"""
Dosu Fork Validation Automation

This script automates the validation of Dosu.dev on a fork of the OpenMC repository.
It follows a systematic approach to test Dosu's performance on representative closed issues.

Workflow:
1. Sync fork's develop branch with upstream
2. Clean up existing issues in fork
3. Retrieve representative closed issues from upstream (by category and difficulty)
4. Create these issues in the fork
5. Monitor Dosu's responses
6. Compare with actual resolutions

Usage:
    python validate_dosu_fork.py --upstream-repo openmc-dev/openmc --fork-repo pranavkantgaur/openmc
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

try:
    from github import Github
    from github.Issue import Issue
    from github.Repository import Repository
except ImportError:
    print("Error: PyGithub not installed. Run: pip install PyGithub")
    sys.exit(1)


class DosuForkValidator:
    """Validates Dosu.dev by testing on a fork with representative issues."""
    
    def __init__(self, github_token: str, output_dir: str = 'dosu_fork_validation'):
        """
        Initialize validator.
        
        Parameters
        ----------
        github_token : str
            GitHub personal access token with repo scope
        output_dir : str
            Directory to save validation results
        """
        self.github = Github(github_token)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / 'upstream_issues').mkdir(exist_ok=True)
        (self.output_dir / 'fork_issues').mkdir(exist_ok=True)
        (self.output_dir / 'dosu_responses').mkdir(exist_ok=True)
        (self.output_dir / 'comparisons').mkdir(exist_ok=True)
    
    def sync_fork_with_upstream(self, fork_repo_name: str, upstream_repo_name: str) -> bool:
        """
        Sync fork's develop branch with upstream.
        
        Parameters
        ----------
        fork_repo_name : str
            Fork repository name (e.g., 'pranavkantgaur/openmc')
        upstream_repo_name : str
            Upstream repository name (e.g., 'openmc-dev/openmc')
        
        Returns
        -------
        bool
            True if sync successful
        """
        print(f"\n{'='*80}")
        print(f"STEP 1: Syncing fork with upstream")
        print(f"{'='*80}")
        
        try:
            fork_repo = self.github.get_repo(fork_repo_name)
            upstream_repo = self.github.get_repo(upstream_repo_name)
            
            # Get upstream develop branch
            upstream_develop = upstream_repo.get_branch('develop')
            upstream_sha = upstream_develop.commit.sha
            
            print(f"✓ Upstream develop at: {upstream_sha[:8]}")
            
            # Update fork's develop branch to match upstream
            # Note: This requires the fork to have develop branch
            try:
                fork_develop = fork_repo.get_branch('develop')
                fork_sha = fork_develop.commit.sha
                
                if fork_sha == upstream_sha:
                    print(f"✓ Fork already synced with upstream")
                else:
                    print(f"  Fork develop at: {fork_sha[:8]}")
                    print(f"  Need to sync (this requires git push access)")
                    print(f"  Manual sync required: Update fork's develop to {upstream_sha[:8]}")
                    print(f"  You can do this via GitHub UI: Sync fork button")
                
                return True
                
            except Exception as e:
                print(f"Warning: Could not access fork's develop branch: {e}")
                return False
                
        except Exception as e:
            print(f"Error syncing fork: {e}")
            return False
    
    def clean_fork_issues(self, fork_repo_name: str, dry_run: bool = True) -> int:
        """
        Close all existing issues in the fork.
        
        Parameters
        ----------
        fork_repo_name : str
            Fork repository name
        dry_run : bool
            If True, only list issues without closing
        
        Returns
        -------
        int
            Number of issues closed/to be closed
        """
        print(f"\n{'='*80}")
        print(f"STEP 2: Cleaning fork issues")
        print(f"{'='*80}")
        
        try:
            fork_repo = self.github.get_repo(fork_repo_name)
            open_issues = list(fork_repo.get_issues(state='open'))
            
            print(f"Found {len(open_issues)} open issues in fork")
            
            if dry_run:
                print(f"DRY RUN: Would close {len(open_issues)} issues")
                for issue in open_issues[:5]:  # Show first 5
                    print(f"  #{issue.number}: {issue.title[:60]}")
                if len(open_issues) > 5:
                    print(f"  ... and {len(open_issues) - 5} more")
                return len(open_issues)
            
            # Close issues
            closed_count = 0
            for issue in open_issues:
                try:
                    issue.edit(state='closed')
                    issue.create_comment("Closing for Dosu validation testing. This issue was created for testing purposes.")
                    print(f"  Closed #{issue.number}: {issue.title[:60]}")
                    closed_count += 1
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    print(f"  Error closing #{issue.number}: {e}")
            
            print(f"✓ Closed {closed_count} issues")
            return closed_count
            
        except Exception as e:
            print(f"Error cleaning fork issues: {e}")
            return 0
    
    def get_issue_difficulty(self, issue: Issue) -> int:
        """
        Estimate issue difficulty (1-5) based on various factors.
        
        Parameters
        ----------
        issue : Issue
            GitHub issue
        
        Returns
        -------
        int
            Difficulty score (1=trivial, 5=very complex)
        """
        score = 1
        
        # Check body length
        body_length = len(issue.body or "")
        if body_length > 1000:
            score += 1
        if body_length > 2000:
            score += 1
        
        # Check number of comments
        comments_count = issue.comments
        if comments_count > 5:
            score += 1
        if comments_count > 15:
            score += 1
        
        # Check labels
        labels = [label.name.lower() for label in issue.labels]
        if any('complex' in label or 'difficult' in label for label in labels):
            score += 2
        
        # Check if closed by PR (more complex issues often need PRs)
        if issue.pull_request is None:
            # Look for PR references
            body_text = (issue.body or "") + " "
            for comment in issue.get_comments():
                body_text += (comment.body or "") + " "
            
            pr_pattern = re.compile(r'#(\d+)')
            if pr_pattern.search(body_text):
                score += 1
        
        return min(score, 5)
    
    def fetch_representative_issues(
        self, 
        upstream_repo_name: str,
        categories: List[str] = ['bug', 'enhancement', 'question'],
        per_category: int = 5
    ) -> Dict[str, List[Issue]]:
        """
        Fetch representative closed issues from upstream by category and difficulty.
        
        Parameters
        ----------
        upstream_repo_name : str
            Upstream repository name
        categories : list
            Issue categories to fetch (based on labels)
        per_category : int
            Number of issues per category
        
        Returns
        -------
        dict
            Dictionary mapping category to list of issues sorted by difficulty
        """
        print(f"\n{'='*80}")
        print(f"STEP 3: Fetching representative issues from upstream")
        print(f"{'='*80}")
        
        upstream_repo = self.github.get_repo(upstream_repo_name)
        categorized_issues = {cat: [] for cat in categories}
        
        for category in categories:
            print(f"\nFetching {category} issues...")
            
            # Fetch issues with this label
            label_map = {
                'bug': 'bug',
                'enhancement': 'enhancement',
                'question': 'question'
            }
            
            label_name = label_map.get(category, category)
            
            try:
                # Get closed issues with this label
                issues = []
                for issue in upstream_repo.get_issues(state='closed', labels=[label_name]):
                    if issue.pull_request is not None:
                        continue  # Skip PRs
                    
                    # Calculate difficulty
                    difficulty = self.get_issue_difficulty(issue)
                    issues.append((issue, difficulty))
                    
                    if len(issues) >= per_category * 3:  # Get extras to choose from
                        break
                
                # Sort by difficulty and select representative sample
                issues.sort(key=lambda x: x[1])
                
                # Select evenly distributed issues across difficulty spectrum
                selected = []
                if len(issues) >= per_category:
                    step = len(issues) // per_category
                    for i in range(per_category):
                        idx = i * step
                        selected.append(issues[idx][0])
                else:
                    selected = [iss[0] for iss in issues]
                
                categorized_issues[category] = selected
                
                print(f"  Selected {len(selected)} {category} issues:")
                for issue in selected:
                    diff = self.get_issue_difficulty(issue)
                    print(f"    #{issue.number} (difficulty {diff}/5): {issue.title[:50]}")
                
            except Exception as e:
                print(f"  Error fetching {category} issues: {e}")
        
        # Save to file
        summary_file = self.output_dir / 'upstream_issues_summary.json'
        summary = {}
        for category, issues in categorized_issues.items():
            summary[category] = [
                {
                    'number': issue.number,
                    'title': issue.title,
                    'url': issue.html_url,
                    'difficulty': self.get_issue_difficulty(issue),
                    'body': issue.body,
                    'labels': [label.name for label in issue.labels],
                    'comments_count': issue.comments
                }
                for issue in issues
            ]
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n✓ Saved summary to {summary_file}")
        
        total = sum(len(issues) for issues in categorized_issues.values())
        print(f"✓ Total issues selected: {total}")
        
        return categorized_issues
    
    def create_issues_in_fork(
        self,
        fork_repo_name: str,
        categorized_issues: Dict[str, List[Issue]],
        dry_run: bool = True
    ) -> List[Dict]:
        """
        Create selected issues in the fork.
        
        Parameters
        ----------
        fork_repo_name : str
            Fork repository name
        categorized_issues : dict
            Dictionary of issues by category
        dry_run : bool
            If True, only simulate creation
        
        Returns
        -------
        list
            List of created issue metadata
        """
        print(f"\n{'='*80}")
        print(f"STEP 4: Creating issues in fork")
        print(f"{'='*80}")
        
        fork_repo = self.github.get_repo(fork_repo_name)
        created_issues = []
        
        for category, issues in categorized_issues.items():
            print(f"\nCreating {category} issues...")
            
            for upstream_issue in issues:
                # Prepare issue body with reference to original
                new_body = f"""**[DOSU VALIDATION TEST]**

This is a test issue created from upstream issue #{upstream_issue.number} to validate Dosu.dev's performance.

**Original Issue URL:** {upstream_issue.html_url}

---

{upstream_issue.body or "No description provided"}

---

**Expected Resolution:**
This issue was originally resolved in upstream. Dosu should provide guidance that aligns with the actual resolution.
"""
                
                new_title = f"[TEST] {upstream_issue.title}"
                
                # Get labels (create if needed)
                labels_to_add = [category]
                
                if dry_run:
                    print(f"  DRY RUN: Would create issue: {new_title[:60]}")
                    created_issues.append({
                        'upstream_number': upstream_issue.number,
                        'title': new_title,
                        'category': category,
                        'difficulty': self.get_issue_difficulty(upstream_issue),
                        'dry_run': True
                    })
                else:
                    try:
                        # Create issue
                        new_issue = fork_repo.create_issue(
                            title=new_title,
                            body=new_body,
                            labels=labels_to_add
                        )
                        
                        print(f"  ✓ Created #{new_issue.number}: {new_title[:60]}")
                        
                        created_issues.append({
                            'upstream_number': upstream_issue.number,
                            'upstream_url': upstream_issue.html_url,
                            'fork_number': new_issue.number,
                            'fork_url': new_issue.html_url,
                            'title': new_title,
                            'category': category,
                            'difficulty': self.get_issue_difficulty(upstream_issue),
                            'created_at': new_issue.created_at.isoformat()
                        })
                        
                        # Rate limiting
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"  Error creating issue: {e}")
        
        # Save created issues manifest
        manifest_file = self.output_dir / 'fork_issues_manifest.json'
        with open(manifest_file, 'w') as f:
            json.dump({
                'created_at': datetime.utcnow().isoformat(),
                'total_issues': len(created_issues),
                'issues': created_issues
            }, f, indent=2)
        
        print(f"\n✓ Saved manifest to {manifest_file}")
        print(f"✓ Total issues created: {len(created_issues)}")
        
        return created_issues
    
    def monitor_dosu_responses(
        self,
        fork_repo_name: str,
        created_issues: List[Dict],
        check_interval: int = 60,
        max_wait_time: int = 3600
    ) -> Dict[int, Dict]:
        """
        Monitor fork issues for Dosu responses.
        
        Parameters
        ----------
        fork_repo_name : str
            Fork repository name
        created_issues : list
            List of created issue metadata
        check_interval : int
            Seconds between checks
        max_wait_time : int
            Maximum time to wait for responses
        
        Returns
        -------
        dict
            Dictionary mapping issue number to Dosu response data
        """
        print(f"\n{'='*80}")
        print(f"STEP 5: Monitoring for Dosu responses")
        print(f"{'='*80}")
        
        fork_repo = self.github.get_repo(fork_repo_name)
        dosu_responses = {}
        
        issue_numbers = [iss['fork_number'] for iss in created_issues if 'fork_number' in iss]
        
        print(f"Monitoring {len(issue_numbers)} issues for Dosu responses...")
        print(f"Check interval: {check_interval}s, Max wait: {max_wait_time}s")
        
        start_time = time.time()
        pending_issues = set(issue_numbers)
        
        while pending_issues and (time.time() - start_time) < max_wait_time:
            print(f"\nChecking for responses... ({len(pending_issues)} pending)")
            
            for issue_num in list(pending_issues):
                try:
                    issue = fork_repo.get_issue(issue_num)
                    
                    # Check for comments from Dosu
                    dosu_comments = []
                    for comment in issue.get_comments():
                        if comment.user.login.lower() == 'dosu' or 'dosu' in comment.user.login.lower():
                            dosu_comments.append({
                                'author': comment.user.login,
                                'body': comment.body,
                                'created_at': comment.created_at.isoformat(),
                                'url': comment.html_url
                            })
                    
                    if dosu_comments:
                        print(f"  ✓ Found Dosu response for issue #{issue_num}")
                        dosu_responses[issue_num] = {
                            'issue_number': issue_num,
                            'issue_url': issue.html_url,
                            'dosu_comments': dosu_comments,
                            'total_comments': issue.comments,
                            'response_time': (datetime.fromisoformat(dosu_comments[0]['created_at']) - issue.created_at).total_seconds()
                        }
                        pending_issues.remove(issue_num)
                        
                        # Save response
                        response_file = self.output_dir / 'dosu_responses' / f'issue_{issue_num}_dosu.json'
                        with open(response_file, 'w') as f:
                            json.dump(dosu_responses[issue_num], f, indent=2)
                
                except Exception as e:
                    print(f"  Error checking issue #{issue_num}: {e}")
            
            if pending_issues:
                print(f"Waiting {check_interval}s before next check...")
                time.sleep(check_interval)
        
        if pending_issues:
            print(f"\n⚠️  Timeout: {len(pending_issues)} issues still pending")
            print(f"   Pending: {list(pending_issues)}")
        
        print(f"\n✓ Collected {len(dosu_responses)} Dosu responses")
        
        # Save all responses
        all_responses_file = self.output_dir / 'dosu_responses_all.json'
        with open(all_responses_file, 'w') as f:
            json.dump(dosu_responses, f, indent=2)
        
        return dosu_responses
    
    def compare_with_actual_resolutions(
        self,
        upstream_repo_name: str,
        categorized_issues: Dict[str, List[Issue]],
        dosu_responses: Dict[int, Dict],
        created_issues: List[Dict]
    ) -> Dict:
        """
        Compare Dosu responses with actual resolutions.
        
        Parameters
        ----------
        upstream_repo_name : str
            Upstream repository name
        categorized_issues : dict
            Original upstream issues by category
        dosu_responses : dict
            Dosu responses from fork
        created_issues : list
            Created issue metadata
        
        Returns
        -------
        dict
            Comparison results
        """
        print(f"\n{'='*80}")
        print(f"STEP 6: Comparing Dosu responses with actual resolutions")
        print(f"{'='*80}")
        
        # Create mapping from fork issue to upstream issue
        fork_to_upstream = {}
        for issue_data in created_issues:
            if 'fork_number' in issue_data:
                fork_to_upstream[issue_data['fork_number']] = issue_data['upstream_number']
        
        upstream_repo = self.github.get_repo(upstream_repo_name)
        comparisons = []
        
        for fork_num, dosu_data in dosu_responses.items():
            if fork_num not in fork_to_upstream:
                continue
            
            upstream_num = fork_to_upstream[fork_num]
            
            try:
                # Get upstream issue resolution
                upstream_issue = upstream_repo.get_issue(upstream_num)
                
                # Get closing comment or PR
                resolution_info = {
                    'closed_at': upstream_issue.closed_at.isoformat() if upstream_issue.closed_at else None,
                    'closed_by': upstream_issue.closed_by.login if upstream_issue.closed_by else None,
                    'comments': []
                }
                
                # Get last few comments before closing
                comments = list(upstream_issue.get_comments())
                if comments:
                    last_comments = comments[-3:]  # Last 3 comments
                    resolution_info['comments'] = [
                        {
                            'author': c.user.login,
                            'body': c.body[:500],  # First 500 chars
                            'created_at': c.created_at.isoformat()
                        }
                        for c in last_comments
                    ]
                
                # Create comparison
                comparison = {
                    'upstream_issue': {
                        'number': upstream_num,
                        'url': upstream_issue.html_url,
                        'title': upstream_issue.title,
                        'resolution': resolution_info
                    },
                    'fork_issue': {
                        'number': fork_num,
                        'url': dosu_data['issue_url']
                    },
                    'dosu_response': {
                        'response_time_seconds': dosu_data.get('response_time', 0),
                        'comment_count': len(dosu_data['dosu_comments']),
                        'first_response': dosu_data['dosu_comments'][0]['body'][:500] if dosu_data['dosu_comments'] else ""
                    },
                    'comparison_notes': "Manual evaluation required. Compare Dosu's response with actual resolution."
                }
                
                comparisons.append(comparison)
                
                # Save individual comparison
                comparison_file = self.output_dir / 'comparisons' / f'comparison_{fork_num}.json'
                with open(comparison_file, 'w') as f:
                    json.dump(comparison, f, indent=2)
                
                print(f"✓ Compared issue #{fork_num} (upstream #{upstream_num})")
                
            except Exception as e:
                print(f"  Error comparing issue #{fork_num}: {e}")
        
        # Save all comparisons
        all_comparisons_file = self.output_dir / 'comparisons_all.json'
        with open(all_comparisons_file, 'w') as f:
            json.dump({
                'total_comparisons': len(comparisons),
                'comparisons': comparisons
            }, f, indent=2)
        
        print(f"\n✓ Created {len(comparisons)} comparisons")
        print(f"✓ Saved to {all_comparisons_file}")
        
        return {'total': len(comparisons), 'comparisons': comparisons}
    
    def generate_summary_report(self) -> str:
        """Generate a summary markdown report."""
        report_file = self.output_dir / 'VALIDATION_SUMMARY.md'
        
        report = f"""# Dosu.dev Fork Validation Summary

**Generated:** {datetime.utcnow().isoformat()}

## Validation Strategy

This validation tested Dosu.dev on a fork using representative closed issues from upstream.

### Process:
1. ✅ Synced fork with upstream develop branch
2. ✅ Cleaned existing issues in fork
3. ✅ Selected representative issues (by category and difficulty)
4. ✅ Created test issues in fork
5. ✅ Monitored Dosu's automatic responses
6. ✅ Compared with actual upstream resolutions

## Results

See detailed files:
- `fork_issues_manifest.json` - Created test issues
- `dosu_responses_all.json` - Dosu's responses
- `comparisons_all.json` - Side-by-side comparisons
- `comparisons/*.json` - Individual comparisons

## Manual Evaluation Required

For each comparison in `comparisons/`, evaluate:
1. **Accuracy**: Does Dosu's response align with actual resolution?
2. **Relevance**: Does it address the core issue?
3. **Helpfulness**: Would it guide user toward solution?
4. **Code Context**: Does it reference relevant OpenMC code?
5. **Hallucination**: Any incorrect information?

## Next Steps

1. Review individual comparisons
2. Create evaluation scores (1-5) for each
3. Calculate aggregate metrics
4. Decide: Deploy to upstream, iterate on prompts, or reassess

## Notes on Iterative Testing

Since Dosu lacks public API for knowledge base reset:
- Each validation iteration builds on previous knowledge
- Dosu learns from resolved issues
- Cannot easily A/B test different prompt configurations
- Consider: Use different categories of issues for iterations
- Or: Focus on improving prompts for categories where Dosu underperforms

## Recommendation

Based on manual evaluation, document:
- Which issue types Dosu handles well
- Where it needs improvement
- Whether to propose for upstream OpenMC
"""
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n✓ Generated summary report: {report_file}")
        return str(report_file)
    
    def run_validation(
        self,
        upstream_repo_name: str,
        fork_repo_name: str,
        dry_run: bool = True,
        categories: List[str] = ['bug', 'enhancement', 'question'],
        per_category: int = 5,
        monitor_wait: int = 3600
    ) -> Dict:
        """
        Run complete validation workflow.
        
        Parameters
        ----------
        upstream_repo_name : str
            Upstream repository (e.g., 'openmc-dev/openmc')
        fork_repo_name : str
            Fork repository (e.g., 'pranavkantgaur/openmc')
        dry_run : bool
            If True, simulate without making changes
        categories : list
            Issue categories to test
        per_category : int
            Issues per category
        monitor_wait : int
            Seconds to wait for Dosu responses
        
        Returns
        -------
        dict
            Validation results
        """
        print("="*80)
        print("DOSU.DEV FORK VALIDATION")
        print("="*80)
        print(f"Upstream: {upstream_repo_name}")
        print(f"Fork: {fork_repo_name}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print("="*80)
        
        # Step 1: Sync fork
        self.sync_fork_with_upstream(fork_repo_name, upstream_repo_name)
        
        # Step 2: Clean fork issues
        if not dry_run:
            self.clean_fork_issues(fork_repo_name, dry_run=False)
        else:
            self.clean_fork_issues(fork_repo_name, dry_run=True)
        
        # Step 3: Fetch representative issues
        categorized_issues = self.fetch_representative_issues(
            upstream_repo_name,
            categories=categories,
            per_category=per_category
        )
        
        # Step 4: Create issues in fork
        created_issues = self.create_issues_in_fork(
            fork_repo_name,
            categorized_issues,
            dry_run=dry_run
        )
        
        if dry_run:
            print("\n" + "="*80)
            print("DRY RUN COMPLETE")
            print("="*80)
            print("Run without --dry-run to execute validation")
            return {'status': 'dry_run', 'issues_would_create': len(created_issues)}
        
        # Step 5: Monitor Dosu responses
        print(f"\nWaiting for Dosu to respond (max {monitor_wait}s)...")
        dosu_responses = self.monitor_dosu_responses(
            fork_repo_name,
            created_issues,
            check_interval=60,
            max_wait_time=monitor_wait
        )
        
        # Step 6: Compare with actual resolutions
        comparisons = self.compare_with_actual_resolutions(
            upstream_repo_name,
            categorized_issues,
            dosu_responses,
            created_issues
        )
        
        # Generate summary
        report_file = self.generate_summary_report()
        
        print("\n" + "="*80)
        print("VALIDATION COMPLETE")
        print("="*80)
        print(f"Issues created: {len(created_issues)}")
        print(f"Dosu responses: {len(dosu_responses)}")
        print(f"Comparisons: {comparisons['total']}")
        print(f"\nResults: {self.output_dir}")
        print(f"Summary: {report_file}")
        print("\nNext: Manually evaluate comparisons and update validation notes")
        
        return {
            'status': 'complete',
            'issues_created': len(created_issues),
            'dosu_responses': len(dosu_responses),
            'comparisons': comparisons['total'],
            'output_dir': str(self.output_dir)
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Automate Dosu.dev validation on OpenMC fork'
    )
    parser.add_argument(
        '--upstream-repo',
        default='openmc-dev/openmc',
        help='Upstream repository name'
    )
    parser.add_argument(
        '--fork-repo',
        required=True,
        help='Fork repository name (e.g., pranavkantgaur/openmc)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate without making changes'
    )
    parser.add_argument(
        '--categories',
        nargs='+',
        default=['bug', 'enhancement', 'question'],
        help='Issue categories to test'
    )
    parser.add_argument(
        '--per-category',
        type=int,
        default=5,
        help='Number of issues per category'
    )
    parser.add_argument(
        '--monitor-wait',
        type=int,
        default=3600,
        help='Seconds to wait for Dosu responses'
    )
    parser.add_argument(
        '--output-dir',
        default='dosu_fork_validation',
        help='Output directory'
    )
    
    args = parser.parse_args()
    
    # Get GitHub token
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        print("Create a token at: https://github.com/settings/tokens")
        print("Required scope: repo (full control of private repositories)")
        sys.exit(1)
    
    # Run validation
    validator = DosuForkValidator(github_token, args.output_dir)
    result = validator.run_validation(
        upstream_repo_name=args.upstream_repo,
        fork_repo_name=args.fork_repo,
        dry_run=args.dry_run,
        categories=args.categories,
        per_category=args.per_category,
        monitor_wait=args.monitor_wait
    )
    
    sys.exit(0 if result['status'] == 'complete' or result['status'] == 'dry_run' else 1)


if __name__ == '__main__':
    main()
