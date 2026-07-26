# agents/knowledge_agent.py
"""
Knowledge Agent — 8th distinct AI agent in AgentCare.

Uses RAG (Retrieval-Augmented Generation) to answer patient questions
about hospital policies, procedures, departments, and general information.

This agent does NOT provide medical advice - only administrative and
informational content from official hospital documents.
"""

import logging
from typing import Dict, Any, Optional, List
from services.llm_service import llm_service
from services.rag_service import rag_service

logger = logging.getLogger(__name__)


KNOWLEDGE_SYSTEM_PROMPT = """You are the AgentCare Knowledge Agent — a helpful 
assistant that answers questions about hospital information using retrieved 
documents.

You will receive:
- A user's question
- Relevant document chunks retrieved from the hospital knowledge base

Your job:
1. Read the retrieved chunks carefully
2. Answer the user's question using ONLY information from the chunks
3. Cite the source document(s) used
4. Be concise, clear, and friendly

STRICT RULES:
- You NEVER give medical advice, diagnoses, or prescriptions
- You NEVER interpret symptoms or medical results
- You ONLY answer administrative/informational questions
- If chunks don't contain the answer, say so honestly
- If the question is medical (diagnosis/treatment), politely redirect
  to consulting a doctor
- Never invent information not in the retrieved chunks

Respond ONLY in this exact JSON format:
{
  "answer": "your friendly, direct answer to the question (2-4 sentences)",
  "detailed_answer": "longer answer with more detail if useful (optional, can be empty)",
  "sources_used": ["source1.txt", "source2.txt"],
  "found_relevant_info": true or false,
  "safety_note": "optional safety reminder if applicable, else null"
}"""


class KnowledgeAgent:
    """
    Knowledge Agent — Uses RAG to answer hospital info questions.
    
    Distinct responsibilities:
    - Retrieves relevant hospital documents via vector search
    - Uses LLM to synthesize accurate answers from documents
    - Provides source citations
    - Maintains safety boundaries (no medical advice)
    """

    def __init__(self):
        self.llm = llm_service
        self.rag = rag_service
        self._rag_initialized = False

    def _ensure_rag_ready(self):
        """Lazy-initialize RAG service on first use."""
        if not self._rag_initialized:
            logger.info("[KNOWLEDGE AGENT] Initializing RAG service...")
            self.rag.initialize()
            self._rag_initialized = True

    def answer_question(
        self,
        question: str,
        category_filter: Optional[str] = None,
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """
        Main entry point for knowledge questions.
        
        Args:
            question: The user's question
            category_filter: Optional filter (policies, procedures, etc.)
            top_k: Number of chunks to retrieve
            
        Returns:
            Dict with answer, sources, and metadata
        """
        try:
            logger.info(
                f"[KNOWLEDGE AGENT] Processing question: '{question[:80]}'"
            )
            
            # Ensure RAG is ready
            self._ensure_rag_ready()
            
            # Retrieve relevant chunks
            chunks = self.rag.retrieve(
                query=question,
                top_k=top_k,
                category_filter=category_filter,
            )
            
            if not chunks:
                logger.warning("[KNOWLEDGE AGENT] No relevant chunks found")
                return {
                    "success": True,
                    "answer": (
                        "I don't have specific information about that in our "
                        "knowledge base. Please contact our reception at "
                        "+91-80-4567-8900 for assistance."
                    ),
                    "sources": [],
                    "chunks_used": [],
                    "found_relevant_info": False,
                    "safety_note": None,
                }
            
            # Format chunks for LLM
            context_text = self._format_chunks_for_llm(chunks)
            
            # Ask LLM to synthesize answer
            llm_result = self.llm.chat_json(
                system_prompt=KNOWLEDGE_SYSTEM_PROMPT,
                user_message=(
                    f"PATIENT QUESTION:\n\"{question}\"\n\n"
                    f"RETRIEVED KNOWLEDGE BASE CHUNKS:\n\n"
                    f"{context_text}\n\n"
                    f"Answer the patient's question using ONLY the above chunks. "
                    f"Cite the source files you used."
                ),
            )
            
            # Extract fields safely
            # Extract fields safely with better fallback
            answer = llm_result.get("answer", "")
            detailed = llm_result.get("detailed_answer", "")
            sources = llm_result.get("sources_used", [])
            found_info = llm_result.get("found_relevant_info", True)
            safety_note = llm_result.get("safety_note")
            
            # If LLM JSON parsing failed but we have chunks, create answer from chunks
            if not answer or answer == "" or "error" in str(llm_result).lower():
                # Fallback: Build answer directly from top chunk
                if chunks:
                    top_chunk = chunks[0]["content"]
                    # Take first 300 chars as answer
                    answer = top_chunk[:300].strip()
                    if len(top_chunk) > 300:
                        answer += "..."
                    detailed = "This information was retrieved directly from our knowledge base."
                    found_info = True
                    logger.info("[KNOWLEDGE AGENT] Used fallback: direct chunk as answer")
                else:
                    answer = "I couldn't find specific information about that. Please contact reception at +91-80-4567-8900."
            
            # Extract clean source list from chunks (fallback if LLM misses)
            if not sources:
                sources = list(set(c["source"] for c in chunks))
            
            logger.info(
                f"[KNOWLEDGE AGENT] Answered from {len(sources)} source(s), "
                f"top_score={chunks[0]['score'] if chunks else 0}"
            )
            
            return {
                "success": True,
                "answer": answer,
                "detailed_answer": detailed,
                "sources": sources,
                "chunks_used": [
                    {
                        "source": c["source"],
                        "category": c["category"],
                        "score": c["score"],
                        "preview": c["content"][:200] + "..." if len(c["content"]) > 200 else c["content"],
                    }
                    for c in chunks
                ],
                "found_relevant_info": found_info,
                "safety_note": safety_note,
                "top_similarity_score": chunks[0]["score"] if chunks else 0,
            }
        
        except Exception as e:
            logger.error(f"[KNOWLEDGE AGENT] Failed: {e}")
            return {
                "success": False,
                "answer": (
                    f"Sorry, I encountered an error looking that up. "
                    f"Please try again or contact our reception. Error: {str(e)}"
                ),
                "sources": [],
                "chunks_used": [],
                "found_relevant_info": False,
                "safety_note": None,
            }

    def _format_chunks_for_llm(self, chunks: List[Dict[str, Any]]) -> str:
        """Formats retrieved chunks as readable text for LLM."""
        lines = []
        for i, chunk in enumerate(chunks, 1):
            lines.append(f"--- CHUNK {i} (source: {chunk['source']}, relevance: {chunk['score']}) ---")
            lines.append(chunk["content"])
            lines.append("")
        return "\n".join(lines)

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Returns statistics about the knowledge base."""
        try:
            self._ensure_rag_ready()
            return self.rag.get_stats()
        except Exception as e:
            logger.error(f"[KNOWLEDGE AGENT] Stats failed: {e}")
            return {"error": str(e)}


# ── Singleton instance ────────────────────────────────────────
knowledge_agent = KnowledgeAgent()