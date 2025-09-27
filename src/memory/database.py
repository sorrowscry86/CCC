"""
CCC Stage 2 - Memory Data Access Layer (DAL)
Version: 1.0
Author: Phase 2 Implementation
"""

import os
import json
import logging
import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiosqlite
from pathlib import Path

from ..models.memory_models import Session, Conversation, Turn, AgentState, ContextSummary

logger = logging.getLogger(__name__)


class MemoryDAL:
    """Data Access Layer for CCC memory operations"""
    
    def __init__(self, db_path: str = "ccc_memory.db"):
        self.db_path = db_path
        self.schema_path = Path(__file__).parent.parent.parent / "database" / "schema" / "schema.sql"
        
    async def initialize_database(self) -> bool:
        """Initialize database with schema"""
        try:
            # Create database directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
            
            async with aiosqlite.connect(self.db_path) as db:
                # Enable foreign keys
                await db.execute("PRAGMA foreign_keys = ON")
                
                # Read and execute schema
                if self.schema_path.exists():
                    schema_sql = self.schema_path.read_text()
                    await db.executescript(schema_sql)
                    await db.commit()
                    logger.info(f"Database initialized at {self.db_path}")
                else:
                    logger.error(f"Schema file not found at {self.schema_path}")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    # Session Management
    async def create_session(self, session: Session) -> bool:
        """Create a new session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO sessions (session_id, created_at, last_active, user_preferences, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    session.session_id,
                    session.created_at,
                    session.last_active,
                    json.dumps(session.user_preferences),
                    session.status
                ))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT session_id, created_at, last_active, user_preferences, status
                    FROM sessions WHERE session_id = ?
                """, (session_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return Session(
                            session_id=row[0],
                            created_at=datetime.fromisoformat(row[1]),
                            last_active=datetime.fromisoformat(row[2]),
                            user_preferences=json.loads(row[3] or '{}'),
                            status=row[4]
                        )
            return None
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity timestamp"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE sessions SET last_active = ? WHERE session_id = ?
                """, (datetime.utcnow(), session_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")
            return False
    
    # Conversation Management
    async def create_conversation(self, conversation: Conversation) -> bool:
        """Create a new conversation"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO conversations (conversation_id, session_id, created_at, directive, status, context_summary)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    conversation.conversation_id,
                    conversation.session_id,
                    conversation.created_at,
                    conversation.directive,
                    conversation.status,
                    conversation.context_summary
                ))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            return False
    
    async def get_conversations(self, session_id: str, limit: int = 10) -> List[Conversation]:
        """Get conversations for a session"""
        try:
            conversations = []
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT conversation_id, session_id, created_at, directive, status, context_summary
                    FROM conversations 
                    WHERE session_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (session_id, limit)) as cursor:
                    async for row in cursor:
                        conversations.append(Conversation(
                            conversation_id=row[0],
                            session_id=row[1],
                            created_at=datetime.fromisoformat(row[2]),
                            directive=row[3],
                            status=row[4],
                            context_summary=row[5] or ''
                        ))
            return conversations
        except Exception as e:
            logger.error(f"Failed to get conversations: {e}")
            return []
    
    # Turn Management
    async def create_turn(self, turn: Turn) -> bool:
        """Create a new turn"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO turns (turn_id, conversation_id, turn_number, agent, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    turn.turn_id,
                    turn.conversation_id,
                    turn.turn_number,
                    turn.agent,
                    turn.content,
                    turn.timestamp,
                    json.dumps(turn.metadata)
                ))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to create turn: {e}")
            return False
    
    async def get_turns(self, conversation_id: str) -> List[Turn]:
        """Get all turns for a conversation"""
        try:
            turns = []
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT turn_id, conversation_id, turn_number, agent, content, timestamp, metadata
                    FROM turns 
                    WHERE conversation_id = ? 
                    ORDER BY turn_number ASC
                """, (conversation_id,)) as cursor:
                    async for row in cursor:
                        turns.append(Turn(
                            turn_id=row[0],
                            conversation_id=row[1],
                            turn_number=row[2],
                            agent=row[3],
                            content=row[4],
                            timestamp=datetime.fromisoformat(row[5]),
                            metadata=json.loads(row[6] or '{}')
                        ))
            return turns
        except Exception as e:
            logger.error(f"Failed to get turns: {e}")
            return []
    
    # Agent State Management
    async def get_agent_state(self, session_id: str, agent: str) -> Optional[AgentState]:
        """Get agent state for a session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT state_id, session_id, agent, state_data, updated_at
                    FROM agent_states 
                    WHERE session_id = ? AND agent = ?
                """, (session_id, agent)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return AgentState(
                            state_id=row[0],
                            session_id=row[1],
                            agent=row[2],
                            state_data=json.loads(row[3] or '{}'),
                            updated_at=datetime.fromisoformat(row[4])
                        )
            return None
        except Exception as e:
            logger.error(f"Failed to get agent state: {e}")
            return None
    
    async def update_agent_state(self, session_id: str, agent: str, state_data: Dict[str, Any]) -> bool:
        """Update or create agent state"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Use UPSERT (INSERT OR REPLACE)
                await db.execute("""
                    INSERT OR REPLACE INTO agent_states (state_id, session_id, agent, state_data, updated_at)
                    VALUES (
                        COALESCE((SELECT state_id FROM agent_states WHERE session_id = ? AND agent = ?), ?),
                        ?, ?, ?, ?
                    )
                """, (
                    session_id, agent, str(uuid.uuid4()),  # Generate new ID if not exists
                    session_id, agent, json.dumps(state_data), datetime.utcnow()
                ))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update agent state: {e}")
            return False
    
    # Context Summary Management
    async def create_context_summary(self, summary: ContextSummary) -> bool:
        """Create a context summary"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO context_summaries (summary_id, session_id, summary_text, created_at, conversation_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    summary.summary_id,
                    summary.session_id,
                    summary.summary_text,
                    summary.created_at,
                    summary.conversation_count
                ))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to create context summary: {e}")
            return False
    
    async def get_latest_context_summary(self, session_id: str) -> Optional[ContextSummary]:
        """Get the latest context summary for a session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT summary_id, session_id, summary_text, created_at, conversation_count
                    FROM context_summaries 
                    WHERE session_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, (session_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return ContextSummary(
                            summary_id=row[0],
                            session_id=row[1],
                            summary_text=row[2],
                            created_at=datetime.fromisoformat(row[3]),
                            conversation_count=row[4]
                        )
            return None
        except Exception as e:
            logger.error(f"Failed to get context summary: {e}")
            return None
    
    async def cleanup_expired_sessions(self, max_age_days: int = 30) -> int:
        """Clean up expired sessions and related data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    DELETE FROM sessions WHERE last_active < ?
                """, (cutoff_date,))
                deleted_count = cursor.rowcount
                await db.commit()
                logger.info(f"Cleaned up {deleted_count} expired sessions")
                return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0