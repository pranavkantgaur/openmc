#!/usr/bin/env python3
"""
Analyze Dosu.dev validation results.

This script analyzes the validation data collected by validate_dosu.py
and generates statistical reports on Dosu's performance.

Usage:
    python analyze_dosu_validation.py --validation-dir dosu_validation
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List
import statistics


def load_validation_data(validation_dir: Path) -> Dict:
    """Load validation manifest and evaluations."""
    manifest_file = validation_dir / 'validation_manifest.json'
    
    if not manifest_file.exists():
        print(f"Error: Manifest file not found: {manifest_file}")
        sys.exit(1)
    
    with open(manifest_file, 'r') as f:
        manifest = json.load(f)
    
    return manifest


def load_evaluations(validation_dir: Path) -> List[Dict]:
    """Load all evaluation JSON files."""
    evaluations = []
    eval_pattern = validation_dir / 'evaluations' / 'eval_issue_*.json'
    
    eval_dir = validation_dir / 'evaluations'
    if not eval_dir.exists():
        print("Warning: No evaluations directory found")
        print("Create evaluations in: dosu_validation/evaluations/")
        print("Format: eval_issue_<number>.json")
        return []
    
    for eval_file in eval_dir.glob('eval_issue_*.json'):
        try:
            with open(eval_file, 'r') as f:
                evaluation = json.load(f)
                evaluations.append(evaluation)
        except Exception as e:
            print(f"Warning: Could not load {eval_file}: {e}")
    
    return evaluations


def analyze_performance(evaluations: List[Dict]) -> Dict:
    """Analyze Dosu's performance from evaluations."""
    if not evaluations:
        return {
            'error': 'No evaluations found',
            'total_evaluated': 0
        }
    
    # Collect scores
    accuracy_scores = []
    relevance_scores = []
    helpfulness_scores = []
    code_context_count = 0
    hallucination_count = 0
    matches_resolution_count = 0
    
    for eval_data in evaluations:
        quality = eval_data.get('dosu_response_quality', {})
        
        if 'accuracy_score' in quality:
            accuracy_scores.append(quality['accuracy_score'])
        if 'relevance_score' in quality:
            relevance_scores.append(quality['relevance_score'])
        if 'helpfulness_score' in quality:
            helpfulness_scores.append(quality['helpfulness_score'])
        
        if quality.get('code_context_used'):
            code_context_count += 1
        if quality.get('hallucination_detected'):
            hallucination_count += 1
        if quality.get('matches_actual_resolution'):
            matches_resolution_count += 1
    
    # Calculate statistics
    total = len(evaluations)
    
    results = {
        'total_evaluated': total,
        'accuracy': {
            'mean': statistics.mean(accuracy_scores) if accuracy_scores else 0,
            'median': statistics.median(accuracy_scores) if accuracy_scores else 0,
            'std_dev': statistics.stdev(accuracy_scores) if len(accuracy_scores) > 1 else 0,
            'min': min(accuracy_scores) if accuracy_scores else 0,
            'max': max(accuracy_scores) if accuracy_scores else 0,
        },
        'relevance': {
            'mean': statistics.mean(relevance_scores) if relevance_scores else 0,
            'median': statistics.median(relevance_scores) if relevance_scores else 0,
            'std_dev': statistics.stdev(relevance_scores) if len(relevance_scores) > 1 else 0,
        },
        'helpfulness': {
            'mean': statistics.mean(helpfulness_scores) if helpfulness_scores else 0,
            'median': statistics.median(helpfulness_scores) if helpfulness_scores else 0,
            'std_dev': statistics.stdev(helpfulness_scores) if len(helpfulness_scores) > 1 else 0,
        },
        'code_context_usage': {
            'count': code_context_count,
            'percentage': (code_context_count / total * 100) if total > 0 else 0
        },
        'hallucinations': {
            'count': hallucination_count,
            'percentage': (hallucination_count / total * 100) if total > 0 else 0
        },
        'matches_actual_resolution': {
            'count': matches_resolution_count,
            'percentage': (matches_resolution_count / total * 100) if total > 0 else 0
        }
    }
    
    return results


def generate_report(manifest: Dict, analysis: Dict, output_file: Path):
    """Generate markdown report."""
    report = f"""# Dosu.dev Validation Report for OpenMC

**Generated:** {analysis.get('generated_at', 'N/A')}
**Repository:** openmc-dev/openmc

## Summary

- **Total Issues Collected:** {manifest['total_issues']}
- **Total Evaluated:** {analysis['total_evaluated']}
- **Evaluation Coverage:** {(analysis['total_evaluated'] / manifest['total_issues'] * 100):.1f}%

## Performance Metrics

### Accuracy Score
- **Mean:** {analysis['accuracy']['mean']:.2f} / 5.0
- **Median:** {analysis['accuracy']['median']:.2f} / 5.0
- **Std Dev:** {analysis['accuracy']['std_dev']:.2f}
- **Range:** {analysis['accuracy']['min']:.0f} - {analysis['accuracy']['max']:.0f}

### Relevance Score
- **Mean:** {analysis['relevance']['mean']:.2f} / 5.0
- **Median:** {analysis['relevance']['median']:.2f} / 5.0
- **Std Dev:** {analysis['relevance']['std_dev']:.2f}

### Helpfulness Score
- **Mean:** {analysis['helpfulness']['mean']:.2f} / 5.0
- **Median:** {analysis['helpfulness']['median']:.2f} / 5.0
- **Std Dev:** {analysis['helpfulness']['std_dev']:.2f}

## Context and Quality

### Code Context Usage
- **Count:** {analysis['code_context_usage']['count']} / {analysis['total_evaluated']}
- **Percentage:** {analysis['code_context_usage']['percentage']:.1f}%

### Hallucinations Detected
- **Count:** {analysis['hallucinations']['count']} / {analysis['total_evaluated']}
- **Percentage:** {analysis['hallucinations']['percentage']:.1f}%

### Matches Actual Resolution
- **Count:** {analysis['matches_actual_resolution']['count']} / {analysis['total_evaluated']}
- **Percentage:** {analysis['matches_actual_resolution']['percentage']:.1f}%

## Interpretation

### Overall Performance Rating

"""
    
    # Calculate overall rating
    avg_score = (analysis['accuracy']['mean'] + analysis['relevance']['mean'] + analysis['helpfulness']['mean']) / 3
    
    if avg_score >= 4.5:
        rating = "⭐⭐⭐⭐⭐ Excellent"
        interpretation = "Dosu provides highly accurate and helpful responses that closely match actual resolutions."
    elif avg_score >= 4.0:
        rating = "⭐⭐⭐⭐ Very Good"
        interpretation = "Dosu provides very good responses with minor room for improvement."
    elif avg_score >= 3.5:
        rating = "⭐⭐⭐ Good"
        interpretation = "Dosu provides good responses but may miss some details or context."
    elif avg_score >= 3.0:
        rating = "⭐⭐ Fair"
        interpretation = "Dosu provides fair guidance but often lacks detail or accuracy."
    else:
        rating = "⭐ Needs Improvement"
        interpretation = "Dosu's responses need significant improvement for OpenMC."
    
    report += f"**{rating}** (Average: {avg_score:.2f}/5.0)\n\n"
    report += f"{interpretation}\n\n"
    
    # Add context usage analysis
    if analysis['code_context_usage']['percentage'] >= 80:
        report += "✅ **Codebase Context**: Dosu effectively uses codebase context in most responses.\n\n"
    elif analysis['code_context_usage']['percentage'] >= 50:
        report += "⚠️ **Codebase Context**: Dosu uses codebase context in about half of responses.\n\n"
    else:
        report += "❌ **Codebase Context**: Dosu rarely uses codebase context in responses.\n\n"
    
    # Add hallucination analysis
    if analysis['hallucinations']['percentage'] <= 5:
        report += "✅ **Hallucination Rate**: Very low (<5%) - Responses are generally accurate.\n\n"
    elif analysis['hallucinations']['percentage'] <= 15:
        report += "⚠️ **Hallucination Rate**: Moderate (5-15%) - Some responses contain inaccuracies.\n\n"
    else:
        report += "❌ **Hallucination Rate**: High (>15%) - Significant concern for production use.\n\n"
    
    # Add resolution matching analysis
    if analysis['matches_actual_resolution']['percentage'] >= 70:
        report += "✅ **Resolution Matching**: Dosu frequently suggests solutions similar to actual resolutions.\n\n"
    elif analysis['matches_actual_resolution']['percentage'] >= 50:
        report += "⚠️ **Resolution Matching**: Dosu sometimes matches actual resolutions.\n\n"
    else:
        report += "❌ **Resolution Matching**: Dosu rarely matches actual resolutions.\n\n"
    
    report += """## Recommendations

Based on this validation:

"""
    
    if avg_score >= 4.0 and analysis['hallucinations']['percentage'] <= 10:
        report += """1. ✅ **Deploy Dosu**: Performance is strong enough for production use
2. Monitor hallucination rate and user feedback
3. Consider as Phase 2 upgrade from template-based responses
4. Free for open source - excellent value proposition
"""
    elif avg_score >= 3.5:
        report += """1. ⚠️ **Pilot Program**: Test with subset of issues first
2. Monitor performance and gather user feedback
3. Compare cost vs. maintainer time saved
4. Consider alongside template-based responses
"""
    else:
        report += """1. ❌ **Not Recommended**: Performance below threshold for OpenMC
2. Stick with template-based responses (our implementation)
3. Re-evaluate when Dosu improves or provides OpenMC-specific training
4. Consider manual triage by maintainers
"""
    
    report += """
## Next Steps

1. Review individual evaluations for specific insights
2. Compare with template-based response performance
3. Consider issue type breakdown (bugs vs features vs questions)
4. Make final recommendation for OpenMC team

## Detailed Results

See individual evaluation files in `evaluations/` directory for case-by-case analysis.
"""
    
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"✓ Generated report: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze Dosu.dev validation results'
    )
    parser.add_argument(
        '--validation-dir',
        default='dosu_validation',
        help='Validation data directory'
    )
    
    args = parser.parse_args()
    validation_dir = Path(args.validation_dir)
    
    if not validation_dir.exists():
        print(f"Error: Validation directory not found: {validation_dir}")
        print("Run validate_dosu.py first to collect validation data")
        sys.exit(1)
    
    print("="*80)
    print("DOSU.DEV VALIDATION ANALYSIS")
    print("="*80)
    
    # Load data
    print("\nLoading validation data...")
    manifest = load_validation_data(validation_dir)
    print(f"  Total issues: {manifest['total_issues']}")
    
    print("\nLoading evaluations...")
    evaluations = load_evaluations(validation_dir)
    print(f"  Evaluations found: {len(evaluations)}")
    
    if not evaluations:
        print("\n⚠️  No evaluations found!")
        print("\nTo complete validation:")
        print("1. Obtain Dosu responses for each issue")
        print("2. Create evaluation files in: dosu_validation/evaluations/")
        print("3. Format: eval_issue_<number>.json")
        print("4. Run this script again")
        sys.exit(1)
    
    # Analyze
    print("\nAnalyzing performance...")
    from datetime import datetime
    analysis = analyze_performance(evaluations)
    analysis['generated_at'] = datetime.utcnow().isoformat()
    
    # Save analysis
    analysis_file = validation_dir / 'analysis_results.json'
    with open(analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"  Saved analysis: {analysis_file}")
    
    # Generate report
    print("\nGenerating report...")
    report_file = validation_dir / 'VALIDATION_REPORT.md'
    generate_report(manifest, analysis, report_file)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nResults:")
    print(f"  Average Accuracy: {analysis['accuracy']['mean']:.2f}/5.0")
    print(f"  Average Relevance: {analysis['relevance']['mean']:.2f}/5.0")
    print(f"  Average Helpfulness: {analysis['helpfulness']['mean']:.2f}/5.0")
    print(f"  Code Context Usage: {analysis['code_context_usage']['percentage']:.1f}%")
    print(f"  Hallucination Rate: {analysis['hallucinations']['percentage']:.1f}%")
    print(f"  Matches Resolution: {analysis['matches_actual_resolution']['percentage']:.1f}%")
    print(f"\nReport: {report_file}")


if __name__ == '__main__':
    main()
