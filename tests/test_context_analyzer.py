"""
Unit tests for Context Analyzer
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.context_analyzer import ContextAnalyzer


class TestContextAnalyzer:
    """Test the ContextAnalyzer class"""

    @pytest.fixture
    def analyzer(self):
        """Create a ContextAnalyzer instance"""
        return ContextAnalyzer()

    def test_extract_key_topics(self, analyzer):
        """Test extracting key topics from text"""
        text = """
        Python programming language is great for data science and machine learning.
        Python has excellent libraries like pandas and numpy for data analysis.
        """
        topics = analyzer.extract_key_topics(text)

        assert isinstance(topics, list)
        assert 'python' in topics
        assert 'data' in topics
        # Stop words should not be included
        assert 'the' not in topics
        assert 'is' not in topics

    def test_extract_key_topics_empty(self, analyzer):
        """Test extracting topics from empty text"""
        topics = analyzer.extract_key_topics("")
        assert topics == []

    def test_calculate_relevance_score(self, analyzer):
        """Test relevance score calculation"""
        current = "Create a Python function to validate email addresses"
        historical = {
            'directive': 'Write a Python function for email validation',
            'created_at': datetime.utcnow()
        }

        score = analyzer.calculate_relevance_score(current, historical)

        assert 0 <= score <= 1
        assert score > 0.2  # Should have some relevance (common words: python, function, email, validation)

    def test_calculate_relevance_score_unrelated(self, analyzer):
        """Test relevance score for unrelated content"""
        current = "Create a database schema"
        historical = {
            'directive': 'Write JavaScript animations',
            'created_at': datetime.utcnow()
        }

        score = analyzer.calculate_relevance_score(current, historical)

        assert 0 <= score <= 1
        assert score < 0.3  # Should be low relevance

    def test_time_decay(self, analyzer):
        """Test that older conversations have lower relevance"""
        current = "Python validation function"

        recent = {
            'directive': 'Python validation function',
            'created_at': datetime.utcnow()
        }

        old = {
            'directive': 'Python validation function',
            'created_at': datetime.utcnow() - timedelta(hours=48)
        }

        recent_score = analyzer.calculate_relevance_score(current, recent)
        old_score = analyzer.calculate_relevance_score(current, old)

        assert recent_score > old_score

    def test_summarize_conversation_sequence(self, analyzer):
        """Test conversation summarization"""
        turns = [
            {
                'agent': 'beatrice',
                'content': 'We need to create a Python function for email validation using regex patterns'
            },
            {
                'agent': 'codey',
                'content': 'Here is the Python function implementation with regex for email validation'
            }
        ]

        summary = analyzer.summarize_conversation_sequence(turns)

        assert isinstance(summary, str)
        assert 'beatrice' in summary.lower() or 'codey' in summary.lower()
        assert len(summary) > 0

    def test_summarize_empty_sequence(self, analyzer):
        """Test summarization of empty sequence"""
        summary = analyzer.summarize_conversation_sequence([])
        assert summary == ""

    def test_filter_relevant_context(self, analyzer):
        """Test filtering conversations by relevance"""
        current = "Create email validation"

        conversations = [
            {
                'directive': 'Write email validator function',
                'created_at': datetime.utcnow()
            },
            {
                'directive': 'Build authentication system',
                'created_at': datetime.utcnow()
            },
            {
                'directive': 'Create database migration',
                'created_at': datetime.utcnow()
            }
        ]

        # Set low threshold for testing
        analyzer.similarity_threshold = 0.1
        relevant = analyzer.filter_relevant_context(current, conversations)

        assert len(relevant) > 0
        # Most relevant should be email validator (results are sorted by relevance)
        # Check that the first result has the highest relevance score
        if len(relevant) > 1:
            assert relevant[0]['relevance_score'] >= relevant[1]['relevance_score']
        # Email validator should be in the results somewhere
        email_found = any('email' in conv['directive'].lower() for conv in relevant)
        assert email_found, "Email validator should be in relevant results"
        # Each should have relevance_score
        for conv in relevant:
            assert 'relevance_score' in conv

    def test_identify_learning_patterns(self, analyzer):
        """Test identifying agent learning patterns"""
        history = [
            {
                'content': 'This is a detailed response about Python programming and data structures',
                'metadata': {'execution_time_ms': 1200}
            },
            {
                'content': 'Another response discussing Python and algorithms',
                'metadata': {'execution_time_ms': 1500}
            }
        ]

        patterns = analyzer.identify_learning_patterns(history)

        assert 'response_lengths' in patterns
        assert 'preferred_topics' in patterns
        assert 'average_response_length' in patterns
        assert len(patterns['response_lengths']) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
