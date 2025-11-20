"""
Unit tests for Memory Models
"""

import pytest
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.memory_models import Session, Conversation, Turn, AgentState, ContextSummary


class TestSession:
    """Test Session model"""

    def test_session_creation(self):
        """Test creating a session"""
        session = Session(user_preferences={'theme': 'dark'}, status='active')

        assert session.session_id is not None
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_active, datetime)
        assert session.user_preferences == {'theme': 'dark'}
        assert session.status == 'active'

    def test_session_to_dict(self):
        """Test session serialization"""
        session = Session(user_preferences={'test': 'value'})
        data = session.to_dict()

        assert 'session_id' in data
        assert 'created_at' in data
        assert 'user_preferences' in data
        assert data['user_preferences'] == {'test': 'value'}

    def test_session_from_dict(self):
        """Test session deserialization"""
        session = Session(user_preferences={'key': 'value'})
        data = session.to_dict()

        restored = Session.from_dict(data)

        assert restored.session_id == session.session_id
        assert restored.user_preferences == session.user_preferences


class TestConversation:
    """Test Conversation model"""

    def test_conversation_creation(self):
        """Test creating a conversation"""
        conv = Conversation(
            session_id='test-session',
            directive='Create a function',
            status='active'
        )

        assert conv.conversation_id is not None
        assert conv.session_id == 'test-session'
        assert conv.directive == 'Create a function'
        assert conv.status == 'active'

    def test_conversation_to_dict(self):
        """Test conversation serialization"""
        conv = Conversation(session_id='session-1', directive='Test directive')
        data = conv.to_dict()

        assert 'conversation_id' in data
        assert 'session_id' in data
        assert 'directive' in data
        assert data['directive'] == 'Test directive'


class TestTurn:
    """Test Turn model"""

    def test_turn_creation(self):
        """Test creating a turn"""
        turn = Turn(
            conversation_id='conv-1',
            turn_number=1,
            agent='beatrice',
            content='This is a response',
            metadata={'model': 'gpt-4'}
        )

        assert turn.turn_id is not None
        assert turn.conversation_id == 'conv-1'
        assert turn.turn_number == 1
        assert turn.agent == 'beatrice'
        assert turn.content == 'This is a response'
        assert turn.metadata['model'] == 'gpt-4'

    def test_turn_to_dict(self):
        """Test turn serialization"""
        turn = Turn(
            conversation_id='conv-1',
            turn_number=2,
            agent='codey',
            content='Implementation here'
        )
        data = turn.to_dict()

        assert 'turn_id' in data
        assert 'agent' in data
        assert data['agent'] == 'codey'
        assert data['turn_number'] == 2


class TestAgentState:
    """Test AgentState model"""

    def test_agent_state_creation(self):
        """Test creating agent state"""
        state = AgentState(
            session_id='session-1',
            agent='beatrice',
            state_data={'interaction_count': 5}
        )

        assert state.state_id is not None
        assert state.session_id == 'session-1'
        assert state.agent == 'beatrice'
        assert state.state_data['interaction_count'] == 5

    def test_agent_state_to_dict(self):
        """Test agent state serialization"""
        state = AgentState(
            session_id='session-1',
            agent='codey',
            state_data={'preferred_topics': {'python': 10}}
        )
        data = state.to_dict()

        assert 'state_id' in data
        assert 'agent' in data
        assert 'state_data' in data
        assert data['state_data']['preferred_topics']['python'] == 10


class TestContextSummary:
    """Test ContextSummary model"""

    def test_context_summary_creation(self):
        """Test creating context summary"""
        summary = ContextSummary(
            session_id='session-1',
            summary_text='Summary of conversations',
            conversation_count=5
        )

        assert summary.summary_id is not None
        assert summary.session_id == 'session-1'
        assert summary.summary_text == 'Summary of conversations'
        assert summary.conversation_count == 5

    def test_context_summary_to_dict(self):
        """Test context summary serialization"""
        summary = ContextSummary(
            session_id='session-1',
            summary_text='Test summary'
        )
        data = summary.to_dict()

        assert 'summary_id' in data
        assert 'summary_text' in data
        assert data['summary_text'] == 'Test summary'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
