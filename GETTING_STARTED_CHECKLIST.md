# Getting Started Checklist

Use this checklist to get your code reviewer up and running!

## ✅ Phase 1: MVP with Tree-Sitter (Current)

### Initial Setup
- [ ] Clone/download the project
- [ ] Install dependencies: `pip install -r requirements.txt --break-system-packages`
- [ ] Run tree-sitter setup: `python scripts/setup_tree_sitter.py`
- [ ] Run tests: `python tests/test_basic.py`

### Test with Example
- [ ] Review example MR: `python scripts/review_mr.py examples/sample_mr.json`
- [ ] Verify you see 6 issues found
- [ ] Check output includes Python and C++ issues

### Download Real MRs
- [ ] Set GitLab credentials:
  ```bash
  export GITLAB_URL="https://gitlab.example.com"
  export GITLAB_TOKEN="your_token_here"
  ```
- [ ] Find your project ID in GitLab
- [ ] Download 5-10 test MRs: `python scripts/download_mrs.py --project-id XXX --count 10`
- [ ] Verify MR files created in `test_data/mrs/`

### Run First Review Batch
- [ ] Review all downloaded MRs: `python scripts/batch_review.py test_data/mrs/`
- [ ] Save baseline metrics: `python scripts/batch_review.py test_data/mrs/ --output-report baseline.json`
- [ ] Review the metrics output
- [ ] Note the issues-per-MR and false positive rate

### Tune Rules
- [ ] Open `config/review_rules.yaml`
- [ ] Adjust function length limits based on your codebase
- [ ] Adjust complexity thresholds
- [ ] Add file exclusion patterns if needed
- [ ] Re-run batch review with custom config
- [ ] Compare new metrics with baseline

### Quality Assessment
- [ ] Pick 2-3 reviewed MRs to manually inspect
- [ ] Label issues as true positive / false positive
- [ ] Create `human_labels.json`:
  ```json
  {
    "123": {
      "true_positives": 5,
      "false_positives": 2,
      "false_negatives": 1
    }
  }
  ```
- [ ] Re-run with labels: `python scripts/batch_review.py test_data/mrs/ --human-labels human_labels.json`
- [ ] Note your precision and recall

### Documentation
- [ ] Document which rules work well for your codebase
- [ ] Document which rules produce too many false positives
- [ ] Create a summary of Phase 1 findings

## 📋 Phase 2: GitLab Pattern Analysis (Next)

### Prerequisites
- [ ] Have reviewed 20+ MRs in Phase 1
- [ ] Have baseline quality metrics
- [ ] GitLab API access working

### Implementation Tasks
- [ ] Use your existing GitLab review analyzer
- [ ] Extract common review patterns from history
- [ ] Identify team-specific conventions
- [ ] Generate best practices documentation
- [ ] Use LLM for semantic categorization

### Integration
- [ ] Merge pattern insights into rule configuration
- [ ] Add team conventions to documentation
- [ ] Update rules based on historical patterns

### Validation
- [ ] Review same MRs with pattern-enhanced rules
- [ ] Measure improvement in precision/recall
- [ ] Compare with Phase 1 baseline

## 🔧 Phase 3: Clangd Integration (Future)

### Prerequisites
- [ ] Make-based build system working
- [ ] Bear installed: `sudo apt-get install bear` or `brew install bear`

### Setup
- [ ] Generate compile_commands.json:
  ```bash
  bear -- make clean all
  ```
- [ ] Verify compile_commands.json created
- [ ] Test clangd can parse a file

### Implementation
- [ ] Integrate clangd language server
- [ ] Add semantic analysis rules
- [ ] Combine tree-sitter + clangd insights

### Validation
- [ ] Compare semantic vs structural analysis
- [ ] Measure impact on issue quality
- [ ] Assess performance impact

## 📚 Phase 4: Documentation Integration (Future)

### Prerequisites
- [ ] Claude MDs organized and indexed
- [ ] Internal docs accessible
- [ ] Vector database setup

### Implementation
- [ ] Index Claude MDs with embeddings
- [ ] Implement graph traversal for links
- [ ] Add file proximity search
- [ ] Integrate with reviewer

### Validation
- [ ] Test doc retrieval quality
- [ ] Measure context relevance
- [ ] Assess impact on review quality

## 🧪 Phase 5: Quality Improvements (Future)

### Experimentation
- [ ] A/B test different prompting strategies
- [ ] Try different LLM models
- [ ] Experiment with doc chunking
- [ ] Test various embedding models

### Measurement
- [ ] Track improvements systematically
- [ ] Use metrics to guide decisions
- [ ] Document what works

## 🚀 Phase 6: CI/CD Integration (Future)

### Prerequisites
- [ ] Phase 1-5 quality validated
- [ ] Error handling robust
- [ ] Performance acceptable

### Implementation
- [ ] GitLab webhook handler
- [ ] Auto-comment on MRs
- [ ] Quality gates configuration
- [ ] Performance optimization

### Deployment
- [ ] Test in staging
- [ ] Gradual rollout
- [ ] Monitor and iterate

## 🎯 Success Criteria

### Phase 1 Success
- ✓ Reviews run without errors
- ✓ Issues are relevant to your codebase
- ✓ Precision > 60% (with manual labeling)
- ✓ Recall > 40% (with manual labeling)
- ✓ Analysis time < 10s per MR

### Overall Success
- Team finds reviews helpful
- False positive rate < 20%
- Catches real issues consistently
- Integrated into development workflow
- Saves reviewer time

## 📝 Notes & Observations

Use this space to track your progress and learnings:

### What Works Well
- 

### What Needs Improvement
- 

### Unexpected Findings
- 

### Ideas for Future
- 

---

## Quick Commands Reference

```bash
# Phase 1: Setup
pip install -r requirements.txt --break-system-packages
python scripts/setup_tree_sitter.py
python tests/test_basic.py

# Download MRs
export GITLAB_URL="https://gitlab.example.com"
export GITLAB_TOKEN="your_token"
python scripts/download_mrs.py --project-id 123 --count 10

# Review single MR
python scripts/review_mr.py test_data/mrs/mr_1.json

# Batch review
python scripts/batch_review.py test_data/mrs/

# With config
python scripts/review_mr.py mr.json --config config/review_rules.yaml

# With metrics
python scripts/batch_review.py test_data/mrs/ \
    --output-report metrics.json \
    --baseline baseline.json \
    --human-labels labels.json

# GitLab comment format
python scripts/review_mr.py mr.json --gitlab-comments comments.json
```

---

**Start with Phase 1 checklist and work through systematically!**
