"""
CCC Stage 2 - Context Analyzer
Version: 1.0
Author: Phase 2 Implementation
"""

import re
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from collections import Counter

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    """Analyzes conversations for context extraction and relevance"""
    
    def __init__(self):
        self.similarity_threshold = 0.7
        self.max_context_age_hours = 24
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'shall', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
    
    def extract_key_topics(self, conversation_text: str) -> List[str]:
        """Extract main topics and themes from conversation"""
        try:
            if not conversation_text:
                return []
            
            # Convert to lowercase and extract words
            words = re.findall(r'\b[a-zA-Z]{3,}\b', conversation_text.lower())
            
            # Remove stop words
            meaningful_words = [word for word in words if word not in self.stop_words]
            
            # Count word frequencies
            word_counts = Counter(meaningful_words)
            
            # Return top 10 most frequent words as topics
            top_topics = [word for word, count in word_counts.most_common(10)]
            
            return top_topics
            
        except Exception as e:
            logger.error(f"Failed to extract key topics: {e}")
            return []
    
    def calculate_relevance_score(
        self, 
        current_directive: str,
        historical_conversation: dict
    ) -> float:
        """Calculate relevance score between current and past interactions"""
        try:
            if not current_directive or not historical_conversation:
                return 0.0
            
            # Extract words from current directive
            current_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', current_directive.lower()))
            current_words = current_words - self.stop_words
            
            # Extract words from historical conversation
            historical_text = historical_conversation.get('directive', '')
            historical_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', historical_text.lower()))
            historical_words = historical_words - self.stop_words
            
            # Calculate Jaccard similarity
            if not current_words and not historical_words:
                return 0.0
            
            intersection = current_words.intersection(historical_words)
            union = current_words.union(historical_words)
            
            if not union:
                return 0.0
            
            similarity = len(intersection) / len(union)
            
            # Apply time decay
            conversation_age = datetime.utcnow() - historical_conversation.get('created_at', datetime.utcnow())
            age_hours = conversation_age.total_seconds() / 3600
            
            time_decay = max(0, 1 - (age_hours / self.max_context_age_hours))
            
            return similarity * time_decay
            
        except Exception as e:
            logger.error(f"Failed to calculate relevance score: {e}")
            return 0.0
    
    def summarize_conversation_sequence(self, turns: List[Dict[str, Any]]) -> str:
        """Create concise summary of conversation sequence"""
        try:
            if not turns:
                return ""
            
            # Group turns by agent
            agent_contributions = {}
            for turn in turns:
                agent = turn.get('agent', 'unknown')
                content = turn.get('content', '')
                
                if agent not in agent_contributions:
                    agent_contributions[agent] = []
                agent_contributions[agent].append(content)
            
            # Create summary
            summary_parts = []
            for agent, contributions in agent_contributions.items():
                # Extract key themes from agent's contributions
                combined_text = ' '.join(contributions)
                key_topics = self.extract_key_topics(combined_text)
                
                if key_topics:
                    summary_parts.append(f"{agent.title()}: {', '.join(key_topics[:5])}")
            
            return "; ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Failed to summarize conversation sequence: {e}")
            return ""
    
    def identify_learning_patterns(self, agent_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify patterns in agent responses for learning"""
        try:
            if not agent_history:
                return {}
            
            patterns = {
                'response_lengths': [],
                'common_phrases': [],
                'response_times': [],
                'topic_preferences': {},
                'interaction_success_rate': 0.0
            }
            
            for interaction in agent_history:
                # Analyze response length
                content = interaction.get('content', '')
                patterns['response_lengths'].append(len(content.split()))
                
                # Extract common phrases (2-3 words)
                phrases = re.findall(r'\b\w+\s+\w+(?:\s+\w+)?\b', content.lower())
                patterns['common_phrases'].extend(phrases)
                
                # Track topic preferences
                topics = self.extract_key_topics(content)
                for topic in topics:
                    patterns['topic_preferences'][topic] = patterns['topic_preferences'].get(topic, 0) + 1
                
                # Analyze response time if available
                metadata = interaction.get('metadata', {})
                response_time = metadata.get('execution_time_ms', 0)
                if response_time:
                    patterns['response_times'].append(response_time)
            
            # Calculate average response length
            if patterns['response_lengths']:
                avg_length = sum(patterns['response_lengths']) / len(patterns['response_lengths'])
                patterns['average_response_length'] = avg_length
            
            # Count common phrases
            phrase_counts = Counter(patterns['common_phrases'])
            patterns['top_phrases'] = phrase_counts.most_common(5)
            
            # Sort topic preferences
            sorted_topics = sorted(patterns['topic_preferences'].items(), key=lambda x: x[1], reverse=True)
            patterns['preferred_topics'] = sorted_topics[:10]
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to identify learning patterns: {e}")
            return {}
    
    def get_context_relevance_threshold(self) -> float:
        """Get the minimum relevance score for context inclusion"""
        return self.similarity_threshold
    
    def filter_relevant_context(
        self, 
        current_directive: str, 
        historical_conversations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter historical conversations by relevance to current directive"""
        try:
            relevant_context = []
            
            for conversation in historical_conversations:
                relevance_score = self.calculate_relevance_score(current_directive, conversation)
                
                if relevance_score >= self.similarity_threshold:
                    conversation['relevance_score'] = relevance_score
                    relevant_context.append(conversation)
            
            # Sort by relevance score (highest first)
            relevant_context.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            return relevant_context
            
        except Exception as e:
            logger.error(f"Failed to filter relevant context: {e}")
            return []