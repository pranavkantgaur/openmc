#!/usr/bin/env python3
"""
AI-powered GitHub issue responder for OpenMC.

This script analyzes GitHub issues and provides AI-generated responses with:
- Issue classification (bug, feature request, question)
- Complexity assessment
- Suggested resolution or guidance
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    from github import Github
    from github.Issue import Issue
except ImportError:
    print("Error: PyGithub not installed. Run: pip install PyGithub")
    sys.exit(1)


class IssueAnalyzer:
    """Analyzes GitHub issues using AI to provide intelligent responses."""
    
    ISSUE_TYPES = {
        'bug': 'Bug Report',
        'feature': 'Feature Request',
        'question': 'Question/Support',
        'documentation': 'Documentation',
        'enhancement': 'Enhancement',
        'other': 'Other'
    }
    
    COMPLEXITY_LEVELS = {
        'trivial': 'Trivial (< 1 hour)',
        'simple': 'Simple (1-4 hours)',
        'moderate': 'Moderate (1-3 days)',
        'complex': 'Complex (1-2 weeks)',
        'very_complex': 'Very Complex (> 2 weeks)'
    }
    
    def __init__(self, github_token: str, ai_api_key: Optional[str] = None, ai_provider: str = 'openai'):
        """
        Initialize the issue analyzer.
        
        Parameters
        ----------
        github_token : str
            GitHub personal access token
        ai_api_key : str, optional
            API key for AI provider (OpenAI or Anthropic)
        ai_provider : str
            AI provider to use ('openai' or 'anthropic')
        """
        self.github = Github(github_token)
        self.ai_api_key = ai_api_key
        self.ai_provider = ai_provider
        
        # Initialize AI client if API key is provided
        self.ai_client = None
        if ai_api_key:
            if ai_provider == 'openai':
                try:
                    import openai
                    self.ai_client = openai.OpenAI(api_key=ai_api_key)
                except ImportError:
                    print("Warning: openai package not installed")
            elif ai_provider == 'anthropic':
                try:
                    import anthropic
                    self.ai_client = anthropic.Anthropic(api_key=ai_api_key)
                except ImportError:
                    print("Warning: anthropic package not installed")
    
    def classify_issue(self, issue: Issue) -> Tuple[str, str, str]:
        """
        Classify an issue by type and complexity.
        
        Parameters
        ----------
        issue : Issue
            GitHub issue object
        
        Returns
        -------
        tuple
            (issue_type, complexity, reasoning)
        """
        title = issue.title.lower()
        body = (issue.body or "").lower()
        labels = [label.name.lower() for label in issue.labels]
        
        # Determine issue type
        issue_type = 'other'
        if 'bug' in labels or 'bug' in title or 'error' in title or 'crash' in title:
            issue_type = 'bug'
        elif 'feature' in labels or 'enhancement' in labels or 'feature request' in title:
            issue_type = 'feature'
        elif 'question' in title or 'how to' in title or 'how do i' in body:
            issue_type = 'question'
        elif 'documentation' in labels or 'docs' in labels or 'documentation' in title:
            issue_type = 'documentation'
        
        # Estimate complexity based on issue content
        complexity = 'moderate'
        reasoning = []
        
        # Simple heuristics for complexity
        word_count = len(body.split())
        if word_count < 50:
            complexity = 'simple'
            reasoning.append("Brief description suggests straightforward issue")
        elif word_count > 300:
            complexity = 'complex'
            reasoning.append("Detailed description suggests complex issue")
        
        # Check for specific indicators
        if 'segfault' in body or 'crash' in body or 'memory' in body:
            complexity = 'complex'
            reasoning.append("Memory/crash issues typically require deeper investigation")
        
        if 'simple' in title or 'quick' in title or 'typo' in title:
            complexity = 'trivial'
            reasoning.append("Title indicates trivial fix")
        
        if 'architecture' in body or 'redesign' in body or 'breaking' in body:
            complexity = 'very_complex'
            reasoning.append("Architectural changes require significant effort")
        
        reasoning_text = "; ".join(reasoning) if reasoning else "Based on issue content analysis"
        
        return issue_type, complexity, reasoning_text
    
    def generate_response_with_ai(self, issue: Issue, issue_type: str, complexity: str) -> str:
        """
        Generate a response using AI.
        
        Parameters
        ----------
        issue : Issue
            GitHub issue object
        issue_type : str
            Classified issue type
        complexity : str
            Estimated complexity
        
        Returns
        -------
        str
            AI-generated response
        """
        if not self.ai_client:
            return self._generate_fallback_response(issue, issue_type, complexity)
        
        prompt = self._build_ai_prompt(issue, issue_type, complexity)
        
        try:
            if self.ai_provider == 'openai':
                response = self.ai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "You are an expert in OpenMC, a Monte Carlo particle transport code. Provide helpful, accurate responses to user issues."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                return response.choices[0].message.content
            elif self.ai_provider == 'anthropic':
                message = self.ai_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return message.content[0].text
        except Exception as e:
            print(f"Warning: AI generation failed: {e}")
            return self._generate_fallback_response(issue, issue_type, complexity)
    
    def _build_ai_prompt(self, issue: Issue, issue_type: str, complexity: str) -> str:
        """Build a prompt for the AI model."""
        return f"""Analyze this OpenMC GitHub issue and provide a helpful response:

**Issue Type**: {self.ISSUE_TYPES.get(issue_type, 'Other')}
**Estimated Complexity**: {self.COMPLEXITY_LEVELS.get(complexity, 'Unknown')}

**Title**: {issue.title}

**Description**:
{issue.body or 'No description provided'}

**Labels**: {', '.join([label.name for label in issue.labels]) or 'None'}

Please provide:
1. A brief analysis of the issue
2. If it's a bug: suggest potential causes and debugging steps
3. If it's a feature request: assess feasibility and suggest implementation approach
4. If it's a question: provide guidance or point to relevant documentation
5. Any relevant code examples or references to OpenMC documentation

Keep the response concise, professional, and actionable. Reference specific OpenMC components, documentation, or examples where relevant.
"""
    
    def _generate_fallback_response(self, issue: Issue, issue_type: str, complexity: str) -> str:
        """Generate a template-based response when AI is not available."""
        issue_type_name = self.ISSUE_TYPES.get(issue_type, 'Other')
        complexity_name = self.COMPLEXITY_LEVELS.get(complexity, 'Unknown')
        
        response = f"""Thank you for opening this issue!

## Automated Analysis

**Issue Type**: {issue_type_name}
**Estimated Complexity**: {complexity_name}

"""
        
        if issue_type == 'bug':
            response += """### Bug Report Guidelines

To help us investigate this bug, please ensure you've provided:

1. **Steps to reproduce**: Clear instructions to reproduce the issue
2. **Expected behavior**: What you expected to happen
3. **Actual behavior**: What actually happened
4. **Environment details**:
   - OpenMC version
   - Operating system
   - Installation method (pip, conda, from source)
   - Nuclear data library being used

### Initial Suggestions

1. Check if this is a known issue in the [documentation](https://docs.openmc.org)
2. Verify you're using the latest version of OpenMC
3. Try running with `openmc --version` to confirm installation
4. Check if the issue persists with different nuclear data libraries

If you can provide a minimal reproducible example, that would greatly help in debugging.
"""
        
        elif issue_type == 'feature':
            response += """### Feature Request

Thank you for suggesting this enhancement! The OpenMC development team will review this proposal.

### Considerations

When evaluating feature requests, we typically consider:

1. **Use case**: How would this benefit OpenMC users?
2. **API design**: How would this fit into existing OpenMC APIs?
3. **Backward compatibility**: Would this break existing code?
4. **Maintenance burden**: What's the long-term maintenance cost?

### How to Help

If you're interested in contributing this feature:

1. Review the [contributing guidelines](https://docs.openmc.org/en/latest/devguide/index.html)
2. Consider opening a discussion on the [forum](https://openmc.discourse.group) first
3. If you'd like to implement it yourself, feel free to open a draft PR for feedback

We appreciate community contributions and would be happy to guide you through the process!
"""
        
        elif issue_type == 'question':
            response += """### Question/Support

For general usage questions, we recommend:

1. **Documentation**: Check the [OpenMC User's Guide](https://docs.openmc.org/en/stable/usersguide/index.html)
2. **Examples**: Browse [example notebooks](https://docs.openmc.org/en/stable/examples/index.html)
3. **Forum**: Post on the [OpenMC Discourse forum](https://openmc.discourse.group) for community support
4. **API Reference**: Review the [Python API documentation](https://docs.openmc.org/en/stable/pythonapi/index.html)

### Relevant Resources

Depending on your specific question, these resources might help:

- **Installation**: [Installation Guide](https://docs.openmc.org/en/stable/usersguide/install.html)
- **Getting Started**: [Quickstart Guide](https://docs.openmc.org/en/stable/quickinstall.html)
- **Examples**: [Gallery of Examples](https://docs.openmc.org/en/stable/examples/index.html)

If your question remains unanswered after checking these resources, please let us know and we'll do our best to help!
"""
        
        else:
            response += """### Next Steps

A member of the OpenMC development team will review this issue and respond accordingly.

In the meantime, you can:

1. Provide additional context or information that might be helpful
2. Check the [documentation](https://docs.openmc.org) for related information
3. Search [existing issues](https://github.com/openmc-dev/openmc/issues) for similar topics
4. Join the discussion on the [OpenMC forum](https://openmc.discourse.group)

Thank you for your contribution to the OpenMC project!
"""
        
        return response
    
    def format_response(self, issue: Issue, issue_type: str, complexity: str, 
                       ai_response: str, reasoning: str) -> str:
        """
        Format the complete response with metadata.
        
        Parameters
        ----------
        issue : Issue
            GitHub issue object
        issue_type : str
            Classified issue type
        complexity : str
            Estimated complexity
        ai_response : str
            AI-generated response content
        reasoning : str
            Classification reasoning
        
        Returns
        -------
        str
            Formatted response
        """
        header = f"""<!--
This is an automated response generated by the OpenMC AI Issue Responder.
Classification: {self.ISSUE_TYPES.get(issue_type, 'Other')} | Complexity: {self.COMPLEXITY_LEVELS.get(complexity, 'Unknown')}
Reasoning: {reasoning}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
-->

"""
        
        footer = """

---

*This response was automatically generated. A human maintainer will review and follow up as needed.*

*If you believe this classification is incorrect or the response is not helpful, please let us know!*
"""
        
        return header + ai_response + footer
    
    def process_issue(self, repo_name: str, issue_number: int, dry_run: bool = True) -> Dict:
        """
        Process a GitHub issue and generate a response.
        
        Parameters
        ----------
        repo_name : str
            Repository name (e.g., 'openmc-dev/openmc')
        issue_number : int
            Issue number to process
        dry_run : bool
            If True, don't actually post the comment
        
        Returns
        -------
        dict
            Processing results
        """
        try:
            repo = self.github.get_repo(repo_name)
            issue = repo.get_issue(issue_number)
            
            print(f"Processing issue #{issue_number}: {issue.title}")
            
            # Classify the issue
            issue_type, complexity, reasoning = self.classify_issue(issue)
            print(f"  Classification: {issue_type} (complexity: {complexity})")
            print(f"  Reasoning: {reasoning}")
            
            # Generate AI response
            print(f"  Generating response...")
            ai_response = self.generate_response_with_ai(issue, issue_type, complexity)
            
            # Format complete response
            full_response = self.format_response(issue, issue_type, complexity, ai_response, reasoning)
            
            if dry_run:
                print("\n" + "="*80)
                print("DRY RUN - Response that would be posted:")
                print("="*80)
                print(full_response)
                print("="*80 + "\n")
            else:
                # Post the comment
                comment = issue.create_comment(full_response)
                print(f"  ✓ Posted comment: {comment.html_url}")
            
            return {
                'success': True,
                'issue_number': issue_number,
                'issue_type': issue_type,
                'complexity': complexity,
                'reasoning': reasoning,
                'response_length': len(full_response),
                'dry_run': dry_run
            }
            
        except Exception as e:
            print(f"Error processing issue #{issue_number}: {e}")
            return {
                'success': False,
                'issue_number': issue_number,
                'error': str(e),
                'dry_run': dry_run
            }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AI-powered GitHub issue responder for OpenMC'
    )
    parser.add_argument(
        '--repo',
        required=True,
        help='Repository name (e.g., openmc-dev/openmc)'
    )
    parser.add_argument(
        '--issue-number',
        type=int,
        required=True,
        help='Issue number to process'
    )
    parser.add_argument(
        '--dry-run',
        type=lambda x: x.lower() == 'true',
        default=True,
        help='Dry run mode (true/false)'
    )
    parser.add_argument(
        '--ai-provider',
        choices=['openai', 'anthropic', 'none'],
        default='none',
        help='AI provider to use'
    )
    
    args = parser.parse_args()
    
    # Get credentials from environment
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    ai_api_key = None
    if args.ai_provider == 'openai':
        ai_api_key = os.environ.get('OPENAI_API_KEY')
        if not ai_api_key:
            print("Warning: OPENAI_API_KEY not set, using fallback responses")
    elif args.ai_provider == 'anthropic':
        ai_api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not ai_api_key:
            print("Warning: ANTHROPIC_API_KEY not set, using fallback responses")
    
    # Process the issue
    analyzer = IssueAnalyzer(github_token, ai_api_key, args.ai_provider)
    result = analyzer.process_issue(args.repo, args.issue_number, args.dry_run)
    
    # Output result as JSON for GitHub Actions
    print(json.dumps(result, indent=2))
    
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
