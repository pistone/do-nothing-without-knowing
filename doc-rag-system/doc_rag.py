#!/usr/bin/env python3
"""
Document RAG system - Main script.

Usage:
    # Index documents
    python doc_rag.py index --docs-dir /path/to/docs

    # Query documents
    python doc_rag.py query "How do we handle authentication?"

    # Show document links
    python doc_rag.py links path/to/doc.md
"""

import argparse
import sys
from pathlib import Path

# Will be imported from the files we created
from doc_indexer import DocumentIndexer
from doc_retriever import DocumentRetriever, format_context_for_agent


def cmd_index(args):
    """Index documents."""
    indexer = DocumentIndexer(
        docs_dir=Path(args.docs_dir),
        db_path=Path(args.db_path),
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    
    indexer.index_documents(force_reindex=args.force)
    print(f"\n✓ Documents indexed to {args.db_path}")


def cmd_query(args):
    """Query documents."""
    retriever = DocumentRetriever(db_path=Path(args.db_path))
    
    print(f"\n🔍 Query: {args.query}")
    print("=" * 80)
    
    docs = retriever.retrieve(
        query=args.query,
        top_k=args.top_k,
        use_graph=args.use_graph,
        max_hops=args.max_hops
    )
    
    if not docs:
        print("No relevant documents found.")
        return
    
    print(f"\nFound {len(docs)} relevant documents:\n")
    
    for i, doc in enumerate(docs, 1):
        print(f"\n{'─' * 80}")
        print(f"[{i}] {doc.doc_title} - {doc.section}")
        print(f"    File: {doc.file_path}")
        print(f"    Score: {doc.score:.3f} | Method: {doc.retrieval_method}")
        print(f"{'─' * 80}")
        
        # Print first 500 chars
        content = doc.content[:500]
        if len(doc.content) > 500:
            content += "..."
        print(content)
    
    if args.format_for_llm:
        print("\n\n" + "=" * 80)
        print("FORMATTED FOR LLM:")
        print("=" * 80)
        print(retriever.format_for_llm(docs))


def cmd_links(args):
    """Show document links."""
    retriever = DocumentRetriever(db_path=Path(args.db_path))
    
    links = retriever.get_document_links(args.file_path)
    
    print(f"\nLinks for: {args.file_path}")
    print("=" * 80)
    
    if links['outgoing']:
        print(f"\nOutgoing links ({len(links['outgoing'])}):")
        for link in links['outgoing']:
            print(f"  → {link}")
    else:
        print("\nNo outgoing links")
    
    if links['incoming']:
        print(f"\nIncoming links ({len(links['incoming'])}):")
        for link in links['incoming']:
            print(f"  ← {link}")
    else:
        print("\nNo incoming links")


def cmd_search_title(args):
    """Search by title."""
    retriever = DocumentRetriever(db_path=Path(args.db_path))
    
    matches = retriever.find_by_title(args.title)
    
    print(f"\nDocuments matching '{args.title}':")
    print("=" * 80)
    
    if matches:
        for path in matches:
            node = retriever.doc_graph[path]
            print(f"  • {node['title']}")
            print(f"    {path}")
    else:
        print("No matches found")


def main():
    parser = argparse.ArgumentParser(
        description='Document RAG system for cross-referenced markdown files'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Index command
    index_parser = subparsers.add_parser('index', help='Index documents')
    index_parser.add_argument(
        '--docs-dir',
        required=True,
        help='Directory containing markdown files'
    )
    index_parser.add_argument(
        '--db-path',
        default='./doc_index',
        help='Path to store index (default: ./doc_index)'
    )
    index_parser.add_argument(
        '--chunk-size',
        type=int,
        default=1000,
        help='Chunk size in characters (default: 1000)'
    )
    index_parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=200,
        help='Chunk overlap in characters (default: 200)'
    )
    index_parser.add_argument(
        '--force',
        action='store_true',
        help='Force reindex even if files unchanged'
    )
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query documents')
    query_parser.add_argument('query', help='Search query')
    query_parser.add_argument(
        '--db-path',
        default='./doc_index',
        help='Path to index (default: ./doc_index)'
    )
    query_parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of results (default: 5)'
    )
    query_parser.add_argument(
        '--no-graph',
        dest='use_graph',
        action='store_false',
        help='Disable graph traversal'
    )
    query_parser.add_argument(
        '--max-hops',
        type=int,
        default=2,
        help='Maximum graph hops (default: 2)'
    )
    query_parser.add_argument(
        '--format-for-llm',
        action='store_true',
        help='Format output for LLM consumption'
    )
    
    # Links command
    links_parser = subparsers.add_parser('links', help='Show document links')
    links_parser.add_argument('file_path', help='Relative path to document')
    links_parser.add_argument(
        '--db-path',
        default='./doc_index',
        help='Path to index (default: ./doc_index)'
    )
    
    # Search title command
    title_parser = subparsers.add_parser('search-title', help='Search by title')
    title_parser.add_argument('title', help='Title or partial title')
    title_parser.add_argument(
        '--db-path',
        default='./doc_index',
        help='Path to index (default: ./doc_index)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Dispatch to command handler
    if args.command == 'index':
        cmd_index(args)
    elif args.command == 'query':
        cmd_query(args)
    elif args.command == 'links':
        cmd_links(args)
    elif args.command == 'search-title':
        cmd_search_title(args)


if __name__ == '__main__':
    main()
