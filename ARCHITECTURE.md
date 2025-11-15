# Auto Code Reviewer - Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        INPUT SOURCES                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐     ┌────────────┐ │
│  │   GitLab     │      │  Local MR    │     │   Manual   │ │
│  │   API        │─────▶│   JSON       │◀────│   Files    │ │
│  │              │      │   Files      │     │            │ │
│  └──────────────┘      └──────┬───────┘     └────────────┘ │
│                               │                             │
└───────────────────────────────┼─────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    MR Parser          │
                    │  (mr_parser.py)       │
                    │                       │
                    │  • Extract metadata   │
                    │  • Parse file changes │
                    │  • Filter by language │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Diff Parser         │
                    │  (diff_parser.py)     │
                    │                       │
                    │  • Parse git diffs    │
                    │  • Extract code hunks │
                    │  • Get added lines    │
                    └───────────┬───────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                    ANALYSIS LAYER                              │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│              ┌─────────────────────────────┐                  │
│              │  Tree-Sitter Analyzer       │                  │
│              │  (tree_sitter_analyzer.py)  │                  │
│              │                             │                  │
│              │  • Parse syntax trees       │                  │
│              │  • Execute rules            │                  │
│              │  • Aggregate issues         │                  │
│              └──────────┬──────────────────┘                  │
│                         │                                     │
│         ┌───────────────┼───────────────┐                    │
│         │               │               │                    │
│         ▼               ▼               ▼                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  C/C++ Rules│ │Python Rules │ │General Rules│           │
│  │             │ │             │ │             │           │
│  │ • Null chk  │ │ • Bare exc  │ │ • Func len  │           │
│  │ • Res leak  │ │ • Mut def   │ │ • Complexity│           │
│  │ • Miss ret  │ │ • Unused    │ │ • Nesting   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                                │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   Code Reviewer       │
                │   (reviewer.py)       │
                │                       │
                │  • Orchestrate flow   │
                │  • Aggregate results  │
                │  • Format output      │
                └───────────┬───────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
  ┌───────────────────┐       ┌───────────────────┐
  │  Metrics Tracker  │       │  Review Result    │
  │  (metrics.py)     │       │                   │
  │                   │       │  • Issues list    │
  │  • Track quality  │       │  • Severity dist  │
  │  • Precision/     │       │  • Category dist  │
  │    Recall         │       │  • File list      │
  │  • Compare        │       │  • Timing         │
  │    baseline       │       │                   │
  └─────────┬─────────┘       └─────────┬─────────┘
            │                           │
            └──────────┬────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                         OUTPUTS                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────────┐ │
│  │   Console    │   │   GitLab     │   │   Metrics       │ │
│  │   Output     │   │   Comments   │   │   JSON          │ │
│  │              │   │   (JSON)     │   │                 │ │
│  │  • Summary   │   │              │   │  • Quality      │ │
│  │  • Issues    │   │  • Formatted │   │  • Trends       │ │
│  │  • Metrics   │   │    for API   │   │  • Comparison   │ │
│  └──────────────┘   └──────────────┘   └─────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Input Processing
```
GitLab MR → MR Parser → Extract Files → Filter by Language
                ↓
           Parse Diffs → Extract Code Changes → Get Added Lines
```

### 2. Analysis Pipeline
```
For each changed file:
    1. Detect language (C/C++/Python/...)
    2. Get/Create analyzer for language
    3. Parse code with tree-sitter
    4. Execute all rules
    5. Collect issues
```

### 3. Aggregation
```
All issues → Group by:
    • File
    • Severity (error/warning/info)
    • Category (complexity/style/safety/...)
    • Rule ID
```

### 4. Output Generation
```
Review Result → Format as:
    • Human-readable (console)
    • GitLab comments (JSON)
    • Metrics report (JSON)
```

## Key Design Decisions

### 1. Parser Separation
- **MR Parser**: Handles GitLab-specific structure
- **Diff Parser**: Generic git diff handling
- **Benefit**: Easy to add other VCS systems (GitHub, Bitbucket)

### 2. Language-Agnostic Core
- Analyzer doesn't know about specific languages
- Rules are pluggable and language-specific
- **Benefit**: Easy to add new languages

### 3. Rule-Based Architecture
- Each rule is independent
- Rules implement single responsibility
- **Benefit**: Easy to add/remove/customize rules

### 4. Metrics First
- Built-in quality tracking
- Precision/recall from day one
- **Benefit**: Data-driven improvements

### 5. No External Dependencies (Phase 1)
- Works without GitLab connection
- No database required
- Local file-based testing
- **Benefit**: Fast iteration and testing

## Configuration Flow

```
config/review_rules.yaml
         ↓
    Loaded by
         ↓
    CodeReviewer
         ↓
    Creates Analyzers with
         ↓
    Language-specific configs
         ↓
    Applied to Rules
```

## Future Architecture (Phases 2-6)

```
┌─────────────────────────────────────────────────────────────┐
│                    FUTURE ADDITIONS                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Phase 2:                Phase 3:             Phase 4:      │
│  ┌──────────────┐       ┌──────────────┐    ┌───────────┐  │
│  │ GitLab       │       │  Clangd      │    │   Doc     │  │
│  │ Pattern      │       │  Semantic    │    │  Indexer  │  │
│  │ Analyzer     │       │  Analysis    │    │           │  │
│  └──────┬───────┘       └──────┬───────┘    └─────┬─────┘  │
│         │                      │                   │        │
│         └──────────┬───────────┴───────────────────┘        │
│                    │                                        │
│                    ▼                                        │
│            ┌───────────────┐                               │
│            │  LLM Review   │  Phase 5                      │
│            │  Synthesis    │                               │
│            └───────┬───────┘                               │
│                    │                                        │
│                    ▼                                        │
│            ┌───────────────┐                               │
│            │  GitLab       │  Phase 6                      │
│            │  CI/CD        │                               │
│            └───────────────┘                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | Input | Output |
|-----------|---------------|-------|--------|
| MRParser | Parse MR JSON | GitLab JSON | MergeRequest object |
| DiffParser | Parse diffs | Diff text | FileDiff objects |
| TreeSitterAnalyzer | Structural analysis | Source code | CodeIssue list |
| AnalysisRule | Check specific pattern | Syntax tree | CodeIssue list |
| CodeReviewer | Orchestrate review | MergeRequest | ReviewResult |
| MetricsTracker | Track quality | ReviewResult list | QualityMetrics |

## Extension Points

### Add New Language
1. Install tree-sitter grammar
2. Update `_create_parser()` in TreeSitterAnalyzer
3. Create language-specific rules module
4. Add to `_get_analyzer()` in CodeReviewer

### Add New Rule
1. Inherit from `AnalysisRule`
2. Implement `check()` method
3. Add to appropriate rules module
4. Register in analyzer

### Add New Metric
1. Extend `QualityMetrics` dataclass
2. Update `compute_metrics()` in MetricsTracker
3. Update `print_metrics()` for display

### Add New Output Format
1. Add formatter method to CodeReviewer
2. Export in review scripts
3. Document usage

## Performance Characteristics

**Current (Phase 1):**
- ~0.1-0.5s per file
- ~2-10s per MR (10-50 files)
- Linear scaling with file count

**Expected (All Phases):**
- Phase 2: +10-20% (LLM calls)
- Phase 3: +50-100% (clangd analysis)
- Phase 4: +5-10% (doc retrieval)
- **Total: ~5-30s per MR**

**Optimizations for Later:**
- Parallel file processing
- Incremental analysis (only changed functions)
- Result caching
- Async LLM calls
