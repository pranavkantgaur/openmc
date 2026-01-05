# AI Tools for OpenMC

This directory contains AI-powered tools for automating issue triage and response in the OpenMC repository.

## Contents

- **GitHub Action** - Automated issue responder
- **Python Scripts** - Issue responder and validation tools
- **Jupyter Notebook** - Statistical analysis and visualization
- **Comparison Guide** - Analysis of alternative AI tools
- **Dosu Validation** - Tools to validate Dosu.dev performance
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

### 5. Dosu.dev Validation Tool

**File**: `validate_dosu.py`

Validates Dosu.dev's performance on closed OpenMC issues.

**Purpose**: Before deploying Dosu.dev for OpenMC, validate its effectiveness by testing on historical closed issues.

**Features:**
- Fetches closed issues with complete conversation history
- Extracts closing PR details (conversations, file changes)
- Identifies the commit context for codebase indexing
- Generates prompts for Dosu evaluation
- Creates structured validation dataset

**Usage:**
```bash
# Set GitHub token
export GITHUB_TOKEN=your_token_here

# Run validation data collection
python validate_dosu.py \
    --repo openmc-dev/openmc \
    --max-issues 50 \
    --output-dir dosu_validation
```

**Output Structure:**
```
dosu_validation/
├── validation_manifest.json    # Index of all validation cases
├── issues/                      # Issue data (JSON)
│   ├── issue_123.json
│   └── ...
├── pull_requests/               # PR data (JSON)
│   ├── pr_789.json
│   └── ...
└── dosu_responses/              # Dosu prompts and responses
    ├── prompt_issue_123.txt     # Prompt for Dosu
    └── dosu_response_issue_123.txt  # Dosu's response (manual)
```

**Workflow:**
1. Run `validate_dosu.py` to collect issue/PR data
2. Review prompts in `dosu_responses/prompt_issue_*.txt`
3. Obtain Dosu responses (via Dosu service, API, or manual)
4. Save responses as `dosu_response_issue_*.txt`
5. Create evaluations in `evaluations/eval_issue_*.json`
6. Run `analyze_dosu_validation.py` to generate performance report

**Evaluation Format:**
```json
{
  "issue_number": 123,
  "dosu_response_quality": {
    "accuracy_score": 4,
    "relevance_score": 5,
    "helpfulness_score": 4,
    "code_context_used": true,
    "hallucination_detected": false,
    "matches_actual_resolution": true
  },
  "notes": "Detailed evaluation notes..."
}
```

### 6. Dosu Analysis Tool

**File**: `analyze_dosu_validation.py`

Analyzes Dosu validation results and generates performance reports.

**Usage:**
```bash
python analyze_dosu_validation.py --validation-dir dosu_validation
```

**Output:**
- `analysis_results.json` - Statistical metrics
- `VALIDATION_REPORT.md` - Human-readable report with recommendations

**Metrics:**
- Accuracy, relevance, and helpfulness scores (1-5 scale)
- Code context usage percentage
- Hallucination detection rate
- Resolution matching percentage
- Overall performance rating and recommendations

### 7. Dosu Fork Validation Tool

**File**: `validate_dosu_fork.py`

Automates validation of Dosu.dev on a fork repository using representative historical issues.

**Purpose**: Since Dosu lacks a public API and cannot be easily configured programmatically, this tool validates Dosu by creating test issues in a fork and monitoring its automatic responses.

**Validation Strategy:**
1. Sync fork's develop branch with upstream
2. Clean existing issues in fork (creates clean slate)
3. Fetch representative closed issues from upstream (by category and difficulty)
4. Create these test issues in the fork
5. Monitor Dosu's automatic responses
6. Compare Dosu's responses with actual upstream resolutions

**Features:**
- Fetches top-N representative issues per category (bug, enhancement, question)
- Selects issues across difficulty spectrum (trivial to very complex)
- Creates test issues with reference to original upstream issues
- Monitors fork for Dosu responses with configurable timeout
- Generates side-by-side comparisons with actual resolutions
- Dry-run mode for planning
- Comprehensive JSON output for manual evaluation

**Usage:**
```bash
# Set GitHub token (needs repo scope for fork access)
export GITHUB_TOKEN=your_token_here

# Dry run to preview
python validate_dosu_fork.py \
    --upstream-repo openmc-dev/openmc \
    --fork-repo pranavkantgaur/openmc \
    --dry-run

# Live validation (creates issues, monitors Dosu)
python validate_dosu_fork.py \
    --upstream-repo openmc-dev/openmc \
    --fork-repo pranavkantgaur/openmc \
    --categories bug enhancement question \
    --per-category 5 \
    --monitor-wait 3600
```

**Output Structure:**
```
dosu_fork_validation/
├── VALIDATION_SUMMARY.md           # Summary report
├── upstream_issues_summary.json    # Selected upstream issues
├── fork_issues_manifest.json       # Created test issues
├── dosu_responses_all.json         # Dosu's responses
├── comparisons_all.json            # All comparisons
├── upstream_issues/                # Upstream issue data
├── fork_issues/                    # Fork issue metadata
├── dosu_responses/                 # Individual Dosu responses
└── comparisons/                    # Individual comparisons
    ├── comparison_1.json
    └── ...
```

**Manual Evaluation:**
After automated collection, manually evaluate each comparison:
- Accuracy (1-5): How well does Dosu's response match actual resolution?
- Relevance (1-5): Does it address the core issue?
- Helpfulness (1-5): Would it guide user to solution?
- Code Context: Does it reference relevant OpenMC code?
- Hallucination: Any incorrect information?

**Notes on Iterative Testing:**
- Dosu lacks API for knowledge base reset
- Each validation builds on Dosu's learned knowledge
- Cannot easily A/B test different prompt configurations
- Workaround: Use different issue categories for each iteration
- Or: Test on categories where Dosu underperforms after reviewing initial results

**Integration with Dosu:**
1. Install Dosu via GitHub Marketplace on your fork
2. Configure Dosu settings via web UI
3. Set "Notes for Dosu" to improve performance
4. Run this script to create test issues
5. Dosu automatically responds
6. Script collects and compares responses

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

For a specific comparison between **GitHub Copilot vs Dosu.dev** for issue triage, including:
- Hallucination mitigation strategies
- Codebase context building approaches
- Cost structures and billing
- Subscription requirements for issue posters
- Customization and control options

See `COPILOT_VS_DOSU_COMPARISON.md` for detailed analysis.

The comparisons cover:
- Codebase context building capabilities
- Issue triage and resolution features
- Cost and pricing models
- Suitability for OpenMC
- Trade-offs and recommendations

## License

These tools are part of the OpenMC project and follow the same MIT/X license.
