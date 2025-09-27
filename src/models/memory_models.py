"""
CCC Stage 2 - Memory Data Models
Version: 1.0
Author: Phase 2 Implementation
"""

from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import json
import uuid


@dataclass
class Session:
    """Represents a CCC memory session"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    status: str = 'active'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat(),
            'user_preferences': self.user_preferences,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Create Session from dictionary"""
        return cls(
            session_id=data['session_id'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_active=datetime.fromisoformat(data['last_active']),
            user_preferences=data.get('user_preferences', {}),
            status=data.get('status', 'active')
        )


@dataclass
class Conversation:
    """Represents a conversation within a session"""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ''
    created_at: datetime = field(default_factory=datetime.utcnow)
    directive: str = ''
    status: str = 'active'
    context_summary: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'conversation_id': self.conversation_id,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'directive': self.directive,
            'status': self.status,
            'context_summary': self.context_summary
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create Conversation from dictionary"""
        return cls(
            conversation_id=data['conversation_id'],
            session_id=data['session_id'],
            created_at=datetime.fromisoformat(data['created_at']),
            directive=data['directive'],
            status=data.get('status', 'active'),
            context_summary=data.get('context_summary', '')
        )


@dataclass
class Turn:
    """Represents a single turn in a conversation"""
    turn_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ''
    turn_number: int = 0
    agent: str = ''
    content: str = ''
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'turn_id': self.turn_id,
            'conversation_id': self.conversation_id,
            'turn_number': self.turn_number,
            'agent': self.agent,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Turn':
        """Create Turn from dictionary"""
        return cls(
            turn_id=data['turn_id'],
            conversation_id=data['conversation_id'],
            turn_number=data['turn_number'],
            agent=data['agent'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )


@dataclass
class AgentState:
    """Represents the persistent state of an agent"""
    state_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ''
    agent: str = ''
    state_data: Dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'state_id': self.state_id,
            'session_id': self.session_id,
            'agent': self.agent,
            'state_data': self.state_data,
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """Create AgentState from dictionary"""
        return cls(
            state_id=data['state_id'],
            session_id=data['session_id'],
            agent=data['agent'],
            state_data=data.get('state_data', {}),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )


@dataclass
class ContextSummary:
    """Represents a context summary for efficient retrieval"""
    summary_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ''
    summary_text: str = ''
    created_at: datetime = field(default_factory=datetime.utcnow)
    conversation_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'summary_id': self.summary_id,
            'session_id': self.session_id,
            'summary_text': self.summary_text,
            'created_at': self.created_at.isoformat(),
            'conversation_count': self.conversation_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextSummary':
        """Create ContextSummary from dictionary"""
        return cls(
            summary_id=data['summary_id'],
            session_id=data['session_id'],
            summary_text=data['summary_text'],
            created_at=datetime.fromisoformat(data['created_at']),
            conversation_count=data.get('conversation_count', 0)
        )