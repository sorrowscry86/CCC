#!/usr/bin/env python3
"""
CCC Phase 2 Usage Example
Demonstrates how to use the memory-enhanced features programmatically
"""

import asyncio
import sys
import os

# Add CCC source to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory.database import MemoryDAL
from src.services.memory_service import MemoryService

async def demo_phase2_features():
    """Demonstrate Phase 2 memory features"""
    print("🚀 CCC Phase 2 Memory Features Demo")
    print("=" * 50)
    
    # Initialize memory components
    print("1. Initializing memory system...")
    dal = MemoryDAL('demo_memory.db')
    await dal.initialize_database()
    memory_service = MemoryService(dal)
    print("   ✅ Memory system ready")
    
    # Create a session
    print("\n2. Creating memory session...")
    session = await memory_service.initialize_session({
        'user_name': 'Demo User',
        'preferences': {'context_depth': 10, 'auto_summarize': True}
    })
    print(f"   ✅ Session created: {session.session_id}")
    
    # Create and store a conversation
    print("\n3. Creating conversation...")
    conversation = await memory_service.create_conversation(
        session.session_id,
        "Create a Python function that validates email addresses"
    )
    print(f"   ✅ Conversation created: {conversation.conversation_id}")
    
    # Store conversation turns
    print("\n4. Storing conversation turns...")
    
    # Beatrice's analysis
    await memory_service.store_conversation_turn(
        session.session_id,
        conversation.conversation_id,
        'beatrice',
        'I need to analyze email validation requirements. This involves regex patterns, domain validation, and error handling.',
        {'model': 'gpt-4', 'temperature': 0.7, 'execution_time_ms': 1200}
    )
    print("   ✅ Stored Beatrice's analysis")
    
    # Codey's implementation
    await memory_service.store_conversation_turn(
        session.session_id,
        conversation.conversation_id,
        'codey',
        '''Here's the email validation function:

import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
''',
        {'model': 'gpt-4', 'temperature': 0.7, 'execution_time_ms': 2100}
    )
    print("   ✅ Stored Codey's implementation")
    
    # Beatrice's review
    await memory_service.store_conversation_turn(
        session.session_id,
        conversation.conversation_id,
        'beatrice',
        'The implementation looks good. The regex pattern covers standard email formats. Consider adding more detailed error messages for production use.',
        {'model': 'gpt-4', 'temperature': 0.7, 'execution_time_ms': 900}
    )
    print("   ✅ Stored Beatrice's review")
    
    # Demonstrate context retrieval
    print("\n5. Retrieving relevant context...")
    context = await memory_service.get_relevant_context(
        session.session_id,
        "Create a function to validate phone numbers",
        max_context_turns=5
    )
    
    print(f"   📊 Found {len(context['relevant_conversations'])} relevant conversations")
    print(f"   🧠 Agent states tracked: {list(context['agent_states'].keys())}")
    print(f"   📝 Context summary: {context['context_summary'][:100]}...")
    
    # Show agent learning
    print("\n6. Checking agent learning patterns...")
    beatrice_state = await dal.get_agent_state(session.session_id, 'beatrice')
    codey_state = await dal.get_agent_state(session.session_id, 'codey')
    
    if beatrice_state:
        print(f"   🎯 Beatrice interactions: {beatrice_state.state_data.get('interaction_count', 0)}")
        print(f"   📏 Avg response length: {beatrice_state.state_data.get('average_response_length', 0):.1f} words")
    
    if codey_state:
        print(f"   🎯 Codey interactions: {codey_state.state_data.get('interaction_count', 0)}")
        print(f"   📏 Avg response length: {codey_state.state_data.get('average_response_length', 0):.1f} words")
    
    print("\n" + "=" * 50)
    print("🎉 Phase 2 Memory Features Demo Complete!")
    print("\n📋 Demonstrated Features:")
    print("   • Session creation and management")
    print("   • Conversation and turn storage")
    print("   • Context analysis and retrieval")
    print("   • Agent learning and state tracking")
    print("   • Memory persistence across sessions")

if __name__ == '__main__':
    asyncio.run(demo_phase2_features())