# Document RAG System

A hybrid RAG (Retrieval-Augmented Generation) system for cross-referenced markdown documentation.

## Features

✅ **Hybrid Retrieval**
- Semantic search using vector embeddings
- Graph traversal following document links
- Combines both for better results

✅ **Cross-Reference Aware**
- Preserves link structure between documents
- Follows incoming and outgoing references
- Understands document relationships

✅ **Incremental Indexing**
- Only reindexes changed files
- Fast updates for large document sets
- Content hash-based change detection

✅ **Agent-Ready**
- Formats output for LLM consumption
- Easy integration with programming agents
- Contextual code explanations

## Architecture

```
Markdown Files → Indexer → Vector DB (ChromaDB)
      ↓                          ↓
   Parse links              Generate embeddings
      ↓                          ↓
  Graph structure → Retriever ← Semantic search
                       ↓
                  Hybrid results
                       ↓
                   Reranking
                       ↓
                  Format for LLM
```

## Installation

```bash
# Install dependencies
pip install -r requirements_rag.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-key-here"
```

## Quick Start

### 1. Index Your Documents

```bash
# Index all markdown files in a directory
python doc_rag.py index --docs-dir /path/to/your/docs

# This will:
# - Parse all .md files
# - Extract links and build graph
# - Chunk documents intelligently
# - Generate embeddings
# - Store in ./doc_index/
```

### 2. Query Documents

```bash
# Semantic search + graph traversal
python doc_rag.py query "How do we handle authentication?"

# Semantic search only (no graph)
python doc_rag.py query "payment processing" --no-graph

# Get more results
python doc_rag.py query "error handling" --top-k 10

# Format for LLM
python doc_rag.py query "API design" --format-for-llm
```

### 3. Explore Document Links

```bash
# Show incoming/outgoing links for a document
python doc_rag.py links path/to/document.md

# Search by title
python doc_rag.py search-title "Authentication"
```

## Using with a Programming Agent

```python
from doc_retriever import DocumentRetriever
from openai import OpenAI

# Initialize
retriever = DocumentRetriever(db_path="./doc_index")
client = OpenAI()

# Work on a Jira ticket
ticket = "JIRA-123: Add rate limiting to payment API"

# Retrieve relevant docs
docs = retriever.retrieve(ticket, top_k=5, use_graph=True)

# Format for LLM
context = retriever.format_for_llm(docs)

# Build prompt
prompt = f"""
Jira Ticket: {ticket}

Relevant Documentation:
{context}

Task: Provide an implementation plan following our team's conventions.
"""

# Call LLM
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a programming assistant."},
        {"role": "user", "content": prompt}
    ]
)

print(response.choices[0].message.content)
```

See `agent_example.py` for a complete example.

## How It Works

### Hybrid Retrieval

**Step 1: Semantic Search**
- Embed the query using OpenAI's `text-embedding-3-small`
- Find top-k most similar document chunks in ChromaDB
- Returns documents semantically related to query

**Step 2: Graph Traversal**
- Start from semantic search results (seed documents)
- Follow document links (both directions)
- Traverse up to N hops away
- Retrieves related documents via explicit references

**Step 3: Combine & Rerank**
- Merge semantic + graph results
- Deduplicate by chunk ID
- Rerank by combined score
- Return top-k final results

### Document Chunking

Documents are chunked by section (## headings):
- Each section becomes one or more chunks
- Chunks maintain context (document title + section)
- Overlapping chunks for continuity
- Preserves document structure

### Link Extraction

Markdown links are extracted and resolved:
```markdown
[See Authentication](./auth/overview.md)
[API Reference](../api/endpoints.md)
```

Builds bidirectional graph:
- **Outgoing**: Links this doc references
- **Incoming**: Links that reference this doc

## Configuration

### Indexing Parameters

```python
indexer = DocumentIndexer(
    docs_dir=Path("/path/to/docs"),
    db_path=Path("./doc_index"),
    embedding_model="text-embedding-3-small",  # OpenAI model
    chunk_size=1000,         # Characters per chunk
    chunk_overlap=200        # Overlap between chunks
)
```

### Retrieval Parameters

```python
docs = retriever.retrieve(
    query="your query",
    top_k=5,                 # Number of results
    use_graph=True,          # Enable graph traversal
    max_hops=2               # Maximum link hops
)
```

## Advanced Usage

### Incremental Updates

```bash
# Only reindex changed files
python doc_rag.py index --docs-dir /path/to/docs

# Force full reindex
python doc_rag.py index --docs-dir /path/to/docs --force
```

### Custom Chunk Sizes

```bash
# Larger chunks (more context)
python doc_rag.py index --docs-dir /path/to/docs --chunk-size 2000

# Smaller chunks (more precise)
python doc_rag.py index --docs-dir /path/to/docs --chunk-size 500
```

### Programmatic Usage

```python
from doc_retriever import DocumentRetriever

retriever = DocumentRetriever(db_path="./doc_index")

# Get document graph info
links = retriever.get_document_links("path/to/doc.md")
print(f"Outgoing: {links['outgoing']}")
print(f"Incoming: {links['incoming']}")

# Search by title
matches = retriever.find_by_title("Authentication")

# Custom retrieval
docs = retriever.retrieve(
    query="rate limiting",
    top_k=10,
    use_graph=True,
    max_hops=3
)
```

## Document Format

### Basic Markdown

```markdown
# Document Title

Content here...

## Section 1

More content...

[Link to another doc](./other-doc.md)
```

### With Frontmatter (Optional)

```markdown
---
category: architecture
tags: [authentication, security]
author: team-name
---

# Authentication System

...
```

Frontmatter is extracted and stored as metadata.

## Performance

**Indexing:**
- ~100-200 documents/minute
- Depends on OpenAI API rate limits
- Batch processing for efficiency

**Retrieval:**
- ~100-500ms per query
- Semantic search: 10-50ms
- Graph traversal: 50-200ms
- Reranking: 10-50ms

**Storage:**
- ~1-5KB per document chunk
- ~100-500 chunks per 10,000 words
- Graph: ~100 bytes per document

## File Structure

```
doc_index/
├── chroma.sqlite3          # ChromaDB vector database
├── doc_graph.json          # Document link graph
└── content_hashes.json     # File change tracking
```

## Integration with Code Review Agent

This RAG system is designed to integrate with the Auto Code Reviewer (Phase 4):

```python
from doc_retriever import DocumentRetriever
from auto_reviewer import CodeReviewer

# Initialize both
retriever = DocumentRetriever(db_path="./doc_index")
reviewer = CodeReviewer()

# Review with documentation context
mr = load_mr("mr_123.json")

for file_change in mr.files:
    # Get relevant docs for this file
    docs = retriever.retrieve(
        query=f"best practices for {file_change.file_path}",
        top_k=3
    )
    
    # Review with context
    issues = reviewer.review_with_context(file_change, docs)
```

## Troubleshooting

### OpenAI API Errors

```bash
# Check API key is set
echo $OPENAI_API_KEY

# Test connection
python -c "from openai import OpenAI; OpenAI().models.list()"
```

### Empty Results

- Check documents were indexed: `ls doc_index/`
- Verify query is relevant to document content
- Try broader queries
- Check `--top-k` parameter

### Slow Indexing

- Reduce `chunk_size` to create fewer chunks
- Use smaller batches
- Check OpenAI API rate limits

### Memory Issues

- Reduce `chunk_size` and `chunk_overlap`
- Index documents in smaller batches
- Use a machine with more RAM

## Future Enhancements

- [ ] Support for other embedding models (local, Cohere, etc.)
- [ ] Advanced reranking with cross-encoders
- [ ] Caching for frequent queries
- [ ] Multi-language support
- [ ] Image and diagram extraction
- [ ] Code snippet extraction and indexing
- [ ] Integration with Jira for ticket context

## License

[Your License]
