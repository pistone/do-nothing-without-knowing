"""
Document RAG system for cross-referenced markdown files.

Combines:
1. Vector embeddings for semantic search
2. Graph structure for link following
3. Metadata for filtering
"""

import re
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
import hashlib
import json

# ChromaDB for vector storage
import chromadb
from chromadb.config import Settings

# OpenAI for embeddings (can swap for others)
from openai import OpenAI


@dataclass
class Document:
    """Represents a documentation chunk."""
    id: str
    content: str
    metadata: Dict
    embedding: Optional[List[float]] = None


@dataclass
class DocumentNode:
    """Represents a document in the graph."""
    file_path: str
    title: str
    content: str
    outgoing_links: Set[str]  # Links from this doc to others
    incoming_links: Set[str]  # Links to this doc from others
    metadata: Dict


class DocumentIndexer:
    """
    Index markdown documents with hybrid retrieval:
    - Vector embeddings for semantic search
    - Graph structure for link traversal
    """
    
    def __init__(
        self,
        docs_dir: Path,
        db_path: Path = Path("./doc_index"),
        embedding_model: str = "text-embedding-3-small",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize the indexer.
        
        Args:
            docs_dir: Root directory containing markdown files
            db_path: Path to store the vector database
            embedding_model: OpenAI embedding model to use
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks
        """
        self.docs_dir = Path(docs_dir)
        self.db_path = Path(db_path)
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize OpenAI client
        self.openai_client = OpenAI()
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"description": "Cross-referenced markdown documentation"}
        )
        
        # Document graph (file_path -> DocumentNode)
        self.doc_graph: Dict[str, DocumentNode] = {}
        
        # Cache for file content hashes (to detect changes)
        self.content_hashes: Dict[str, str] = {}
        self._load_hashes()
    
    def _load_hashes(self):
        """Load cached content hashes."""
        hash_file = self.db_path / "content_hashes.json"
        if hash_file.exists():
            with open(hash_file) as f:
                self.content_hashes = json.load(f)
    
    def _save_hashes(self):
        """Save content hashes."""
        hash_file = self.db_path / "content_hashes.json"
        hash_file.parent.mkdir(parents=True, exist_ok=True)
        with open(hash_file, 'w') as f:
            json.dump(self.content_hashes, f, indent=2)
    
    def _compute_hash(self, content: str) -> str:
        """Compute hash of content."""
        return hashlib.md5(content.encode()).hexdigest()
    
    def index_documents(self, force_reindex: bool = False):
        """
        Index all markdown documents.
        
        Args:
            force_reindex: If True, reindex even if unchanged
        """
        print(f"Indexing documents from {self.docs_dir}...")
        
        # Find all markdown files
        md_files = list(self.docs_dir.rglob("*.md"))
        print(f"Found {len(md_files)} markdown files")
        
        # Build document graph
        self._build_document_graph(md_files)
        
        # Chunk and embed documents
        documents = []
        for file_path, node in self.doc_graph.items():
            # Check if file changed
            content_hash = self._compute_hash(node.content)
            
            if not force_reindex and self.content_hashes.get(file_path) == content_hash:
                print(f"  Skipping {file_path} (unchanged)")
                continue
            
            print(f"  Indexing {file_path}")
            
            # Chunk the document
            chunks = self._chunk_document(node)
            documents.extend(chunks)
            
            # Update hash
            self.content_hashes[file_path] = content_hash
        
        if documents:
            # Generate embeddings in batches
            print(f"Generating embeddings for {len(documents)} chunks...")
            self._embed_documents(documents)
            
            # Add to vector database
            print("Adding to vector database...")
            self._add_to_vectordb(documents)
        
        # Save hashes
        self._save_hashes()
        
        # Save graph
        self._save_graph()
        
        print(f"✓ Indexing complete! {len(documents)} chunks indexed.")
    
    def _build_document_graph(self, md_files: List[Path]):
        """Build graph of document links."""
        self.doc_graph = {}
        
        # First pass: create nodes
        for file_path in md_files:
            rel_path = str(file_path.relative_to(self.docs_dir))
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title (first # heading or filename)
            title = self._extract_title(content, file_path.name)
            
            # Extract metadata from frontmatter if present
            metadata = self._extract_metadata(content)
            metadata['file_path'] = rel_path
            
            self.doc_graph[rel_path] = DocumentNode(
                file_path=rel_path,
                title=title,
                content=content,
                outgoing_links=set(),
                incoming_links=set(),
                metadata=metadata
            )
        
        # Second pass: extract links
        for rel_path, node in self.doc_graph.items():
            links = self._extract_links(node.content, rel_path)
            node.outgoing_links = links
            
            # Add incoming links
            for target in links:
                if target in self.doc_graph:
                    self.doc_graph[target].incoming_links.add(rel_path)
    
    def _extract_title(self, content: str, filename: str) -> str:
        """Extract document title."""
        # Look for first # heading
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # Fallback to filename
        return filename.replace('.md', '').replace('_', ' ').replace('-', ' ').title()
    
    def _extract_metadata(self, content: str) -> Dict:
        """Extract YAML frontmatter if present."""
        metadata = {}
        
        # Check for YAML frontmatter
        if content.startswith('---'):
            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if match:
                # Simple key-value parsing (full YAML parser would be better)
                frontmatter = match.group(1)
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
        
        return metadata
    
    def _extract_links(self, content: str, current_file: str) -> Set[str]:
        """Extract markdown links to other documents."""
        links = set()
        
        # Find markdown links: [text](path)
        pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        
        for match in re.finditer(pattern, content):
            link_text, link_path = match.groups()
            
            # Skip external links
            if link_path.startswith('http://') or link_path.startswith('https://'):
                continue
            
            # Skip anchors only
            if link_path.startswith('#'):
                continue
            
            # Remove anchor if present
            link_path = link_path.split('#')[0]
            
            # Resolve relative path
            current_dir = Path(current_file).parent
            resolved = (current_dir / link_path).resolve()
            
            try:
                rel_path = str(resolved.relative_to(self.docs_dir.resolve()))
                links.add(rel_path)
            except ValueError:
                # Link goes outside docs_dir, skip it
                pass
        
        return links
    
    def _chunk_document(self, node: DocumentNode) -> List[Document]:
        """Chunk document into smaller pieces."""
        chunks = []
        content = node.content
        
        # Simple chunking by character count
        # Better approach: chunk by section (## headings)
        sections = self._split_by_sections(content)
        
        for i, (section_title, section_content) in enumerate(sections):
            # Further split if section is too large
            if len(section_content) <= self.chunk_size:
                chunk_parts = [section_content]
            else:
                chunk_parts = self._split_text(section_content)
            
            for j, chunk_text in enumerate(chunk_parts):
                chunk_id = f"{node.file_path}__chunk_{i}_{j}"
                
                # Add context to chunk
                full_text = f"# {node.title}\n\n"
                if section_title:
                    full_text += f"## {section_title}\n\n"
                full_text += chunk_text
                
                metadata = {
                    **node.metadata,
                    'chunk_id': chunk_id,
                    'section': section_title or 'Introduction',
                    'doc_title': node.title,
                }
                
                chunks.append(Document(
                    id=chunk_id,
                    content=full_text,
                    metadata=metadata
                ))
        
        return chunks
    
    def _split_by_sections(self, content: str) -> List[Tuple[str, str]]:
        """Split content by ## headings."""
        sections = []
        
        # Split by ## headings
        parts = re.split(r'\n##\s+(.+)\n', content)
        
        # First part is before any ## heading
        if parts[0].strip():
            sections.append(('', parts[0].strip()))
        
        # Rest are (heading, content) pairs
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                heading = parts[i].strip()
                content_part = parts[i + 1].strip()
                sections.append((heading, content_part))
        
        return sections
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending
                sentence_end = text.rfind('. ', start, end)
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunks.append(text[start:end].strip())
            start = end - self.chunk_overlap
        
        return chunks
    
    def _embed_documents(self, documents: List[Document], batch_size: int = 100):
        """Generate embeddings for documents."""
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            texts = [doc.content for doc in batch]
            
            # Call OpenAI API
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            
            # Assign embeddings
            for doc, embedding_data in zip(batch, response.data):
                doc.embedding = embedding_data.embedding
    
    def _add_to_vectordb(self, documents: List[Document]):
        """Add documents to ChromaDB."""
        self.collection.add(
            ids=[doc.id for doc in documents],
            documents=[doc.content for doc in documents],
            embeddings=[doc.embedding for doc in documents],
            metadatas=[doc.metadata for doc in documents]
        )
    
    def _save_graph(self):
        """Save document graph."""
        graph_file = self.db_path / "doc_graph.json"
        
        # Convert to serializable format
        graph_data = {
            path: {
                'title': node.title,
                'file_path': node.file_path,
                'outgoing_links': list(node.outgoing_links),
                'incoming_links': list(node.incoming_links),
                'metadata': node.metadata
            }
            for path, node in self.doc_graph.items()
        }
        
        with open(graph_file, 'w') as f:
            json.dump(graph_data, f, indent=2)
    
    def load_graph(self):
        """Load document graph."""
        graph_file = self.db_path / "doc_graph.json"
        
        if not graph_file.exists():
            return
        
        with open(graph_file) as f:
            graph_data = json.load(f)
        
        self.doc_graph = {
            path: DocumentNode(
                file_path=data['file_path'],
                title=data['title'],
                content='',  # Not loaded
                outgoing_links=set(data['outgoing_links']),
                incoming_links=set(data['incoming_links']),
                metadata=data['metadata']
            )
            for path, data in graph_data.items()
        }
