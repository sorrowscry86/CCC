#!/usr/bin/env python3
"""
Enhanced OpenAI API Proxy Server for CCC (Covenant Command Cycle) - Stage 2

This Flask server acts as a secure proxy to the OpenAI API with memory capabilities,
protecting the API key and providing controlled access to AI capabilities with
persistent context retention.
"""

import os
import sys
import json
import logging
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_BASE = 'https://api.openai.com/v1'
HOST = '127.0.0.1'
PORT = 5111

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is not set!")
    raise ValueError("OPENAI_API_KEY is required but not found in environment variables")

# Initialize memory service (global variables)
memory_dal = None
memory_service = None

async def initialize_memory_service():
    """Initialize memory service"""
    global memory_dal, memory_service
    
    try:
        from src.memory.database import MemoryDAL
        from src.services.memory_service import MemoryService
        
        db_path = os.getenv('CCC_DATABASE_PATH', 'ccc_memory.db')
        memory_dal = MemoryDAL(db_path)
        await memory_dal.initialize_database()
        memory_service = MemoryService(memory_dal)
        logger.info("Memory service initialized successfully")
        return True
    except Exception as e:
        logger.warning(f"Memory service initialization failed (Stage 1 fallback): {e}")
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    memory_status = 'available' if memory_service else 'unavailable'
    return jsonify({
        'status': 'healthy',
        'service': 'CCC OpenAI Proxy',
        'version': '2.0.0',
        'memory_service': memory_status,
        'stage': '2' if memory_service else '1'
    })


# Stage 2 Memory Endpoints
@app.route('/api/v2/sessions', methods=['POST'])
def create_session():
    """Create new memory session"""
    try:
        if not memory_service:
            return jsonify({'error': 'Memory service not available'}), 503
        
        data = request.get_json() or {}
        user_preferences = data.get('user_preferences', {})
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            session = loop.run_until_complete(
                memory_service.initialize_session(user_preferences)
            )
            return jsonify(session.to_dict())
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session information"""
    try:
        if not memory_service:
            return jsonify({'error': 'Memory service not available'}), 503
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            session = loop.run_until_complete(
                memory_service.get_session(session_id)
            )
            if session:
                return jsonify(session.to_dict())
            else:
                return jsonify({'error': 'Session not found'}), 404
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/sessions/<session_id>/causal', methods=['GET'])
def get_causal_context(session_id):
    """Get causal narrative context for a session"""
    try:
        if not memory_service:
            return jsonify({'error': 'Memory service not available'}), 503
        
        query = request.args.get('query', '')
        if not query:
            return jsonify({'error': 'Query parameter required'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Get causal context from enhanced memory service
            context = loop.run_until_complete(
                memory_service.get_relevant_context(session_id, query, 10)
            )
            
            # Return focused causal information
            return jsonify({
                'session_id': session_id,
                'query': query,
                'causal_narrative': context.get('causal_narrative', 'No causal context available'),
                'traditional_summary': context.get('context_summary', ''),
                'total_conversations': context.get('total_conversations', 0),
                'agent_insights': {
                    agent: {
                        'interaction_count': state.get('interaction_count', 0),
                        'preferred_topics': list(state.get('preferred_topics', {}).keys())[:5]
                    }
                    for agent, state in context.get('agent_states', {}).items()
                }
            })
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Failed to get causal context: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/sessions/<session_id>/context', methods=['GET'])
def get_session_context(session_id):
    """Get relevant context for a session"""
    try:
        if not memory_service:
            return jsonify({'error': 'Memory service not available'}), 503
        
        directive = request.args.get('directive', '')
        max_turns = int(request.args.get('max_turns', 10))
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            context = loop.run_until_complete(
                memory_service.get_relevant_context(session_id, directive, max_turns)
            )
            return jsonify(context)
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Failed to get session context: {e}")
        return jsonify({'error': str(e)}), 500


# Enhanced Chat Completions with Memory (v2 endpoint)
@app.route('/v2/chat/completions', methods=['POST'])
def enhanced_chat_completions():
    """
    Enhanced chat completions with memory support
    Backward compatible with v1 when memory options not provided
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Extract memory options
        memory_options = data.pop('memory_options', {})
        session_id = data.pop('session_id', None)
        
        # If memory is requested but not available, fall back to regular completion
        if memory_options and not memory_service:
            logger.warning("Memory requested but service unavailable, falling back to Stage 1")
            memory_options = {}
            session_id = None
        
        # Handle memory-enhanced request
        if memory_options and session_id and memory_service:
            return handle_memory_enhanced_completion(data, session_id, memory_options)
        else:
            # Fall back to regular completion (Stage 1 behavior)
            return handle_regular_completion(data)
            
    except Exception as e:
        logger.error(f"Enhanced chat completion error: {e}")
        return jsonify({'error': str(e)}), 500


def handle_memory_enhanced_completion(data, session_id, memory_options):
    """Handle memory-enhanced chat completion"""
    try:
        # Get current directive from messages
        messages = data.get('messages', [])
        if not messages:
            return jsonify({'error': 'No messages provided'}), 400
        
        current_directive = messages[-1].get('content', '') if messages else ''
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Get relevant context if requested
            if memory_options.get('use_context', False):
                context = loop.run_until_complete(
                    memory_service.get_relevant_context(
                        session_id, 
                        current_directive,
                        memory_options.get('max_context_turns', 10)
                    )
                )
                
                # Add enhanced context to messages if available
                context_parts = []
                
                # Add traditional context summary
                if context.get('context_summary'):
                    context_parts.append(f"Previous conversation context: {context['context_summary']}")
                
                # Add causal narrative for enhanced reasoning
                if context.get('causal_narrative') and context['causal_narrative'] not in ['Causal reasoning not available', 'No relevant causal context found in memory.']:
                    context_parts.append(f"Causal narrative: {context['causal_narrative']}")
                
                # Add agent learning context
                agent_context = []
                for agent, state in context.get('agent_states', {}).items():
                    if state.get('preferred_topics'):
                        top_topics = sorted(state['preferred_topics'].items(), key=lambda x: x[1], reverse=True)[:3]
                        topics_str = ', '.join([topic for topic, _ in top_topics])
                        agent_context.append(f"{agent.title()} frequently discusses: {topics_str}")
                
                if agent_context:
                    context_parts.append("Agent learning insights: " + "; ".join(agent_context))
                
                # Add context to messages if available
                if context_parts:
                    enhanced_context = "\n\n".join(context_parts)
                    context_message = {
                        'role': 'system',
                        'content': f"Enhanced Context with Causal Reasoning:\n{enhanced_context}\n\nUse this context to inform your response while maintaining your role and expertise."
                    }
                    data['messages'] = [context_message] + data['messages']
                    logger.info(f"Added enhanced context with causal reasoning for session {session_id[:8]}...")
            
            # Make OpenAI API call
            headers = {
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Memory-enhanced chat completion for session {session_id[:8]}...")
            
            response = requests.post(
                f'{OPENAI_API_BASE}/chat/completions',
                json=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Store response in memory if requested
                if memory_options.get('auto_store_response', False):
                    try:
                        # Create conversation if new
                        conversation = loop.run_until_complete(
                            memory_service.create_conversation(session_id, current_directive)
                        )
                        
                        if conversation:
                            # Store the AI response
                            ai_content = result['choices'][0]['message']['content']
                            loop.run_until_complete(
                                memory_service.store_conversation_turn(
                                    session_id,
                                    conversation.conversation_id,
                                    'ai_response',
                                    ai_content,
                                    {
                                        'model_used': data.get('model', 'unknown'),
                                        'temperature': data.get('temperature', 0.7),
                                        'execution_time_ms': response.elapsed.total_seconds() * 1000,
                                        'enhanced_with_causal_reasoning': True
                                    }
                                )
                            )
                    except Exception as e:
                        logger.warning(f"Failed to store response in memory: {e}")
                
                return jsonify(result)
            else:
                error_data = response.json() if response.content else {'error': 'Unknown error'}
                return jsonify(error_data), response.status_code
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Memory-enhanced completion failed: {e}")
        return jsonify({'error': str(e)}), 500


def handle_regular_completion(data):
    """Handle regular chat completion (Stage 1 behavior)"""
    try:
        # Prepare headers for OpenAI API
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Log the request (without sensitive data)
        logger.info(f"Regular chat completion request with model: {data.get('model', 'unknown')}")
        
        # Forward request to OpenAI
        response = requests.post(
            f'{OPENAI_API_BASE}/chat/completions',
            json=data,
            headers=headers,
            timeout=30
        )
        
        # Return the response
        if response.status_code == 200:
            logger.info("Successfully proxied request to OpenAI")
            return jsonify(response.json())
        else:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            return jsonify({
                'error': 'OpenAI API error',
                'status_code': response.status_code,
                'message': response.text
            }), response.status_code
            
    except requests.exceptions.Timeout:
        logger.error("Request to OpenAI API timed out")
        return jsonify({'error': 'Request timeout'}), 408
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return jsonify({'error': 'Request failed', 'details': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """
    Proxy endpoint for OpenAI chat completions
    Forwards requests to OpenAI API with proper authentication
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Prepare headers for OpenAI API
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Log the request (without sensitive data)
        logger.info(f"Proxying chat completion request with model: {data.get('model', 'unknown')}")
        
        # Forward request to OpenAI
        response = requests.post(
            f'{OPENAI_API_BASE}/chat/completions',
            json=data,
            headers=headers,
            timeout=30
        )
        
        # Return the response
        if response.status_code == 200:
            logger.info("Successfully proxied request to OpenAI")
            return jsonify(response.json())
        else:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            return jsonify({
                'error': 'OpenAI API error',
                'status_code': response.status_code,
                'message': response.text
            }), response.status_code
            
    except requests.exceptions.Timeout:
        logger.error("Request to OpenAI API timed out")
        return jsonify({'error': 'Request timeout'}), 408
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return jsonify({'error': 'Request failed', 'details': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Initialize memory service on startup
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        memory_available = loop.run_until_complete(initialize_memory_service())
        loop.close()
        
        if memory_available:
            logger.info("🚀 Covenant API Proxy with Memory (Stage 2) is starting...")
            logger.info(f"🧠 Memory service: ENABLED")
        else:
            logger.info("🚀 Covenant API Proxy (Stage 1 Fallback) is starting...")
            logger.info("🧠 Memory service: DISABLED")
            
    except Exception as e:
        logger.error(f"Startup error: {e}")
        logger.info("🚀 Covenant API Proxy (Stage 1 Fallback) is starting...")
        
    logger.info(f"🌐 Server running on http://{HOST}:{PORT}")
    logger.info("📝 Make sure OPENAI_API_KEY is set in your environment variables")
    app.run(host=HOST, port=PORT, debug=False)