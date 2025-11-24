"""
CCC Stage 2 - Enhanced Memory Service with Causal Reasoning
Version: 2.1
Author: Enhanced Phase 2 Implementation with Causal Memory Core
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..memory.database import MemoryDAL
from ..models.memory_models import Session, Conversation, Turn, AgentState
from ..utils.encryption import EncryptionService
from ..utils.context_analyzer import ContextAnalyzer
from ..utils.causal_memory_core import CausalMemoryCore
from ..utils.performance_utils import BoundedSessionCache, truncate_context, limit_query_results, background_task

logger = logging.getLogger(__name__)


class MemoryService:
    """Enhanced memory operations for CCC with causal reasoning capabilities"""

    def __init__(self, dal: MemoryDAL):
        self.dal = dal
        self.context_analyzer = ContextAnalyzer()
        self.encryption_service = EncryptionService()
        self.causal_memory = CausalMemoryCore()
        # P4.5: Use bounded LRU cache instead of unbounded dict
        self._session_cache = BoundedSessionCache(maxsize=1000, ttl=300)
        logger.info("MemoryService initialized with bounded session cache")
    
    async def initialize_session(self, user_preferences: Dict[str, Any] = None) -> Session:
        """Create new session with optional user context"""
        try:
            session = Session(
                user_preferences=user_preferences or {},
                status='active'
            )
            
            success = await self.dal.create_session(session)
            if success:
                # Cache the session (P4.5: using bounded cache)
                self._session_cache.set(session.session_id, session)

                # Record session creation as causal event
                self.causal_memory.add_event(
                    f"New CCC session created with preferences: {user_preferences or 'default'}",
                    session_id=session.session_id
                )

                logger.info(f"New session created: {session.session_id}")
                return session
            else:
                raise Exception("Failed to create session in database")
                
        except Exception as e:
            logger.error(f"Failed to initialize session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID with caching (P4.5: using bounded cache)"""
        try:
            # Check cache first
            cached_session = self._session_cache.get(session_id)
            if cached_session:
                return cached_session

            # Get from database
            session = await self.dal.get_session(session_id)
            if session:
                # Update cache
                self._session_cache.set(session_id, session)

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
        """Store a single turn with encryption, validation, and causal tracking"""
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
                # Record as causal event for enhanced reasoning
                agent_title = {
                    'beatrice': 'Supervisor',
                    'codey': 'Executor',
                    'wykeve': 'Prime Architect'
                }.get(agent, agent.title())
                
                causal_event_text = f"{agent_title} {agent} responded in conversation: {content[:100]}..."
                
                self.causal_memory.add_event(
                    causal_event_text,
                    session_id=session_id,
                    conversation_id=conversation_id
                )
                
                # Update agent learning asynchronously (P4.10: proper background task)
                self._update_agent_learning_background(session_id, agent, content, metadata or {})
            
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
        """Retrieve contextually relevant conversation history with causal reasoning"""
        try:
            context = {
                'session_id': session_id,
                'relevant_conversations': [],
                'agent_states': {},
                'context_summary': '',
                'causal_narrative': '',
                'domain': '',  # Add domain field for structured context
                'total_conversations': 0
            }
            
            # Get recent conversations using traditional method
            conversations = await self.dal.get_conversations(session_id, limit=20)
            context['total_conversations'] = len(conversations)
            
            if conversations:
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
                
                # Filter for relevance using traditional method
                relevant_conversations = self.context_analyzer.filter_relevant_context(
                    current_directive, 
                    conversation_dicts
                )
                
                # Get turns for relevant conversations (limited) - optimized to avoid N+1 queries
                top_relevant = relevant_conversations[:5]  # Limit to top 5 relevant
                if top_relevant:
                    # Batch fetch all turns in a single query
                    conversation_ids = [conv['conversation_id'] for conv in top_relevant]
                    turns_by_conversation = await self.dal.get_turns_batch(conversation_ids)

                    # Attach turns to each conversation
                    for conv_dict in top_relevant:
                        turns = turns_by_conversation.get(conv_dict['conversation_id'], [])
                        conv_dict['turns'] = [turn.to_dict() for turn in turns[-max_context_turns:]]

                context['relevant_conversations'] = relevant_conversations
                
                # Generate traditional context summary
                if relevant_conversations:
                    all_turns = []
                    for conv in relevant_conversations:
                        all_turns.extend(conv.get('turns', []))
                    
                    context['context_summary'] = self.context_analyzer.summarize_conversation_sequence(all_turns)
            
            # CRITICAL REFACTOR: Two-part query sequence for domain context preservation
            try:
                # Part A: Domain Identification Query
                domain_query = "Based on the session history, identify the primary technical domain of this project (e.g., 'Software Engineering in Python', 'Creative Writing', 'Biological System Design')."
                domain = self.causal_memory.get_causal_context(
                    domain_query,
                    session_id=session_id
                )
                
                # Part B: Contextual Narrative Query (existing)
                causal_narrative = self.causal_memory.get_causal_context(
                    current_directive, 
                    session_id=session_id
                )
                
                # Store both domain and narrative for structured context construction
                # P4.9: Truncate large contexts to save tokens
                context['domain'] = truncate_context(domain, max_tokens=200)
                context['causal_narrative'] = truncate_context(causal_narrative, max_tokens=1500)
                logger.info(f"Enhanced context with domain '{domain[:50]}...' and causal narrative for session {session_id}")
            except Exception as e:
                logger.warning(f"Failed to get causal narrative: {e}")
                context['domain'] = "Technical domain not available"
                context['causal_narrative'] = "Causal reasoning not available"
            
            # Get agent states
            for agent in ['beatrice', 'codey']:
                agent_state = await self.dal.get_agent_state(session_id, agent)
                if agent_state:
                    context['agent_states'][agent] = agent_state.state_data
                else:
                    context['agent_states'][agent] = {}
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get relevant context: {e}")
            return {
                'session_id': session_id,
                'relevant_conversations': [],
                'agent_states': {},
                'context_summary': '',
                'causal_narrative': 'Error retrieving causal context',
                'total_conversations': 0
            }
    
    @background_task
    async def _update_agent_learning_background(
        self,
        session_id: str,
        agent: str,
        content: str,
        metadata: dict
    ):
        """Background task wrapper for agent learning updates"""
        await self._update_agent_learning(session_id, agent, content, metadata)

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
            
            # Record agent learning as causal event
            learning_summary = f"Agent {agent} learning updated: {state_data['interaction_count']} interactions, avg length {state_data['average_response_length']:.1f} words"
            self.causal_memory.add_event(
                learning_summary,
                session_id=session_id
            )
            
            # Store updated state
            success = await self.dal.update_agent_state(session_id, agent, state_data)
            
            if success:
                logger.debug(f"Updated learning data for agent {agent} in session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update agent learning: {e}")
            return False
    
    async def create_conversation(self, session_id: str, directive: str) -> Optional[Conversation]:
        """Create a new conversation with causal event tracking"""
        try:
            conversation = Conversation(
                session_id=session_id,
                directive=directive,
                status='active'
            )
            
            success = await self.dal.create_conversation(conversation)
            if success:
                # Record conversation creation as causal event
                self.causal_memory.add_event(
                    f"New conversation started with directive: {directive}",
                    session_id=session_id,
                    conversation_id=conversation.conversation_id
                )
                
                return conversation
            return None
            
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            return None
    
    async def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Clean up old sessions"""
        try:
            deleted_count = await self.dal.cleanup_expired_sessions(max_age_days)
            
            # Record cleanup as causal event
            if deleted_count > 0:
                self.causal_memory.add_event(f"Cleaned up {deleted_count} expired sessions")
            
            logger.info(f"Cleaned up {deleted_count} old sessions")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return 0
    
    def close(self):
        """Close memory service and causal memory core"""
        try:
            self.causal_memory.close()
        except Exception as e:
            logger.error(f"Error closing causal memory core: {e}")
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.close()
        except Exception:
            pass