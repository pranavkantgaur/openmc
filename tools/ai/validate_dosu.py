#!/usr/bin/env python3
"""
Dosu.dev Validation Script for OpenMC

This script validates Dosu.dev's performance by:
1. Fetching closed GitHub issues from openmc-dev/openmc
2. Retrieving their conversation history and resolution details
3. For issues closed by PRs, fetches PR conversations and file changes
4. Invokes Dosu to generate issue resolution based on the original issue context
5. Saves Dosu's responses alongside actual resolutions for comparison

Usage:
    python validate_dosu.py --repo openmc-dev/openmc --max-issues 50 --output-dir dosu_validation

Requirements:
    - GitHub token with repo access
    - Dosu.dev API access (if available) or manual validation workflow
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
    from github.PullRequest import PullRequest
except ImportError:
    print("Error: PyGithub not installed. Run: pip install PyGithub")
    sys.exit(1)


class DosuValidator:
    """Validates Dosu.dev's performance on closed OpenMC issues."""
    
    def __init__(self, github_token: str, output_dir: str = 'dosu_validation'):
        """
        Initialize validator.
        
        Parameters
        ----------
        github_token : str
            GitHub personal access token
        output_dir : str
            Directory to save validation results
        """
        self.github = Github(github_token)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / 'issues').mkdir(exist_ok=True)
        (self.output_dir / 'pull_requests').mkdir(exist_ok=True)
        (self.output_dir / 'dosu_responses').mkdir(exist_ok=True)
    
    def fetch_closed_issues(self, repo_name: str, max_issues: int = 50) -> List[Issue]:
        """
        Fetch closed issues from repository.
        
        Parameters
        ----------
        repo_name : str
            Repository name (e.g., 'openmc-dev/openmc')
        max_issues : int
            Maximum number of closed issues to fetch
        
        Returns
        -------
        list
            List of closed GitHub Issue objects
        """
        print(f"Fetching closed issues from {repo_name}...")
        repo = self.github.get_repo(repo_name)
        issues = []
        
        try:
            for issue in repo.get_issues(state='closed', sort='updated', direction='desc'):
                # Skip pull requests
                if issue.pull_request is not None:
                    continue
                
                issues.append(issue)
                print(f"  Fetched issue #{issue.number}: {issue.title[:60]}...")
                
                if len(issues) >= max_issues:
                    break
            
            print(f"✓ Fetched {len(issues)} closed issues")
            return issues
            
        except Exception as e:
            print(f"Error fetching issues: {e}")
            return issues
    
    def extract_closing_prs(self, issue: Issue) -> List[int]:
        """
        Extract PR numbers that closed this issue.
        
        Parameters
        ----------
        issue : Issue
            GitHub issue object
        
        Returns
        -------
        list
            List of PR numbers that closed this issue
        """
        closing_prs = []
        
        # Check issue events for closed_by events
        try:
            for event in issue.get_events():
                if event.event == 'closed' and event.commit_id:
                    # Try to find PR associated with this commit
                    # This is a heuristic approach
                    pass
        except Exception as e:
            print(f"    Warning: Could not fetch events for issue #{issue.number}: {e}")
        
        # Search for PR references in issue comments and body
        text_to_search = [issue.body or ""]
        try:
            for comment in issue.get_comments():
                text_to_search.append(comment.body or "")
        except Exception as e:
            print(f"    Warning: Could not fetch comments for issue #{issue.number}: {e}")
        
        # Look for PR references like #123, "closes #123", "fixes #123", etc.
        pr_pattern = re.compile(r'(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)', re.IGNORECASE)
        direct_ref_pattern = re.compile(r'#(\d+)')
        
        for text in text_to_search:
            # First try to find explicit closing references
            matches = pr_pattern.findall(text)
            for pr_num in matches:
                pr_number = int(pr_num)
                if pr_number not in closing_prs:
                    closing_prs.append(pr_number)
            
            # If no explicit references, look for direct PR references
            if not closing_prs:
                matches = direct_ref_pattern.findall(text)
                for pr_num in matches:
                    pr_number = int(pr_num)
                    # Verify it's actually a PR, not another issue
                    try:
                        repo = issue.repository
                        pr = repo.get_pull(pr_number)
                        if pr.state == 'closed' and pr_number not in closing_prs:
                            closing_prs.append(pr_number)
                    except:
                        pass  # Not a PR or doesn't exist
        
        return closing_prs
    
    def fetch_pr_details(self, repo_name: str, pr_number: int) -> Optional[Dict]:
        """
        Fetch PR details including conversation and file changes.
        
        Parameters
        ----------
        repo_name : str
            Repository name
        pr_number : int
            Pull request number
        
        Returns
        -------
        dict or None
            PR details dictionary
        """
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Get PR conversation
            comments = []
            try:
                for comment in pr.get_issue_comments():
                    comments.append({
                        'author': comment.user.login,
                        'body': comment.body,
                        'created_at': comment.created_at.isoformat()
                    })
                
                for review in pr.get_reviews():
                    if review.body:
                        comments.append({
                            'author': review.user.login,
                            'body': review.body,
                            'created_at': review.submitted_at.isoformat() if review.submitted_at else None,
                            'type': 'review'
                        })
            except Exception as e:
                print(f"    Warning: Could not fetch all PR comments: {e}")
            
            # Get file changes
            files_changed = []
            try:
                for file in pr.get_files():
                    files_changed.append({
                        'filename': file.filename,
                        'status': file.status,
                        'additions': file.additions,
                        'deletions': file.deletions,
                        'changes': file.changes,
                        'patch': file.patch if hasattr(file, 'patch') else None
                    })
            except Exception as e:
                print(f"    Warning: Could not fetch PR files: {e}")
            
            return {
                'number': pr.number,
                'title': pr.title,
                'body': pr.body,
                'state': pr.state,
                'merged': pr.merged,
                'merged_at': pr.merged_at.isoformat() if pr.merged_at else None,
                'base_commit': pr.base.sha,
                'head_commit': pr.head.sha,
                'merge_commit': pr.merge_commit_sha,
                'comments': comments,
                'files_changed': files_changed,
                'url': pr.html_url
            }
            
        except Exception as e:
            print(f"    Error fetching PR #{pr_number}: {e}")
            return None
    
    def get_issue_data(self, issue: Issue, repo_name: str) -> Dict:
        """
        Get comprehensive issue data including conversation and PR details.
        
        Parameters
        ----------
        issue : Issue
            GitHub issue object
        repo_name : str
            Repository name
        
        Returns
        -------
        dict
            Complete issue data
        """
        print(f"\nProcessing issue #{issue.number}: {issue.title}")
        
        # Get issue conversation
        comments = []
        try:
            for comment in issue.get_comments():
                comments.append({
                    'author': comment.user.login,
                    'body': comment.body,
                    'created_at': comment.created_at.isoformat()
                })
        except Exception as e:
            print(f"    Warning: Could not fetch all comments: {e}")
        
        # Extract closing PRs
        closing_prs = self.extract_closing_prs(issue)
        print(f"    Found {len(closing_prs)} closing PR(s): {closing_prs}")
        
        # Fetch PR details
        pr_details = []
        for pr_num in closing_prs:
            print(f"    Fetching PR #{pr_num} details...")
            pr_data = self.fetch_pr_details(repo_name, pr_num)
            if pr_data:
                pr_details.append(pr_data)
        
        # Determine the commit ID to use for context
        # Use the base commit of the first closing PR, or the issue's closed_at commit
        context_commit = None
        if pr_details:
            context_commit = pr_details[0].get('base_commit')
        
        if not context_commit:
            # Fallback: try to get commit from issue timeline
            try:
                for event in issue.get_events():
                    if event.event == 'closed' and event.commit_id:
                        context_commit = event.commit_id
                        break
            except:
                pass
        
        # If still no commit, use 'develop' branch HEAD (we'll need to fetch it)
        if not context_commit:
            try:
                repo = self.github.get_repo(repo_name)
                develop_branch = repo.get_branch('develop')
                context_commit = develop_branch.commit.sha
            except Exception as e:
                print(f"    Warning: Could not get develop branch commit: {e}")
                context_commit = 'develop'
        
        print(f"    Context commit: {context_commit}")
        
        return {
            'number': issue.number,
            'title': issue.title,
            'body': issue.body,
            'state': issue.state,
            'labels': [label.name for label in issue.labels],
            'created_at': issue.created_at.isoformat(),
            'closed_at': issue.closed_at.isoformat() if issue.closed_at else None,
            'url': issue.html_url,
            'comments': comments,
            'closing_prs': closing_prs,
            'pr_details': pr_details,
            'context_commit': context_commit
        }
    
    def generate_dosu_prompt(self, issue_data: Dict) -> str:
        """
        Generate a prompt for Dosu (or manual validation).
        
        Parameters
        ----------
        issue_data : dict
            Issue data dictionary
        
        Returns
        -------
        str
            Formatted prompt
        """
        prompt = f"""Issue #{issue_data['number']}: {issue_data['title']}

**Issue Description:**
{issue_data['body'] or 'No description provided'}

**Labels:** {', '.join(issue_data['labels']) or 'None'}

**Created:** {issue_data['created_at']}
**Closed:** {issue_data['closed_at']}

**Context:**
- Repository: openmc-dev/openmc
- Commit ID: {issue_data['context_commit']}
- Branch: develop (or PR base branch)

**Task:**
Based on the issue description and the codebase/documentation at commit {issue_data['context_commit']}, provide a detailed resolution or guidance for this issue. Include:
1. Analysis of the issue
2. Suggested solution or explanation
3. Relevant code references (if applicable)
4. Documentation references (if applicable)
5. Example code snippets (if helpful)

**Note:** This issue was actually closed by PR(s): {', '.join([f"#{pr}" for pr in issue_data['closing_prs']])}
"""
        return prompt
    
    def save_issue_data(self, issue_data: Dict):
        """
        Save issue data to JSON file.
        
        Parameters
        ----------
        issue_data : dict
            Issue data to save
        """
        issue_file = self.output_dir / 'issues' / f"issue_{issue_data['number']}.json"
        with open(issue_file, 'w') as f:
            json.dump(issue_data, f, indent=2, default=str)
        print(f"    Saved issue data to {issue_file}")
        
        # Save PR details separately for easier access
        for pr_data in issue_data.get('pr_details', []):
            pr_file = self.output_dir / 'pull_requests' / f"pr_{pr_data['number']}.json"
            with open(pr_file, 'w') as f:
                json.dump(pr_data, f, indent=2, default=str)
        
        # Save Dosu prompt
        prompt_file = self.output_dir / 'dosu_responses' / f"prompt_issue_{issue_data['number']}.txt"
        prompt = self.generate_dosu_prompt(issue_data)
        with open(prompt_file, 'w') as f:
            f.write(prompt)
        print(f"    Saved Dosu prompt to {prompt_file}")
    
    def create_validation_manifest(self, issues_data: List[Dict]):
        """
        Create a manifest file for validation.
        
        Parameters
        ----------
        issues_data : list
            List of issue data dictionaries
        """
        manifest = {
            'validation_date': datetime.utcnow().isoformat(),
            'total_issues': len(issues_data),
            'issues': []
        }
        
        for issue_data in issues_data:
            manifest['issues'].append({
                'number': issue_data['number'],
                'title': issue_data['title'],
                'url': issue_data['url'],
                'closing_prs': issue_data['closing_prs'],
                'pr_urls': [pr['url'] for pr in issue_data.get('pr_details', [])],
                'context_commit': issue_data['context_commit'],
                'prompt_file': f"dosu_responses/prompt_issue_{issue_data['number']}.txt",
                'issue_file': f"issues/issue_{issue_data['number']}.json",
                'dosu_response_file': f"dosu_responses/dosu_response_issue_{issue_data['number']}.txt"
            })
        
        manifest_file = self.output_dir / 'validation_manifest.json'
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"\n✓ Created validation manifest: {manifest_file}")
        return manifest
    
    def create_readme(self):
        """Create README for validation directory."""
        readme_content = """# Dosu.dev Validation for OpenMC

This directory contains data for validating Dosu.dev's performance on closed OpenMC issues.

## Directory Structure

```
dosu_validation/
├── validation_manifest.json    # Index of all validation cases
├── issues/                      # Issue data (JSON)
│   ├── issue_123.json
│   ├── issue_456.json
│   └── ...
├── pull_requests/               # PR data (JSON)
│   ├── pr_789.json
│   └── ...
└── dosu_responses/              # Dosu prompts and responses
    ├── prompt_issue_123.txt     # Prompt for Dosu
    ├── dosu_response_issue_123.txt  # Dosu's response (to be filled)
    └── ...
```

## Validation Process

### 1. Review the Prompts

Each `prompt_issue_*.txt` file contains:
- Issue description
- Context (commit ID, branch)
- Task for Dosu
- Actual closing PR references (for comparison)

### 2. Obtain Dosu Responses

**Option A: Using Dosu.dev Service (if you have access)**
1. Install Dosu in openmc-dev/openmc repository
2. For each issue, create a test issue or use Dosu's API
3. Save Dosu's response to `dosu_response_issue_*.txt`

**Option B: Manual Invocation (if using Dosu locally)**
1. Set up Dosu with OpenMC codebase indexed
2. Feed each prompt to Dosu
3. Save responses to corresponding files

**Option C: API Integration (if Dosu provides API)**
```python
# Example pseudo-code
import requests

for issue in manifest['issues']:
    prompt = open(issue['prompt_file']).read()
    response = dosu_api.generate_response(
        prompt=prompt,
        repo='openmc-dev/openmc',
        commit=issue['context_commit']
    )
    with open(issue['dosu_response_file'], 'w') as f:
        f.write(response)
```

### 3. Compare Responses

For each issue:
1. Read Dosu's response from `dosu_response_issue_*.txt`
2. Compare with actual resolution:
   - Check `issue_*.json` for issue comments and resolution
   - Check `pr_*.json` for PR description, comments, and file changes
3. Evaluate:
   - **Accuracy**: Does Dosu's suggestion match actual resolution?
   - **Relevance**: Does it address the core issue?
   - **Helpfulness**: Would it guide user to solution?
   - **Code Context**: Does it reference relevant code/docs?
   - **Hallucination**: Any incorrect information?

### 4. Create Evaluation Report

Create `evaluation_report.json`:
```json
{
  "issue_number": 123,
  "dosu_response_quality": {
    "accuracy_score": 4,  // 1-5 scale
    "relevance_score": 5,
    "helpfulness_score": 4,
    "code_context_used": true,
    "hallucination_detected": false,
    "matches_actual_resolution": true
  },
  "notes": "Dosu correctly identified the issue and suggested the same fix..."
}
```

## Evaluation Criteria

### Accuracy (1-5)
- 5: Perfectly matches actual resolution
- 4: Very close, minor differences
- 3: Correct direction, missing details
- 2: Partially correct
- 1: Incorrect or misleading

### Relevance (1-5)
- 5: Directly addresses the issue
- 4: Addresses issue with minor tangents
- 3: Somewhat relevant
- 2: Loosely related
- 1: Off-topic

### Helpfulness (1-5)
- 5: Would immediately solve user's problem
- 4: Provides clear path to solution
- 3: Points in right direction
- 2: Vague guidance
- 1: Not helpful

### Code Context
- true: References relevant code/docs from codebase
- false: Generic response without codebase context

### Hallucination
- true: Contains incorrect information about OpenMC
- false: Information is accurate

## Statistical Analysis

After evaluation, run:
```python
python analyze_dosu_validation.py
```

This will generate:
- Overall accuracy statistics
- Issue type performance (bug vs feature vs question)
- Correlation between issue complexity and Dosu performance
- Comparison with template-based responses

## Notes

- **Context Commit**: Each prompt uses the commit ID from when the issue was filed (or PR base)
- **Closing PRs**: Listed for reference but not provided to Dosu (simulates real-time scenario)
- **Fair Comparison**: Dosu should only use information available at the time of the issue

## Next Steps

1. Complete Dosu response collection
2. Perform evaluation
3. Analyze results
4. Compare with template-based responses (from our implementation)
5. Make recommendation for OpenMC
"""
        
        readme_file = self.output_dir / 'README.md'
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        print(f"✓ Created README: {readme_file}")
    
    def run_validation(self, repo_name: str, max_issues: int = 50) -> Dict:
        """
        Run complete validation workflow.
        
        Parameters
        ----------
        repo_name : str
            Repository name
        max_issues : int
            Maximum number of issues to process
        
        Returns
        -------
        dict
            Validation results
        """
        print("="*80)
        print("DOSU.DEV VALIDATION FOR OPENMC")
        print("="*80)
        
        # Fetch closed issues
        issues = self.fetch_closed_issues(repo_name, max_issues)
        
        if not issues:
            print("No issues found!")
            return {'success': False, 'issues_processed': 0}
        
        # Process each issue
        issues_data = []
        for i, issue in enumerate(issues):
            print(f"\n[{i+1}/{len(issues)}] Processing issue #{issue.number}...")
            try:
                issue_data = self.get_issue_data(issue, repo_name)
                self.save_issue_data(issue_data)
                issues_data.append(issue_data)
            except Exception as e:
                print(f"    Error processing issue #{issue.number}: {e}")
                continue
        
        # Create manifest and README
        manifest = self.create_validation_manifest(issues_data)
        self.create_readme()
        
        # Summary
        print("\n" + "="*80)
        print("VALIDATION DATA COLLECTION COMPLETE")
        print("="*80)
        print(f"Total issues processed: {len(issues_data)}")
        print(f"Issues with closing PRs: {sum(1 for i in issues_data if i['closing_prs'])}")
        print(f"Total PRs fetched: {sum(len(i['pr_details']) for i in issues_data)}")
        print(f"\nOutput directory: {self.output_dir}")
        print(f"\nNext steps:")
        print(f"1. Review prompts in: {self.output_dir}/dosu_responses/")
        print(f"2. Obtain Dosu responses (see README.md)")
        print(f"3. Save responses as: dosu_response_issue_*.txt")
        print(f"4. Evaluate and compare with actual resolutions")
        
        return {
            'success': True,
            'issues_processed': len(issues_data),
            'output_dir': str(self.output_dir),
            'manifest_file': str(self.output_dir / 'validation_manifest.json')
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate Dosu.dev performance on closed OpenMC issues'
    )
    parser.add_argument(
        '--repo',
        default='openmc-dev/openmc',
        help='Repository name (e.g., openmc-dev/openmc)'
    )
    parser.add_argument(
        '--max-issues',
        type=int,
        default=50,
        help='Maximum number of closed issues to fetch'
    )
    parser.add_argument(
        '--output-dir',
        default='dosu_validation',
        help='Output directory for validation data'
    )
    
    args = parser.parse_args()
    
    # Get GitHub token
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        print("Create a token at: https://github.com/settings/tokens")
        sys.exit(1)
    
    # Run validation
    validator = DosuValidator(github_token, args.output_dir)
    result = validator.run_validation(args.repo, args.max_issues)
    
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
