# AI Tools for OpenMC

This directory contains AI-powered tools for automating issue triage and response in the OpenMC repository.

## Contents

- **GitHub Action** - Automated issue responder
- **Python Scripts** - Issue responder and validation tools
- **Jupyter Notebook** - Statistical analysis and visualization
- **Comparison Guide** - Analysis of alternative AI tools
- **Documentation** - Setup guides and examples

## Components

### 1. GitHub Action: AI Issue Responder

**File**: `../../.github/workflows/ai-issue-responder.yml`

A GitHub Action that automatically responds to newly opened issues with:
- Issue classification (bug, feature request, question, etc.)
- Complexity estimation
- Initial guidance and relevant documentation links
- AI-generated analysis (when API keys are configured)

### 2. Issue Responder Script

**File**: `issue_responder.py`

The core Python script that analyzes issues and generates responses.

**Features:**
- Classifies issues by type using heuristics and labels
- Estimates complexity based on content analysis
- Generates template-based or AI-powered responses
- Supports OpenAI and Anthropic AI providers
- Dry-run mode for testing

**Usage:**
```bash
python issue_responder.py \
    --repo openmc-dev/openmc \
    --issue-number 123 \
    --dry-run true \
    --ai-provider none
```

### 3. Validation Script

**File**: `validate_issue_responder.py`

Validates the issue responder against real issues to measure performance.

### 4. Analysis Notebook

**File**: `issue_analysis.ipynb`

Jupyter notebook for statistical and visual analysis of validation results.

**Features:**
- Fetches issues from GitHub repository
- Categorizes and analyzes issue distribution
- Creates test cases with varying complexity
- Measures classification accuracy
- Generates comprehensive validation report
- Provides proof of value for PR submission

**Usage:**
```bash
# Set GitHub token
export GITHUB_TOKEN=your_token_here

# Run validation
python validate_issue_responder.py \
    --repo openmc-dev/openmc \
    --max-issues 100 \
    --output-dir test_results \
    --state all
```

**Features:**
- Categorizes issues by type and complexity
- Creates stratified test cases
- Generates comprehensive validation reports
- Outputs JSON data for further analysis

**Analysis Notebook:**

After running validation, use the Jupyter notebook for visual analysis:

```bash
# Install additional dependencies
pip install pandas matplotlib seaborn jupyter

# Launch Jupyter
jupyter notebook tools/ai/issue_analysis.ipynb
```

The notebook provides:
- Issue type and complexity distribution charts
- Temporal pattern analysis
- Response characteristics visualization
- Classification accuracy metrics
- Statistical summaries and CSV exports

## Setup

### 1. Install Dependencies

```bash
pip install PyGithub openai anthropic requests
```

Or use the requirements file:
```bash
pip install -r tools/ai/requirements.txt
```

### 2. Configure GitHub Token

Create a Personal Access Token with `repo` scope:
https://github.com/settings/tokens

```bash
export GITHUB_TOKEN=your_token_here
```

### 3. (Optional) Configure AI Provider

For enhanced responses, configure an AI provider API key:

**OpenAI:**
```bash
export OPENAI_API_KEY=your_key_here
```

**Anthropic (Claude):**
```bash
export ANTHROPIC_API_KEY=your_key_here
```

## GitHub Action Setup

To enable the automated issue responder:

### 1. Add Repository Secrets

In your GitHub repository settings, add:
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` (optional, for AI-powered responses)

The `GITHUB_TOKEN` is automatically provided by GitHub Actions.

### 2. Enable the Workflow

The workflow is triggered automatically when:
- A new issue is opened
- Manually via workflow_dispatch

### 3. Test the Workflow

You can test manually:
1. Go to Actions tab in your repository
2. Select "AI Issue Responder" workflow
3. Click "Run workflow"
4. Enter an issue number to test

## Validation Workflow

To validate the AI Issue Responder before submitting a PR:

### 1. Run Validation Script

```bash
cd /path/to/openmc
python tools/ai/validate_issue_responder.py \
    --repo openmc-dev/openmc \
    --max-issues 100 \
    --output-dir test_results
```

### 2. Review Results

The script generates:
- `test_results/validation_results_<timestamp>.json` - Detailed metrics
- `test_results/validation_report_<timestamp>.md` - Human-readable report
- `test_results/validation_results_latest.json` - Latest results
- `test_results/validation_report_latest.md` - Latest report

### 3. Use in PR Description

Include the validation report in your PR to demonstrate:
- Classification accuracy on real issues
- Processing performance metrics
- Value proposition for the OpenMC project
- Proof of concept with test data

## Running in GitHub Codespaces

The validation script works perfectly in GitHub Codespaces:

```bash
# 1. Open codespace for openmc repository

# 2. Install dependencies
pip install -r tools/ai/requirements.txt

# 3. Set GitHub token (automatically available in codespace)
export GITHUB_TOKEN=$GITHUB_TOKEN

# 4. Run validation
python tools/ai/validate_issue_responder.py

# 5. View results
cat test_results/validation_report_latest.md
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Issue Created                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              GitHub Action: ai-issue-responder.yml           │
│  • Triggered on issue open                                   │
│  • Checks out repository                                     │
│  • Sets up Python environment                                │
│  • Runs issue_responder.py                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              IssueAnalyzer (issue_responder.py)              │
│  1. Fetch issue details via GitHub API                       │
│  2. Classify issue type (bug/feature/question/etc.)          │
│  3. Estimate complexity (trivial/simple/moderate/complex)    │
│  4. Generate response:                                       │
│     • AI-powered (if API key available)                      │
│     • Template-based (fallback)                              │
│  5. Format response with metadata                            │
│  6. Post comment to issue                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Comment Posted to GitHub Issue                  │
│  • Automated analysis and classification                     │
│  • Initial guidance and suggestions                          │
│  • Links to relevant documentation                           │
│  • Note that human will follow up                            │
└─────────────────────────────────────────────────────────────┘
```

## Issue Classification

The responder uses multiple signals to classify issues:

### Type Classification
- **Bug**: Labels contain "bug", title contains "error", "crash", "bug"
- **Feature**: Labels contain "feature", "enhancement"
- **Question**: Title contains "how to", "question"
- **Documentation**: Labels contain "documentation", "docs"
- **Other**: Doesn't match above categories

### Complexity Estimation
- **Trivial**: < 50 words, or keywords like "typo", "simple"
- **Simple**: 50-150 words, straightforward description
- **Moderate**: 150-300 words (default)
- **Complex**: > 300 words, or mentions "segfault", "memory", "crash"
- **Very Complex**: Contains "architecture", "redesign", "breaking"

## Response Templates

The responder provides context-aware guidance:

- **Bugs**: Steps to reproduce checklist, environment details, debugging suggestions
- **Features**: Contribution guidelines, API design considerations, forum discussion suggestion
- **Questions**: Links to documentation, examples, forum
- **Other**: General next steps and resources

## Performance Metrics

Expected performance (from validation):
- **Processing time**: < 5 seconds per issue
- **Classification accuracy**: > 80% for clear cases
- **Response quality**: Helpful initial guidance, reduces maintainer burden

## Limitations

1. **No Deep Understanding**: Classification is heuristic-based, not semantic
2. **AI API Required**: Best responses require OpenAI or Anthropic API access
3. **English Only**: Assumes issues are written in English
4. **No Context**: Doesn't consider related issues or PR history
5. **Template Limitations**: Fallback responses are generic

## Future Enhancements

Possible improvements:
1. **Vector search** over OpenMC documentation for better guidance
2. **Fine-tuned model** on OpenMC-specific issues
3. **Related issue detection** to link to similar problems
4. **Automatic labeling** based on classification
5. **Sentiment analysis** to prioritize urgent issues
6. **Code snippet analysis** to suggest fixes

## Contributing

To improve the AI tools:

1. **Enhance classification**: Add more heuristics or patterns
2. **Improve templates**: Make responses more specific to OpenMC
3. **Add test cases**: Include edge cases in validation
4. **Extend validation**: Add more metrics and analysis
5. **Documentation**: Improve examples and usage instructions

## Comparison with Other AI Tools

See `AI_TOOLS_COMPARISON.md` for a detailed comparison with:
- AI Assessment Comment Labeler (GitHub Marketplace)
- Dosu.dev (Advanced AI support bot)
- Block/Goose (Developer AI assistant)

The comparison covers:
- Codebase context building capabilities
- Issue triage and resolution features
- Cost and pricing models
- Suitability for OpenMC
- Trade-offs and recommendations

## License

These tools are part of the OpenMC project and follow the same MIT/X license.
