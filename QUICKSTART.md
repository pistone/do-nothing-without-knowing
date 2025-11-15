# Quick Start Guide

Get the code reviewer running in 5 minutes!

## Step 1: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt --break-system-packages

# Install tree-sitter language grammars
python scripts/setup_tree_sitter.py
```

## Step 2: Test the Installation

```bash
# Run basic tests
python tests/test_basic.py

# Review the example MR
python scripts/review_mr.py examples/sample_mr.json
```

You should see output like:
```
🔍 Reviewing examples/sample_mr.json...

============================================================
Review Complete
============================================================
Files analyzed: 2/2
Issues found: 6
Analysis time: 0.15s

ISSUES FOUND: 6
================================================================================

📄 src/payment.py
────────────────────────────────────────────────────────────────────────────────

  ⚠️ Line 1 [WARNING]
     Function 'process_payment' is 32 lines long, exceeds maximum of 40 lines
     Category: complexity | Rule: FUNC_TOO_LONG
     💡 Consider breaking this function into smaller, more focused functions

  ℹ️ Line 34 [INFO]
     Public function 'get_customer_name' missing docstring
     Category: documentation | Rule: MISSING_DOCSTRING
     💡 Add docstring describing parameters, returns, and behavior
```

## Step 3: Download Real MRs (Optional)

```bash
# Set your GitLab credentials
export GITLAB_URL="https://gitlab.example.com"
export GITLAB_TOKEN="your_token_here"

# Download 10 recent merged MRs from project
python scripts/download_mrs.py --project-id 123 --count 10
```

## Step 4: Run Batch Review

```bash
# Review all downloaded MRs
python scripts/batch_review.py test_data/mrs/ --output-report metrics.json
```

## Step 5: Customize Rules

Edit `config/review_rules.yaml` to adjust:
- Function length limits
- Complexity thresholds  
- Which rules to enable/disable
- File exclusions

Then review with custom config:
```bash
python scripts/review_mr.py examples/sample_mr.json --config config/review_rules.yaml
```

## Next Steps

### Phase 2: Add GitLab Pattern Analysis
After testing with local MRs, you can analyze historical review patterns:
```bash
# Coming soon: analyze_review_patterns.py
```

### Phase 3: Add Clangd Integration
Set up compile_commands.json for semantic analysis:
```bash
# For Make-based projects
bear -- make clean all
```

### Phase 4: Add Documentation Context
Index your documentation for context-aware reviews:
```bash
# Coming soon: index_docs.py
```

## Troubleshooting

**Tree-sitter import errors:**
```bash
python scripts/setup_tree_sitter.py
```

**GitLab connection issues:**
- Check GITLAB_URL and GITLAB_TOKEN
- Verify token has API access
- Confirm project ID is correct

**No issues found:**
- Check that MR contains supported file types (.py, .cpp, .c)
- Verify the diff format is correct
- Try the example MR first

## Tips for Best Results

1. **Start Small**: Test with 5-10 MRs first
2. **Tune Rules**: Adjust thresholds based on your codebase
3. **Track Metrics**: Use batch review to measure improvements
4. **Add Labels**: Label true/false positives for accuracy metrics
5. **Iterate**: Continuously refine based on feedback

## Common Workflows

**Daily Development:**
```bash
# Download today's MRs
python scripts/download_mrs.py --project-id 123 --state opened --count 5

# Review them
python scripts/batch_review.py test_data/mrs/
```

**Benchmarking:**
```bash
# Review baseline
python scripts/batch_review.py test_data/baseline/ --output-report baseline.json

# Make improvements to rules...

# Review again and compare
python scripts/batch_review.py test_data/baseline/ --output-report improved.json --baseline baseline.json
```

**CI Integration (Future):**
```bash
# In GitLab CI
- python scripts/review_mr.py current_mr.json --gitlab-comments comments.json
- post_comments_to_mr.py comments.json
```
