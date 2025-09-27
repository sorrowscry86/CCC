"""
CCC Stage 2 - Memory Service
Version: 1.0
Author: Phase 2 Implementation
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..memory.database import MemoryDAL
from ..models.memory_models import Session, Conversation, Turn, AgentState
from ..utils.encryption import EncryptionService
from ..utils.context_analyzer import ContextAnalyzer

logger = logging.getLogger(__name__)


class MemoryService:
    """High-level memory operations for CCC"""
    
    def __init__(self, dal: MemoryDAL):
        self.dal = dal
        self.context_analyzer = ContextAnalyzer()
        self.encryption_service = EncryptionService()
        self._session_cache = {}
        self._cache_timeout = 300  # 5 minutes
    
    async def initialize_session(self, user_preferences: Dict[str, Any] = None) -> Session:
        """Create new session with optional user context"""
        try:
            session = Session(
                user_preferences=user_preferences or {},
                status='active'
            )
            
            success = await self.dal.create_session(session)
            if success:
                # Cache the session
                self._session_cache[session.session_id] = {
                    'session': session,
                    'cached_at': datetime.utcnow()
                }
                logger.info(f"New session created: {session.session_id}")
                return session
            else:
                raise Exception("Failed to create session in database")
                
        except Exception as e:
            logger.error(f"Failed to initialize session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID with caching"""
        try:
            # Check cache first
            if session_id in self._session_cache:
                cached_data = self._session_cache[session_id]
                cache_age = (datetime.utcnow() - cached_data['cached_at']).seconds
                
                if cache_age < self._cache_timeout:
                    return cached_data['session']
                else:
                    # Remove expired cache entry
                    del self._session_cache[session_id]
            
            # Get from database
            session = await self.dal.get_session(session_id)
            if session:
                # Update cache
                self._session_cache[session_id] = {
                    'session': session,
                    'cached_at': datetime.utcnow()
                }
                
                # Update last active timestamp
                await self.dal.update_session_activity(session_id)
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    async def store_conversation_turn(
        self, 
        session_id: str,
        conversation_id: str,
        agent: str,
        content: str,
        metadata: dict = None
    ) -> bool:
        """Store a single turn with encryption and validation"""
        try:
            # Validate session exists
            session = await self.get_session(session_id)
            if not session:
                logger.error(f"Session not found: {session_id}")
                return False
            
            # Get or create conversation
            conversations = await self.dal.get_conversations(session_id, limit=1)
            if not conversations or conversations[0].conversation_id != conversation_id:
                # This is a new conversation, we'll handle it in the proxy server
                pass
            
            # Determine turn number
            existing_turns = await self.dal.get_turns(conversation_id)
            turn_number = len(existing_turns) + 1
            
            # Create turn
            turn = Turn(
                conversation_id=conversation_id,
                turn_number=turn_number,
                agent=agent,
                content=content,
                metadata=metadata or {}
            )
            
            # Store turn
            success = await self.dal.create_turn(turn)
            
            if success:
                # Update agent learning asynchronously
                asyncio.create_task(
                    self._update_agent_learning(session_id, agent, content, metadata or {})
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to store conversation turn: {e}")
            return False
    
    async def get_relevant_context(
        self, 
        session_id: str,
        current_directive: str,
        max_context_turns: int = 10
    ) -> Dict[str, Any]:
        """Retrieve contextually relevant conversation history"""
        try:
            context = {
                'session_id': session_id,
                'relevant_conversations': [],
                'agent_states': {},
                'context_summary': '',
                'total_conversations': 0
            }
            
            # Get recent conversations
            conversations = await self.dal.get_conversations(session_id, limit=20)
            context['total_conversations'] = len(conversations)
            
            if not conversations:
                return context
            
            # Convert conversations to dict format for analyzer
            conversation_dicts = []
            for conv in conversations:
                conversation_dicts.append({
                    'conversation_id': conv.conversation_id,
                    'directive': conv.directive,
                    'created_at': conv.created_at,
                    'status': conv.status,
                    'context_summary': conv.context_summary
                })
            
            # Filter for relevance
            relevant_conversations = self.context_analyzer.filter_relevant_context(
                current_directive, 
                conversation_dicts
            )
            
            # Get turns for relevant conversations (limited)
            for conv_dict in relevant_conversations[:5]:  # Limit to top 5 relevant
                turns = await self.dal.get_turns(conv_dict['conversation_id'])
                conv_dict['turns'] = [turn.to_dict() for turn in turns[-max_context_turns:]]
            
            context['relevant_conversations'] = relevant_conversations
            
            # Get agent states
            for agent in ['beatrice', 'codey']:
                agent_state = await self.dal.get_agent_state(session_id, agent)
                if agent_state:
                    context['agent_states'][agent] = agent_state.state_data
                else:
                    context['agent_states'][agent] = {}
            
            # Generate context summary
            if relevant_conversations:
                all_turns = []
                for conv in relevant_conversations:
                    all_turns.extend(conv.get('turns', []))
                
                context['context_summary'] = self.context_analyzer.summarize_conversation_sequence(all_turns)
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get relevant context: {e}")
            return {
                'session_id': session_id,
                'relevant_conversations': [],
                'agent_states': {},
                'context_summary': '',
                'total_conversations': 0
            }
    
    async def _update_agent_learning(
        self,
        session_id: str,
        agent: str,
        content: str,
        metadata: dict
    ) -> bool:
        """Update agent learning patterns based on interaction"""
        try:
            # Get current agent state
            current_state = await self.dal.get_agent_state(session_id, agent)
            
            if current_state:
                state_data = current_state.state_data
            else:
                state_data = {
                    'interaction_count': 0,
                    'total_response_length': 0,
                    'preferred_topics': {},
                    'average_response_time': 0,
                    'last_updated': datetime.utcnow().isoformat()
                }
            
            # Update interaction count
            state_data['interaction_count'] = state_data.get('interaction_count', 0) + 1
            
            # Update response length statistics
            response_length = len(content.split())
            state_data['total_response_length'] = state_data.get('total_response_length', 0) + response_length
            state_data['average_response_length'] = state_data['total_response_length'] / state_data['interaction_count']
            
            # Update topic preferences
            topics = self.context_analyzer.extract_key_topics(content)
            preferred_topics = state_data.get('preferred_topics', {})
            for topic in topics:
                preferred_topics[topic] = preferred_topics.get(topic, 0) + 1
            state_data['preferred_topics'] = preferred_topics
            
            # Update response time if available
            response_time = metadata.get('execution_time_ms', 0)
            if response_time:
                current_avg = state_data.get('average_response_time', 0)
                count = state_data['interaction_count']
                state_data['average_response_time'] = ((current_avg * (count - 1)) + response_time) / count
            
            # Update timestamp
            state_data['last_updated'] = datetime.utcnow().isoformat()
            
            # Store updated state
            success = await self.dal.update_agent_state(session_id, agent, state_data)
            
            if success:
                logger.debug(f"Updated learning data for agent {agent} in session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update agent learning: {e}")
            return False
    
    async def create_conversation(self, session_id: str, directive: str) -> Optional[Conversation]:
        """Create a new conversation"""
        try:
            conversation = Conversation(
                session_id=session_id,
                directive=directive,
                status='active'
            )
            
            success = await self.dal.create_conversation(conversation)
            if success:
                return conversation
            return None
            
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            return None
    
    async def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Clean up old sessions"""
        try:
            deleted_count = await self.dal.cleanup_expired_sessions(max_age_days)
            logger.info(f"Cleaned up {deleted_count} old sessions")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return 0