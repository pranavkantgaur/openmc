# Example Validation Report

This is an example of what the validation report looks like when you run `validate_issue_responder.py`.

---

# AI Issue Responder Validation Report

**Repository**: openmc-dev/openmc
**Generated**: 2026-01-01 20:45:00 UTC
**Test Cases**: 30

## Executive Summary

This report validates the performance of the AI Issue Responder on real issues from the OpenMC repository. The responder automatically classifies issues and generates helpful responses.

### Overall Performance

- **Success Rate**: 29/30 (96.7%)
- **Average Processing Time**: 2.34s per issue
- **Average Response Length**: 1,247 characters

### Classification Accuracy

- **Correct Classifications**: 24/28 (85.7%)

## Issue Distribution by Category

| Category | Count | Percentage |
|----------|-------|------------|
| Bug | 12 | 40.0% |
| Feature | 8 | 26.7% |
| Question | 6 | 20.0% |
| Documentation | 3 | 10.0% |
| Other | 1 | 3.3% |

## Detailed Test Results

### Sample Classifications

#### Test Case 1: Issue #3050

**Title**: Segmentation fault when running with MPI
**Expected Type**: bug
**Predicted Type**: bug
**Complexity**: complex
**Processing Time**: 2.450s
**Response Length**: 1,456 chars

#### Test Case 2: Issue #3045

**Title**: Add support for custom tally filters
**Expected Type**: feature
**Predicted Type**: feature
**Complexity**: moderate
**Processing Time**: 1.890s
**Response Length**: 1,234 chars

#### Test Case 3: Issue #3040

**Title**: How to set up depletion simulation?
**Expected Type**: question
**Predicted Type**: question
**Complexity**: simple
**Processing Time**: 1.670s
**Response Length**: 987 chars

[... more test cases ...]

## Performance Metrics

### Processing Time Distribution

- **Minimum**: 1.234s
- **Median**: 2.100s
- **Maximum**: 4.567s
- **95th Percentile**: 3.890s

### Response Quality Metrics

- **Bug Reports**: 95% received relevant debugging steps
- **Feature Requests**: 90% got contribution guidance
- **Questions**: 100% linked to relevant documentation
- **Average User Satisfaction**: Not yet measured (requires real-world deployment)

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

- **Reduce maintainer burden** by handling initial issue triage (estimated 30+ hours/month saved)
- **Improve user experience** with faster initial responses (<5 min vs. hours/days)
- **Maintain consistency** in issue handling across all reporters
- **Collect metrics** on issue types and complexity for project planning

### Cost-Benefit Analysis

**Without AI API (Template Responses):**
- Cost: $0/month
- Quality: Good for standard cases
- Recommendation: Start here, upgrade if needed

**With AI API (OpenAI GPT-4):**
- Cost: ~$5-20/month (depending on volume)
- Quality: Excellent, context-aware responses
- Recommendation: For production deployment

**With AI API (Anthropic Claude):**
- Cost: ~$5-15/month
- Quality: Excellent, very contextual
- Recommendation: Alternative to OpenAI

### Suggested Improvements

Based on this validation:

1. **Enable AI Provider**: Connect OpenAI or Anthropic API for smarter responses
2. **Fine-tune Classification**: Adjust heuristics based on OpenMC-specific patterns
3. **Add Domain Knowledge**: Include OpenMC-specific troubleshooting in responses
4. **Monitor Performance**: Track accuracy over time and adjust as needed
5. **Collect Feedback**: Add reaction buttons to responses for user feedback

### Accuracy by Issue Type

| Type | Tested | Correct | Accuracy |
|------|--------|---------|----------|
| Bug | 12 | 11 | 91.7% |
| Feature | 8 | 7 | 87.5% |
| Question | 6 | 6 | 100.0% |
| Documentation | 3 | 2 | 66.7% |
| Other | 1 | 0 | 0.0% |

**Analysis**: 
- Very high accuracy on questions (100%)
- Good accuracy on bugs (91.7%)
- Needs improvement on documentation issues
- "Other" category is catch-all and expected to have lower accuracy

### Next Steps for PR Submission

To submit this to upstream OpenMC:

1. ✅ **Run this validation** on a representative sample of issues
2. ✅ **Include this report** in the PR description
3. **Document setup requirements** (API keys, secrets configuration)
4. **Propose trial period** to gather real-world metrics (suggest 1 month)
5. **Offer to monitor** and adjust based on maintainer feedback

### Deployment Plan

**Phase 1 (Week 1)**: Enable with template responses only
- Monitor for any issues
- Collect initial user feedback
- No API costs

**Phase 2 (Week 2-4)**: Add AI API if response quality needs improvement
- Enable OpenAI or Anthropic
- Compare response quality
- Monitor costs

**Phase 3 (Month 2+)**: Optimize based on metrics
- Adjust classification heuristics
- Improve response templates
- Fine-tune AI prompts

### Success Metrics

After 1 month of deployment, measure:
- **User satisfaction**: Reactions on automated responses
- **Maintainer time saved**: Hours not spent on initial triage
- **Response time improvement**: Time from issue open to first response
- **Classification accuracy**: Human review of 20 random classifications

## Limitations

1. **No Deep Understanding**: Classification is heuristic-based, not semantic
2. **English Only**: Assumes issues are written in English
3. **No Context**: Doesn't consider related issues or PR history
4. **Template Limitations**: Fallback responses are generic (improved with AI)
5. **False Positives**: May misclassify ambiguous issues (~15% error rate)

## Conclusion

The AI Issue Responder shows strong performance on real OpenMC issues:
- **85.7% classification accuracy** meets or exceeds similar systems
- **<3s processing time** provides near-instant responses
- **High success rate** (96.7%) demonstrates reliability
- **Zero cost option** available with template responses

**Recommendation**: Deploy to production with 1-month trial period to gather real-world metrics. Start with template responses, add AI if needed based on user feedback.

---

*This validation was generated automatically by `tools/ai/validate_issue_responder.py`*
