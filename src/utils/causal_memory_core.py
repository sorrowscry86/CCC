"""
CCC Stage 2 - Causal Memory Core Integration
Version: 2.1
Author: Enhanced Phase 2 Implementation with Causal Reasoning

This module integrates the Causal Memory Core functionality into the existing
CCC memory system, providing cause-and-effect context recognition.
"""

from __future__ import annotations

import os
import sys
import logging
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, List, Optional, Dict

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

try:
    import duckdb
    import openai
    CAUSAL_DEPENDENCIES_AVAILABLE = True
except ImportError:
    CAUSAL_DEPENDENCIES_AVAILABLE = False
    logger.warning("DuckDB or OpenAI not available. Causal Memory Core features disabled.")


# P4.3: Singleton embedding model to avoid loading on every request
_EMBEDDING_MODEL_SINGLETON = None
_EMBEDDING_MODEL_LOCK = None

def get_embedding_model():
    """
    Get or create singleton embedding model instance
    P4.3: Prevents loading model on every CausalMemoryCore instantiation
    """
    global _EMBEDDING_MODEL_SINGLETON, _EMBEDDING_MODEL_LOCK
    import threading

    if _EMBEDDING_MODEL_LOCK is None:
        _EMBEDDING_MODEL_LOCK = threading.Lock()

    if _EMBEDDING_MODEL_SINGLETON is None:
        with _EMBEDDING_MODEL_LOCK:
            # Double-check after acquiring lock
            if _EMBEDDING_MODEL_SINGLETON is None:
                try:
                    logger.info("Loading embedding model (singleton)...")
                    _EMBEDDING_MODEL_SINGLETON = SentenceTransformer('all-MiniLM-L6-v2')
                    logger.info("Embedding model loaded successfully")
                except Exception as e:
                    logger.error(f"Failed to load embedding model: {e}")
                    return None

    return _EMBEDDING_MODEL_SINGLETON


@dataclass
class CausalEvent:
    """Represents a causal event in the memory system"""
    event_id: int
    timestamp: datetime
    effect_text: str
    embedding: List[float]
    cause_id: Optional[int] = None
    relationship_text: Optional[str] = None


class CausalMemoryCore:
    """
    Causal Memory Core implementation for CCC Stage 2
    
    Provides semantic recall with causal chain narration, integrating:
    - Event-based memory storage
    - Causal relationship detection
    - Narrative chain reconstruction
    - Semantic search with embeddings
    """
    
    def __init__(self, db_path: str = "ccc_causal_memory.db", 
                 similarity_threshold: float = 0.5,
                 max_potential_causes: int = 5,
                 time_decay_hours: int = 24):
        self.db_path = db_path
        self.similarity_threshold = similarity_threshold
        self.max_potential_causes = max_potential_causes
        self.time_decay_hours = time_decay_hours
        self.llm_model = "gpt-3.5-turbo"
        self.llm_temperature = 0.7
        
        self.conn: Optional[Any] = None
        self.llm: Optional[Any] = None
        self.embedder: Optional[Any] = None
        
        if CAUSAL_DEPENDENCIES_AVAILABLE:
            self._initialize()
        else:
            logger.warning("Causal Memory Core initialized in fallback mode")
    
    def _initialize(self):
        """Initialize the causal memory core"""
        try:
            # Initialize DuckDB connection
            self.conn = duckdb.connect(self.db_path)
            self._initialize_database()
            
            # Initialize OpenAI client
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                openai.api_key = api_key
                self.llm = openai
            else:
                logger.warning("OPENAI_API_KEY not set. LLM features disabled.")

            # P4.3: Use singleton embedding model instead of loading every time
            self.embedder = get_embedding_model()

            logger.info("Causal Memory Core initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Causal Memory Core: {e}")
            self.conn = None
            self.llm = None
            self.embedder = None
    
    def _initialize_database(self):
        """Initialize the causal events database"""
        if not self.conn:
            return
            
        # Create events table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS causal_events (
                event_id INTEGER PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                effect_text VARCHAR NOT NULL,
                embedding DOUBLE[] NOT NULL,
                cause_id INTEGER,
                relationship_text VARCHAR,
                session_id VARCHAR,
                conversation_id VARCHAR
            )
        """)
        
        # Create indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_causal_events_timestamp ON causal_events(timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_causal_events_session ON causal_events(session_id)")
        
        # Create sequence for IDs
        try:
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS causal_events_seq START 1")
        except Exception:
            # Fallback sequence table
            self.conn.execute("CREATE TABLE IF NOT EXISTS _causal_events_seq (val INTEGER)")
            seq_row = self.conn.execute("SELECT COUNT(*) FROM _causal_events_seq").fetchone()
            if seq_row and seq_row[0] == 0:
                self.conn.execute("INSERT INTO _causal_events_seq VALUES (1)")
    
    def add_event(self, effect_text: str, session_id: str = None, 
                  conversation_id: str = None) -> bool:
        """
        Add a new causal event to memory
        
        Args:
            effect_text: Description of the event
            session_id: Optional session ID for CCC integration
            conversation_id: Optional conversation ID for CCC integration
            
        Returns:
            True if event was added successfully
        """
        if not self._is_available():
            return False
            
        try:
            # Generate embedding
            encoded = self.embedder.encode(effect_text)
            if hasattr(encoded, "tolist"):
                effect_embedding = [float(x) for x in encoded.tolist()]
            else:
                effect_embedding = [float(x) for x in list(encoded)]
            
            # Find potential causes
            potential_causes = self._find_potential_causes(effect_embedding, effect_text)
            
            # Determine causal relationship
            cause_id: Optional[int] = None
            relationship_text: Optional[str] = None
            
            for cause in potential_causes:
                relationship = self._judge_causality(cause, effect_text)
                if relationship:
                    cause_id = cause.event_id
                    relationship_text = relationship
                    break
            
            # Insert event
            self._insert_event(effect_text, effect_embedding, cause_id, 
                             relationship_text, session_id, conversation_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add causal event: {e}")
            return False
    
    def get_causal_context(self, query: str, session_id: str = None) -> str:
        """
        Get causal context for a query, returning narrative chains
        
        Args:
            query: Search query
            session_id: Optional session filter
            
        Returns:
            Narrative description of causal chains related to the query
        """
        if not self._is_available():
            return "Causal memory not available"
            
        try:
            # Generate query embedding
            q_vec = self.embedder.encode(query)
            if hasattr(q_vec, "tolist"):
                q_emb = [float(x) for x in q_vec.tolist()]
            else:
                q_emb = [float(x) for x in list(q_vec)]
            
            # Find most relevant event
            target = self._find_most_relevant_event(q_emb, session_id)
            if not target:
                return "No relevant causal context found in memory."
            
            # Build causal chain (ascend to root causes)
            ancestry: List[CausalEvent] = [target]
            seen = {target.event_id}
            curr = target
            
            while curr.cause_id is not None:
                cause = self._get_event_by_id(curr.cause_id)
                if not cause:
                    break
                if cause.event_id in seen:
                    break
                ancestry.append(cause)
                seen.add(cause.event_id)
                curr = cause
            
            path = list(reversed(ancestry))
            
            # Add limited consequences (effects of the target event)
            consequences: List[CausalEvent] = []
            frontier = target
            for _ in range(2):  # Limit to 2 consequence levels
                child = self._find_direct_effect(frontier.event_id)
                if not child or child.event_id in {e.event_id for e in path}:
                    break
                consequences.append(child)
                frontier = child
            
            # Format as narrative
            return self._format_chain_as_narrative(path + consequences)
            
        except Exception as e:
            logger.error(f"Failed to get causal context: {e}")
            return f"Error retrieving causal context: {str(e)}"
    
    def _find_potential_causes(self, effect_embedding: List[float], 
                              effect_text: str) -> List[CausalEvent]:
        """Find potential causal events that could have led to this effect"""
        if not self.conn:
            return []
            
        # Look for recent events within time decay window
        time_threshold = datetime.now() - timedelta(hours=self.time_decay_hours)
        
        rows = self.conn.execute("""
            SELECT event_id, timestamp, effect_text, embedding, cause_id, 
                   relationship_text, session_id, conversation_id
            FROM causal_events 
            WHERE timestamp > ? 
            ORDER BY timestamp DESC 
            LIMIT 50
        """, [time_threshold]).fetchall()
        
        if not rows:
            return []
        
        # Calculate similarity scores
        eff_np = np.array(effect_embedding, dtype=float)
        candidates: List[tuple[float, CausalEvent]] = []
        
        for r in rows:
            # Skip identical events
            if r[2] == effect_text:
                continue
                
            emb_np = np.array(r[3], dtype=float)
            if emb_np.shape != eff_np.shape:
                continue
            
            # Calculate cosine similarity
            denom = np.linalg.norm(eff_np) * np.linalg.norm(emb_np)
            if denom == 0:
                continue
                
            similarity = float(np.dot(eff_np, emb_np) / denom)
            
            if similarity >= self.similarity_threshold:
                event = CausalEvent(
                    event_id=r[0], timestamp=r[1], effect_text=r[2], 
                    embedding=r[3], cause_id=r[4], relationship_text=r[5]
                )
                candidates.append((similarity, event))
        
        # Sort by similarity and timestamp
        candidates.sort(key=lambda x: (x[0], x[1].timestamp), reverse=True)
        return [e for _, e in candidates[:self.max_potential_causes]]
    
    def _judge_causality(self, cause_event: CausalEvent, effect_text: str) -> Optional[str]:
        """Use LLM to judge if there's a causal relationship between events"""
        if not self.llm:
            return None
            
        prompt = (
            f'Based on the preceding event: "{cause_event.effect_text}", '
            f'did it directly lead to the following event: "{effect_text}"?\n\n'
            f'If yes, briefly explain the causal relationship in one sentence. '
            f'If no, respond with "No."'
        )
        
        try:
            response = self.llm.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.llm_temperature,
                max_tokens=100,
            )
            
            result = str(response.choices[0].message.content).strip()
            
            if result.lower() == "no." or result.lower().startswith("no"):
                return None
            
            return result
            
        except Exception as e:
            logger.error(f"LLM causality judgment failed: {e}")
            return None
    
    def _insert_event(self, effect_text: str, embedding: List[float], 
                     cause_id: Optional[int], relationship_text: Optional[str],
                     session_id: str = None, conversation_id: str = None):
        """Insert a new causal event into the database"""
        if not self.conn:
            return
            
        # Get next ID
        try:
            seq_row = self.conn.execute("SELECT nextval('causal_events_seq')").fetchone()
            if seq_row:
                next_id = seq_row[0]
            else:
                raise RuntimeError("Sequence failed")
        except Exception:
            # Fallback sequence
            row = self.conn.execute("SELECT val FROM _causal_events_seq").fetchone()
            if not row:
                self.conn.execute("INSERT INTO _causal_events_seq VALUES (1)")
                row = (1,)
            next_id = row[0]
            self.conn.execute("UPDATE _causal_events_seq SET val = val + 1")
        
        # Insert event
        self.conn.execute("""
            INSERT INTO causal_events 
            (event_id, timestamp, effect_text, embedding, cause_id, 
             relationship_text, session_id, conversation_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [next_id, datetime.now(), effect_text, embedding, cause_id, 
              relationship_text, session_id, conversation_id])
    
    def _get_event_by_id(self, event_id: int) -> Optional[CausalEvent]:
        """Get a causal event by its ID"""
        if not self.conn:
            return None
            
        row = self.conn.execute("""
            SELECT event_id, timestamp, effect_text, embedding, cause_id, 
                   relationship_text, session_id, conversation_id
            FROM causal_events WHERE event_id = ?
        """, [event_id]).fetchone()
        
        if row:
            return CausalEvent(
                event_id=row[0], timestamp=row[1], effect_text=row[2],
                embedding=row[3], cause_id=row[4], relationship_text=row[5]
            )
        return None
    
    def _find_most_relevant_event(self, query_embedding: List[float],
                                 session_id: str = None,
                                 max_results: int = 1000) -> Optional[CausalEvent]:
        """
        Find the most relevant event for a query

        P4.8: Added max_results limit to prevent full table scans
        """
        if not self.conn:
            return None

        # Build query with optional session filter
        base_query = """
            SELECT event_id, timestamp, effect_text, embedding, cause_id,
                   relationship_text, session_id, conversation_id
            FROM causal_events
        """
        params = []

        if session_id:
            base_query += " WHERE session_id = ?"
            params.append(session_id)
        else:
            # P4.8: Warn about full table scan and limit results
            logger.warning(f"Full table scan on causal_events (no session filter), limiting to {max_results} rows")

        # P4.8: Add ORDER BY and LIMIT to prevent scanning entire table
        base_query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(max_results)

        rows = self.conn.execute(base_query, params).fetchall()
        
        if not rows:
            return None
        
        # Find best similarity match
        best_sim = -1.0
        best_event: Optional[CausalEvent] = None
        q_np = np.array(query_embedding, dtype=float)
        
        for r in rows:
            emb = np.array(r[3], dtype=float)
            if emb.shape != q_np.shape:
                continue
                
            denom = np.linalg.norm(q_np) * np.linalg.norm(emb)
            if denom == 0:
                continue
                
            similarity = float(np.dot(q_np, emb) / denom)
            
            # Prefer newer events if similarity is equal
            newer = (best_event and r[1] > best_event.timestamp)
            if (similarity > best_sim) or (similarity == best_sim and newer):
                best_sim = similarity
                best_event = CausalEvent(
                    event_id=r[0], timestamp=r[1], effect_text=r[2],
                    embedding=r[3], cause_id=r[4], relationship_text=r[5]
                )
        
        return best_event if best_sim >= self.similarity_threshold else None
    
    def _find_direct_effect(self, cause_event_id: int) -> Optional[CausalEvent]:
        """Find the direct effect of a causal event"""
        if not self.conn:
            return None
            
        row = self.conn.execute("""
            SELECT event_id, timestamp, effect_text, embedding, cause_id, 
                   relationship_text, session_id, conversation_id
            FROM causal_events 
            WHERE cause_id = ? 
            ORDER BY timestamp ASC 
            LIMIT 1
        """, [cause_event_id]).fetchone()
        
        if row:
            return CausalEvent(
                event_id=row[0], timestamp=row[1], effect_text=row[2],
                embedding=row[3], cause_id=row[4], relationship_text=row[5]
            )
        return None
    
    def _format_chain_as_narrative(self, chain: List[CausalEvent]) -> str:
        """Format a causal chain as a coherent narrative"""
        if not chain:
            return "No causal chain found."
        
        if len(chain) == 1:
            return f"Initially, {chain[0].effect_text}."
        
        # Build causal narrative
        narrative = f"Initially, {chain[0].effect_text}."
        clauses: List[str] = []
        
        for i in range(1, len(chain)):
            event = chain[i]
            relationship = f" ({event.relationship_text})" if event.relationship_text else ""
            
            if i == 1:
                clauses.append(f"This led to {event.effect_text}{relationship}")
            else:
                clauses.append(f"which in turn caused {event.effect_text}{relationship}")
        
        if clauses:
            narrative += " " + ", ".join(clauses) + "."
        
        return narrative
    
    def _is_available(self) -> bool:
        """Check if causal memory core is available"""
        return (CAUSAL_DEPENDENCIES_AVAILABLE and 
                self.conn is not None and 
                self.embedder is not None)
    
    def close(self):
        """Close the causal memory core"""
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.close()
        except Exception:
            pass