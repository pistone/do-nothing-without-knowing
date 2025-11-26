"""
Retriever for RAG system with hybrid search.

Combines:
1. Semantic search (vector similarity)
2. Graph traversal (following links)
3. Ranking and reranking
"""

from typing import List, Dict, Set, Optional
from pathlib import Path
from dataclasses import dataclass
import json

import chromadb
from chromadb.config import Settings
from openai import OpenAI


@dataclass
class RetrievedDoc:
    """A retrieved document chunk."""
    content: str
    file_path: str
    doc_title: str
    section: str
    score: float
    retrieval_method: str  # 'semantic', 'graph', 'hybrid'
    metadata: Dict


class DocumentRetriever:
    """
    Retrieve relevant documents using hybrid approach.
    """
    
    def __init__(
        self,
        db_path: Path = Path("./doc_index"),
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize retriever.
        
        Args:
            db_path: Path to the document index
            embedding_model: OpenAI embedding model
        """
        self.db_path = Path(db_path)
        self.embedding_model = embedding_model
        
        # Initialize OpenAI
        self.openai_client = OpenAI()
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.chroma_client.get_collection("documents")
        
        # Load document graph
        self.doc_graph = self._load_graph()
    
    def _load_graph(self) -> Dict:
        """Load document graph."""
        graph_file = self.db_path / "doc_graph.json"
        
        if not graph_file.exists():
            return {}
        
        with open(graph_file) as f:
            return json.load(f)
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        use_graph: bool = True,
        max_hops: int = 2
    ) -> List[RetrievedDoc]:
        """
        Retrieve relevant documents.
        
        Args:
            query: Search query
            top_k: Number of documents to return
            use_graph: Whether to use graph traversal
            max_hops: Maximum hops for graph traversal
            
        Returns:
            List of retrieved documents
        """
        # Step 1: Semantic search
        semantic_results = self._semantic_search(query, top_k=top_k)
        
        if not use_graph:
            return semantic_results
        
        # Step 2: Graph traversal from seed documents
        graph_results = self._graph_traversal(
            seed_docs=[r.file_path for r in semantic_results],
            max_hops=max_hops,
            max_results=top_k * 2
        )
        
        # Step 3: Combine and deduplicate
        combined = self._combine_results(semantic_results, graph_results)
        
        # Step 4: Rerank
        reranked = self._rerank(query, combined, top_k=top_k)
        
        return reranked
    
    def _semantic_search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[RetrievedDoc]:
        """Perform semantic search using embeddings."""
        # Generate query embedding
        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=[query]
        )
        query_embedding = response.data[0].embedding
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Convert to RetrievedDoc objects
        docs = []
        for i in range(len(results['ids'][0])):
            docs.append(RetrievedDoc(
                content=results['documents'][0][i],
                file_path=results['metadatas'][0][i]['file_path'],
                doc_title=results['metadatas'][0][i]['doc_title'],
                section=results['metadatas'][0][i].get('section', ''),
                score=1.0 - results['distances'][0][i],  # Convert distance to similarity
                retrieval_method='semantic',
                metadata=results['metadatas'][0][i]
            ))
        
        return docs
    
    def _graph_traversal(
        self,
        seed_docs: List[str],
        max_hops: int = 2,
        max_results: int = 10
    ) -> List[RetrievedDoc]:
        """
        Traverse document graph from seed documents.
        
        Args:
            seed_docs: List of file paths to start from
            max_hops: Maximum number of hops
            max_results: Maximum documents to return
            
        Returns:
            List of documents found via graph traversal
        """
        visited = set(seed_docs)
        to_visit = [(doc, 0) for doc in seed_docs]  # (doc_path, hop_count)
        related_docs = []
        
        while to_visit and len(related_docs) < max_results:
            current_doc, hop_count = to_visit.pop(0)
            
            if hop_count >= max_hops:
                continue
            
            # Get document node
            if current_doc not in self.doc_graph:
                continue
            
            node = self.doc_graph[current_doc]
            
            # Follow outgoing links
            for linked_doc in node['outgoing_links']:
                if linked_doc not in visited:
                    visited.add(linked_doc)
                    to_visit.append((linked_doc, hop_count + 1))
                    related_docs.append((linked_doc, hop_count + 1))
            
            # Also consider incoming links (documents that reference this one)
            for linked_doc in node['incoming_links']:
                if linked_doc not in visited:
                    visited.add(linked_doc)
                    to_visit.append((linked_doc, hop_count + 1))
                    related_docs.append((linked_doc, hop_count + 1))
        
        # Retrieve content for these documents
        docs = []
        for doc_path, hop_count in related_docs[:max_results]:
            # Query ChromaDB for chunks from this document
            results = self.collection.get(
                where={"file_path": doc_path},
                limit=3  # Get a few chunks from each document
            )
            
            if results['ids']:
                for i in range(len(results['ids'])):
                    # Score based on hop distance (closer = higher score)
                    score = 1.0 / (hop_count + 1)
                    
                    docs.append(RetrievedDoc(
                        content=results['documents'][i],
                        file_path=results['metadatas'][i]['file_path'],
                        doc_title=results['metadatas'][i]['doc_title'],
                        section=results['metadatas'][i].get('section', ''),
                        score=score,
                        retrieval_method='graph',
                        metadata=results['metadatas'][i]
                    ))
        
        return docs
    
    def _combine_results(
        self,
        semantic_results: List[RetrievedDoc],
        graph_results: List[RetrievedDoc]
    ) -> List[RetrievedDoc]:
        """Combine and deduplicate results."""
        seen_chunks = set()
        combined = []
        
        # Add semantic results first (higher priority)
        for doc in semantic_results:
            chunk_id = doc.metadata.get('chunk_id', '')
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                combined.append(doc)
        
        # Add graph results
        for doc in graph_results:
            chunk_id = doc.metadata.get('chunk_id', '')
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                # Boost score slightly for hybrid retrieval
                doc.retrieval_method = 'hybrid'
                doc.score = doc.score * 0.8  # Slight penalty for graph-only
                combined.append(doc)
        
        return combined
    
    def _rerank(
        self,
        query: str,
        docs: List[RetrievedDoc],
        top_k: int = 5
    ) -> List[RetrievedDoc]:
        """
        Rerank documents (placeholder for more sophisticated reranking).
        
        For now, just sorts by score.
        Could use:
        - Cross-encoder models
        - LLM-based reranking
        - Query-document similarity
        """
        # Sort by score
        ranked = sorted(docs, key=lambda x: x.score, reverse=True)
        return ranked[:top_k]
    
    def get_document_links(self, file_path: str) -> Dict[str, List[str]]:
        """
        Get incoming and outgoing links for a document.
        
        Args:
            file_path: Path to document
            
        Returns:
            Dict with 'outgoing' and 'incoming' link lists
        """
        if file_path not in self.doc_graph:
            return {'outgoing': [], 'incoming': []}
        
        node = self.doc_graph[file_path]
        return {
            'outgoing': node['outgoing_links'],
            'incoming': node['incoming_links']
        }
    
    def find_by_title(self, title_query: str) -> List[str]:
        """
        Find documents by title (fuzzy match).
        
        Args:
            title_query: Title or partial title to search
            
        Returns:
            List of matching file paths
        """
        matches = []
        title_lower = title_query.lower()
        
        for path, node in self.doc_graph.items():
            if title_lower in node['title'].lower():
                matches.append(path)
        
        return matches
    
    def format_for_llm(self, docs: List[RetrievedDoc]) -> str:
        """
        Format retrieved documents for LLM context.
        
        Args:
            docs: Retrieved documents
            
        Returns:
            Formatted string for LLM prompt
        """
        formatted = []
        
        for i, doc in enumerate(docs, 1):
            formatted.append(f"""
Document {i}: {doc.doc_title}
Section: {doc.section}
Source: {doc.file_path}
Retrieval: {doc.retrieval_method} (score: {doc.score:.3f})

{doc.content}

---
""")
        
        return "\n".join(formatted)


def format_context_for_agent(
    retriever: DocumentRetriever,
    query: str,
    top_k: int = 5
) -> str:
    """
    Convenience function to retrieve and format docs for an agent.
    
    Args:
        retriever: DocumentRetriever instance
        query: Query string
        top_k: Number of documents to retrieve
        
    Returns:
        Formatted context string
    """
    docs = retriever.retrieve(query, top_k=top_k, use_graph=True)
    return retriever.format_for_llm(docs)
