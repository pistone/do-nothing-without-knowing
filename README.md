# Auto Code Reviewer

An intelligent code review agent that leverages tree-sitter for structural analysis, clangd for semantic understanding, and documentation context to provide comprehensive code reviews.

## 🎯 Project Goals

Build a measurable, iterative code review system:
1. **Phase 1** (Current): MVP with tree-sitter + local MR testing
2. **Phase 2**: Add GitLab pattern analysis from historical reviews
3. **Phase 3**: Integrate clangd for semantic analysis
4. **Phase 4**: Add documentation context (Claude MDs, blogs, internal docs)
5. **Phase 5**: Experiment with doc quality improvements
6. **Phase 6**: CI/CD integration

## 🚀 Quick Start (Phase 1)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd auto-code-reviewer

# Install dependencies
pip install -r requirements.txt --break-system-packages

# Install tree-sitter language grammars
python scripts/setup_tree_sitter.py
```

### Download Test MRs

```bash
# Set your GitLab credentials
export GITLAB_URL="https://gitlab.example.com"
export GITLAB_TOKEN="your_token_here"

# Download MRs for testing
python scripts/download_mrs.py --project-id 123 --output-dir test_data/mrs/
```

### Run Review on Local MR

```bash
# Review a single MR
python scripts/review_mr.py test_data/mrs/mr_456.json

# Run on all test MRs and generate quality report
python scripts/batch_review.py test_data/mrs/ --output-report quality_metrics.json
```

## 📁 Project Structure

```
auto-code-reviewer/
├── src/
│   └── auto_reviewer/
│       ├── parsers/
│       │   ├── mr_parser.py          # Parse GitLab MR JSON
│       │   └── diff_parser.py        # Parse git diffs
│       ├── analyzers/
│       │   ├── tree_sitter_analyzer.py  # Tree-sitter code analysis
│       │   └── rules/                   # Review rule definitions
│       │       ├── base.py
│       │       ├── cpp_rules.py
│       │       ├── python_rules.py
│       │       └── general_rules.py
│       ├── reviewer.py               # Main reviewer orchestration
│       └── metrics.py                # Quality metrics tracking
├── scripts/
│   ├── setup_tree_sitter.py         # Install language grammars
│   ├── download_mrs.py              # Download MRs from GitLab
│   ├── review_mr.py                 # Review single MR
│   └── batch_review.py              # Batch review with metrics
├── test_data/
│   └── mrs/                         # Downloaded MR files
├── config/
│   └── review_rules.yaml            # Configurable review rules
└── tests/
    └── test_analyzers.py
```

## 🎯 Current Phase 1 Features

### Tree-sitter Analysis
- **Structural checks**: Function length, complexity, nesting depth
- **Pattern detection**: Missing returns, uninitialized variables, resource leaks
- **Style issues**: Naming conventions, formatting consistency
- **Language support**: C, C++, Python (extensible to others)

### Quality Metrics
- True positive rate (issues correctly identified)
- False positive rate (noise)
- Coverage (% of real issues caught)
- Review comment clarity
- Performance (time per file)

### MR Testing Framework
- Download real MRs from GitLab
- Review them locally
- Compare against human reviews
- Track improvements over time

## 🔧 Configuration

Edit `config/review_rules.yaml` to customize:

```yaml
rules:
  general:
    max_function_length: 50
    max_nesting_depth: 4
    max_complexity: 15
  
  cpp:
    check_resource_leaks: true
    require_error_handling: true
    check_memory_safety: true
  
  python:
    check_exception_handling: true
    enforce_type_hints: false
```

## 📊 Quality Metrics

Track reviewer quality over time:

```bash
# Generate metrics report
python scripts/batch_review.py test_data/mrs/ --compare-with-human-reviews
```

Metrics tracked:
- Precision: What % of flagged issues are real?
- Recall: What % of real issues did we catch?
- Comment quality: How helpful are the suggestions?
- False positive rate by rule type

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Test specific analyzer
pytest tests/test_analyzers.py::TestTreeSitterAnalyzer

# Test with real MR
python scripts/review_mr.py test_data/mrs/mr_123.json --verbose
```

## 🔜 Next Steps (Future Phases)

- **Phase 2**: GitLab pattern analysis from historical reviews
- **Phase 3**: Clangd integration (requires compile_commands.json)
- **Phase 4**: Documentation context retrieval
- **Phase 5**: LLM-powered review synthesis
- **Phase 6**: CI/CD integration

## 📝 Contributing

See each phase's goals in the project documentation. Current focus: improving tree-sitter rule accuracy and reducing false positives.

## 📄 License

[Your License Here]
