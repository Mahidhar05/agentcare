# services/rag_service.py
"""
RAG (Retrieval-Augmented Generation) Service for AgentCare.
Powers the Knowledge Agent - answers questions from hospital documents.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval-Augmented Generation service.
    
    - Loads hospital knowledge base documents
    - Creates embeddings using sentence-transformers
    - Stores in ChromaDB vector database
    - Retrieves relevant chunks for user queries
    """

    def __init__(self, knowledge_base_dir: str = "knowledge_base"):
        self.kb_dir = knowledge_base_dir
        self.collection = None
        self.embedder = None
        self._initialized = False
        
        # Chunk configuration
        self.chunk_size = 500        # characters per chunk
        self.chunk_overlap = 100      # overlap between chunks
        self.top_k = 3               # number of relevant chunks to retrieve

    def initialize(self):
        """Lazy initialization — loads models and creates vector DB."""
        if self._initialized:
            return
        
        try:
            logger.info("[RAG] Initializing RAG service...")
            
            # Import here to speed up app startup
            import chromadb
            from chromadb.config import Settings
            from sentence_transformers import SentenceTransformer
            
            # Initialize sentence transformer (embedding model)
            logger.info("[RAG] Loading embedding model (first time may take 1-2 min)...")
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
            
            # Initialize ChromaDB (persistent local storage)
            chroma_client = chromadb.PersistentClient(
                path="./chroma_db",
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create or get collection
            try:
                self.collection = chroma_client.get_collection("agentcare_kb")
                logger.info(
                    f"[RAG] Loaded existing collection with "
                    f"{self.collection.count()} chunks"
                )
            except Exception:
                self.collection = chroma_client.create_collection(
                    name="agentcare_kb",
                    metadata={"description": "AgentCare Hospital Knowledge Base"}
                )
                logger.info("[RAG] Created new empty collection")
            
            self._initialized = True
            
            # Auto-index if collection is empty
            if self.collection.count() == 0:
                logger.info("[RAG] Collection is empty, auto-indexing documents...")
                self.index_documents()
            
        except Exception as e:
            logger.error(f"[RAG] Initialization failed: {e}")
            raise

    def index_documents(self) -> Dict[str, Any]:
        """
        Loads all .txt files from knowledge_base/, chunks them,
        embeds them, and stores in ChromaDB.
        """
        if not self._initialized:
            self.initialize()
        
        logger.info("[RAG] Starting document indexing...")
        
        kb_path = Path(self.kb_dir)
        if not kb_path.exists():
            logger.error(f"[RAG] Knowledge base directory not found: {self.kb_dir}")
            return {"success": False, "error": "kb_dir_not_found"}
        
        # Clear existing data
        try:
            existing_ids = self.collection.get()["ids"]
            if existing_ids:
                self.collection.delete(ids=existing_ids)
                logger.info(f"[RAG] Cleared {len(existing_ids)} existing chunks")
        except Exception as e:
            logger.warning(f"[RAG] Could not clear existing: {e}")
        
        # Process all .txt files
        all_chunks = []
        all_metadatas = []
        all_ids = []
        chunk_id = 0
        
        for txt_file in kb_path.rglob("*.txt"):
            try:
                content = txt_file.read_text(encoding="utf-8")
                
                # Determine category from folder
                relative_path = txt_file.relative_to(kb_path)
                parts = relative_path.parts
                category = parts[0] if len(parts) > 1 else "general"
                filename = txt_file.stem
                
                # Chunk the document
                chunks = self._chunk_text(content)
                
                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    all_metadatas.append({
                        "source": str(relative_path),
                        "category": category,
                        "filename": filename,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    })
                    all_ids.append(f"doc_{chunk_id}")
                    chunk_id += 1
                
                logger.info(
                    f"[RAG] Processed {relative_path}: {len(chunks)} chunks"
                )
            
            except Exception as e:
                logger.error(f"[RAG] Failed to process {txt_file}: {e}")
                continue
        
        if not all_chunks:
            logger.warning("[RAG] No chunks to index")
            return {"success": False, "error": "no_chunks"}
        
        # Create embeddings (batch)
        logger.info(f"[RAG] Creating embeddings for {len(all_chunks)} chunks...")
        embeddings = self.embedder.encode(
            all_chunks,
            show_progress_bar=False,
            convert_to_numpy=True,
        ).tolist()
        
        # Store in ChromaDB
        self.collection.add(
            documents=all_chunks,
            embeddings=embeddings,
            metadatas=all_metadatas,
            ids=all_ids,
        )
        
        logger.info(
            f"[RAG] ✅ Indexed {len(all_chunks)} chunks from "
            f"{len(list(kb_path.rglob('*.txt')))} documents"
        )
        
        return {
            "success": True,
            "total_chunks": len(all_chunks),
            "total_documents": len(list(kb_path.rglob("*.txt"))),
        }

    def _chunk_text(self, text: str) -> List[str]:
        """
        Splits text into overlapping chunks.
        Tries to split at paragraph boundaries when possible.
        """
        # First, split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # If paragraph itself is longer than chunk_size, split it
            if len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                # Split long paragraph into chunks
                for i in range(0, len(para), self.chunk_size - self.chunk_overlap):
                    chunks.append(para[i:i + self.chunk_size].strip())
            
            # If adding this paragraph exceeds chunk size, start new chunk
            elif len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            
            # Otherwise, add to current chunk
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        category_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k relevant chunks for a query.
        
        Args:
            query: The user's question
            top_k: Number of chunks to retrieve (default: 3)
            category_filter: Optional filter by category (policies, procedures, etc.)
        
        Returns:
            List of dicts with 'content', 'source', 'category', 'score'
        """
        if not self._initialized:
            self.initialize()
        
        k = top_k or self.top_k
        
        try:
            # Embed the query
            query_embedding = self.embedder.encode(
                query,
                convert_to_numpy=True,
            ).tolist()
            
            # Build filter
            where_filter = None
            if category_filter:
                where_filter = {"category": category_filter}
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_filter,
            )
            
            # Format results
            chunks = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results.get("distances") else 0
                    
                    chunks.append({
                        "content": doc,
                        "source": metadata.get("source", "Unknown"),
                        "category": metadata.get("category", "general"),
                        "filename": metadata.get("filename", "Unknown"),
                        "score": round(1 - distance, 3),  # Convert distance to similarity
                    })
            
            logger.info(
                f"[RAG] Retrieved {len(chunks)} chunks for query: "
                f"'{query[:60]}...'"
            )
            return chunks
        
        except Exception as e:
            logger.error(f"[RAG] Retrieval failed: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics about the knowledge base."""
        if not self._initialized:
            self.initialize()
        
        try:
            total_chunks = self.collection.count()
            
            # Get category breakdown
            all_data = self.collection.get()
            categories = {}
            documents = set()
            
            for metadata in all_data.get("metadatas", []):
                cat = metadata.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1
                documents.add(metadata.get("source", "unknown"))
            
            return {
                "total_chunks": total_chunks,
                "total_documents": len(documents),
                "categories": categories,
                "documents": list(documents),
            }
        except Exception as e:
            logger.error(f"[RAG] Stats failed: {e}")
            return {"error": str(e)}


# ── Singleton instance ────────────────────────────────────────
rag_service = RAGService()