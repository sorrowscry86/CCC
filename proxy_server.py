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
import threading
import time
import functools
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import configuration and crucible module
from config import config
import crucible

# Load environment variables from .env file
load_dotenv()

# Configure logging
log_level = logging.DEBUG if config.DEBUG else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# Validate configuration
try:
    config.validate()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Initialize Flask app
app = Flask(__name__)

# Configure CORS with environment-based settings
cors_config = config.get_cors_config()
if cors_config:
    CORS(app, **cors_config)
    if config.DEBUG:
        logger.info(f"[CONFIG] CORS enabled with origins: {cors_config.get('origins', '*')}")
else:
    logger.warning("[CONFIG] CORS disabled")

# Configuration aliases for backward compatibility
OPENAI_API_KEY = config.OPENAI_API_KEY
OPENAI_API_BASE = config.OPENAI_API_BASE
HOST = config.HOST
PORT = config.PORT

# Initialize memory service (global variables)
server_start_time = time.time()
memory_dal = None
memory_service = None
memory_initialized = False
memory_initializing = False


class AsyncioLoopManager:
    """Context manager for handling asyncio loop operations"""
    def __enter__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        return self.loop
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.loop.close()
        
    @staticmethod
    def run_async(coro_func, timeout=None):
        """Run an async function in a managed loop with optional timeout"""
        with AsyncioLoopManager() as loop:
            if timeout:
                try:
                    return loop.run_until_complete(asyncio.wait_for(coro_func, timeout=timeout))
                except asyncio.TimeoutError:
                    logger.error(f"Async operation timed out after {timeout} seconds")
                    raise
            else:
                return loop.run_until_complete(coro_func)


def api_error_handler(service_required=True, error_prefix="API error"):
    """Decorator for standardizing API error handling"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Check if memory service is required but not available
                if service_required and not memory_service:
                    return jsonify({'error': 'Memory service not available'}), 503
                
                return func(*args, **kwargs)
                
            except Exception as e:
                error_message = f"{error_prefix}: {e}"
                logger.error(error_message)
                return jsonify({'error': str(e)}), 500
        return wrapper
    return decorator


def call_openai_api(endpoint, data, timeout=None):
    """Make a request to the OpenAI API"""
    if timeout is None:
        timeout = config.OPENAI_API_TIMEOUT

    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }

    logger.info(f"Calling OpenAI API: {endpoint} with model {data.get('model', 'unknown')}")
    
    try:
        response = requests.post(
            f'{OPENAI_API_BASE}/{endpoint}',
            json=data,
            headers=headers,
            timeout=timeout
        )
        
        if response.status_code == 200:
            logger.info(f"OpenAI API call successful: {endpoint}")
            return response.json(), None
        else:
            error_msg = f"OpenAI API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return None, (response.json() if response.content else {'error': 'Unknown error'}, response.status_code)
            
    except requests.exceptions.Timeout:
        logger.error(f"OpenAI API timeout: {endpoint}")
        return None, ({'error': 'Request timeout'}, 408)
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenAI API request error: {e}")
        return None, ({'error': 'Request failed', 'details': str(e)}, 500)


def validate_json_request(f):
    """Decorator to validate JSON requests"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
                
            data = request.get_json()
            if data is None:
                return jsonify({'error': 'No JSON data provided'}), 400
                
        return f(*args, **kwargs)
    return decorated_function


async def initialize_memory_service():
    """Initialize memory service"""
    global memory_dal, memory_service, memory_initialized, memory_initializing
    
    if memory_initializing:
        logger.info("Memory service initialization already in progress...")
        return False
        
    memory_initializing = True
    
    try:
        from src.memory.database import MemoryDAL
        from src.services.memory_service import MemoryService
        
        db_path = os.getenv('CCC_DATABASE_PATH', 'ccc_memory.db')
        memory_dal = MemoryDAL(db_path)
        await memory_dal.initialize_database()
        memory_service = MemoryService(memory_dal)
        logger.info("Memory service initialized successfully")
        memory_initialized = True
        return True
    except Exception as e:
        logger.warning(f"Memory service initialization failed (Stage 1 fallback): {e}")
        memory_initialized = False
        return False
    finally:
        memory_initializing = False


def initialize_memory_service_background():
    """Initialize memory service in background thread"""
    global memory_dal, memory_service, memory_initialized, memory_initializing
    
    try:
        logger.info("[MEMORY] Starting memory service initialization in background...")
        
        # Add timeout for initialization
        try:
            # Use the AsyncioLoopManager for cleaner async handling
            init_timeout = float(config.MEMORY_INIT_TIMEOUT)
            result = AsyncioLoopManager.run_async(initialize_memory_service(), timeout=init_timeout)

            if memory_initialized:
                logger.info("[MEMORY] Memory service: ENABLED")
            else:
                logger.info("[MEMORY] Memory service: DISABLED")

        except asyncio.TimeoutError:
            logger.error(f"[MEMORY] Memory service initialization timed out after {config.MEMORY_INIT_TIMEOUT} seconds")
            memory_initializing = False
            memory_initialized = False
            
    except Exception as e:
        logger.error(f"Memory service initialization error: {e}")
        logger.info("[MEMORY] Memory service: DISABLED (error during initialization)")
        memory_initializing = False
        memory_initialized = False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    global memory_service, memory_initialized, memory_initializing
    
    status = "initializing" if memory_initializing else ("available" if memory_initialized else "unavailable")
    
    return jsonify({
        'status': 'healthy',
        'service': 'CCC OpenAI Proxy',
        'version': '2.0.0',
        'memory_service': status,
        'stage': '2' if memory_initialized else '1'
    })


# Stage 2 Memory Endpoints
@app.route('/api/v2/sessions', methods=['POST'])
@validate_json_request
@api_error_handler(service_required=True, error_prefix="Failed to create session")
def create_session():
    """Create new memory session"""
    data = request.get_json() or {}
    user_preferences = data.get('user_preferences', {})
    
    # Use AsyncioLoopManager for cleaner async handling
    session = AsyncioLoopManager.run_async(
        memory_service.initialize_session(user_preferences)
    )
    return jsonify(session.to_dict())


@app.route('/api/v2/sessions/<session_id>', methods=['GET'])
@api_error_handler(service_required=True, error_prefix="Failed to get session")
def get_session(session_id):
    """Get session information"""
    # Use AsyncioLoopManager for cleaner async handling
    session = AsyncioLoopManager.run_async(
        memory_service.get_session(session_id)
    )
    
    if session:
        return jsonify(session.to_dict())
    else:
        return jsonify({'error': 'Session not found'}), 404


@app.route('/api/v2/sessions/<session_id>/causal', methods=['GET'])
@api_error_handler(service_required=True, error_prefix="Failed to get causal context")
def get_causal_context(session_id):
    """Get causal narrative context for a session"""
    query = request.args.get('query', '')
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    # Use AsyncioLoopManager for cleaner async handling
    context = AsyncioLoopManager.run_async(
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


@app.route('/api/v2/sessions/<session_id>/context', methods=['GET'])
@api_error_handler(service_required=True, error_prefix="Failed to get session context")
def get_session_context(session_id):
    """Get relevant context for a session"""
    directive = request.args.get('directive', '')
    max_turns = int(request.args.get('max_turns', 10))
    
    # Use AsyncioLoopManager for cleaner async handling
    context = AsyncioLoopManager.run_async(
        memory_service.get_relevant_context(session_id, directive, max_turns)
    )
    return jsonify(context)


# Enhanced Chat Completions with Memory (v2 endpoint)
@app.route('/v2/chat/completions', methods=['POST'])
@validate_json_request
@api_error_handler(service_required=False, error_prefix="Enhanced chat completion error")
def enhanced_chat_completions():
    """
    Enhanced chat completions with memory support
    Backward compatible with v1 when memory options not provided
    """
    data = request.get_json()
    
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


def handle_memory_enhanced_completion(data, session_id, memory_options):
    """Handle memory-enhanced chat completion"""
    try:
        # Get current directive from messages
        messages = data.get('messages', [])
        if not messages:
            return jsonify({'error': 'No messages provided'}), 400
        
        current_directive = messages[-1].get('content', '') if messages else ''
        
        with AsyncioLoopManager() as loop:
            # Get relevant context if requested
            if memory_options.get('use_context', False):
                context = loop.run_until_complete(
                    memory_service.get_relevant_context(
                        session_id, 
                        current_directive,
                        memory_options.get('max_context_turns', 10)
                    )
                )
                
                # Debug logging for causal memory
                causal_narrative = context.get('causal_narrative', 'None retrieved')
                logger.info(f"CAUSAL DEBUG - Session {session_id[:8]}: Retrieved narrative length: {len(causal_narrative)} chars")
                logger.info(f"CAUSAL DEBUG - Narrative preview: {causal_narrative[:100]}...")
                
                # Add enhanced context to messages if available
                context_parts = []
                
                # Add traditional context summary
                if context.get('context_summary'):
                    context_parts.append(f"Previous conversation context: {context['context_summary']}")
                
                # CRITICAL REFACTOR: Construct the Structured Context Block
                domain = context.get('domain', 'Technical domain not available')
                narrative_summary = context.get('causal_narrative', 'No causal context available')
                
                # Construct structured context as mandated
                structured_context = f"""**PREVIOUS TECHNICAL CONTEXT**
- **Domain:** {domain}
- **Session History Summary:**
{narrative_summary}
---
"""
                
                # Add traditional context summary if available
                if context.get('context_summary'):
                    structured_context += f"\n**Traditional Context:** {context['context_summary']}\n"
                
                # Add agent learning insights
                agent_context = []
                for agent, state in context.get('agent_states', {}).items():
                    if state.get('preferred_topics'):
                        top_topics = sorted(state['preferred_topics'].items(), key=lambda x: x[1], reverse=True)[:3]
                        topics_str = ', '.join([topic for topic, _ in top_topics])
                        agent_context.append(f"{agent.title()} frequently discusses: {topics_str}")
                
                if agent_context:
                    structured_context += f"\n**Agent Insights:** " + "; ".join(agent_context) + "\n"
                
                # Inject the structured context block
                context_message = {
                    'role': 'system',
                    'content': f"[CCC SUPERVISOR MODE - CAUSAL MEMORY ACTIVE]\n\n{structured_context}\n\nUSE THIS TECHNICAL CONTEXT TO INFORM YOUR ANALYSIS. The domain context ensures you understand the technical framework, while the causal chain shows how previous events led to current circumstances. Apply this knowledge in your supervision."
                }
                data['messages'] = [context_message] + data['messages']
                logger.info(f"Injected structured domain context for session {session_id[:8]}... Domain: {domain[:30]}...")
            
            # Make OpenAI API call using the new centralized function
            result, error = call_openai_api('chat/completions', data)
            
            if error:
                return jsonify(error[0]), error[1]
                
            # Store response in memory if requested
            if memory_options.get('auto_store_response', False):
                try:
                    # Create conversation if new
                    conversation = loop.run_until_complete(
                        memory_service.create_conversation(session_id, current_directive)
                    )

                    if conversation:
                        # Store the AI response - FIXED: Use valid agent name
                        ai_content = result['choices'][0]['message']['content']
                        # Determine which agent is responding based on context
                        responding_agent = 'beatrice'  # Default to supervisor agent
                        if 'execute' in current_directive.lower() or 'implement' in current_directive.lower():
                            responding_agent = 'codey'

                        loop.run_until_complete(
                            memory_service.store_conversation_turn(
                                session_id,
                                conversation.conversation_id,
                                responding_agent,
                                ai_content,
                                {
                                    'model_used': data.get('model', 'unknown'),
                                    'temperature': data.get('temperature', 0.7),
                                    'execution_time_ms': 0,  # Can't access response.elapsed here
                                    'enhanced_with_causal_reasoning': True
                                }
                            )
                        )
                except Exception as e:
                    logger.warning(f"Failed to store response in memory: {e}")

            return jsonify(result)

    except Exception as e:
        logger.error(f"Memory-enhanced completion failed: {e}")
        # Add detailed causal memory status
        if hasattr(memory_service, 'causal_memory'):
            causal_available = memory_service.causal_memory._is_available()
            logger.error(f"Causal Memory Core available: {causal_available}")
        return jsonify({'error': f'Memory enhancement failed: {str(e)}'}), 500


def handle_regular_completion(data):
    """Handle regular chat completion (Stage 1 behavior)"""
    # Use the centralized OpenAI API call function
    result, error = call_openai_api('chat/completions', data)
    
    if error:
        return jsonify(error[0]), error[1]
        
    return jsonify(result)


@app.route('/v1/chat/completions', methods=['POST'])
@validate_json_request
@api_error_handler(service_required=False, error_prefix="Chat completion error")
def chat_completions():
    """
    Proxy endpoint for OpenAI chat completions
    Forwards requests to OpenAI API with proper authentication
    """
    data = request.get_json()
    
    # Use the centralized OpenAI API call function
    result, error = call_openai_api('chat/completions', data)
    
    if error:
        return jsonify(error[0]), error[1]
        
    return jsonify(result)


# Stage 3: Crucible Protocol - Code Verification Endpoint
@app.route('/verify/code', methods=['POST'])
@validate_json_request
@api_error_handler(service_required=False, error_prefix="Code verification error")
def verify_code():
    """
    Stage 3 Crucible Protocol - Automated Code Verification
    
    This endpoint implements the core of the Crucible Protocol, providing
    automated verification of code generated by the Executor agent.
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['session_id', 'code_to_test', 'test_code']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    session_id = data['session_id']
    code_to_test = data['code_to_test']
    test_code = data['test_code']
    timeout = data.get('timeout', 30)
    
    logger.info(f"[CRUCIBLE] Starting verification for session {session_id}")
    
    try:
        # Execute code verification in isolated crucible environment
        result = crucible.verify_code(code_to_test, test_code, timeout)
        
        # Prepare detailed response for the client
        response = {
            'session_id': session_id,
            'success': result['success'],
            'returncode': result['returncode'],
            'output': result['stdout'],
            'error_output': result['stderr'],
            'verification_status': 'PASSED' if result['success'] else 'FAILED',
            'timestamp': time.time()
        }
        
        # Log detailed results for debugging
        if result['success']:
            logger.info(f"[CRUCIBLE] ✅ Verification PASSED for session {session_id}")
        else:
            logger.warning(f"[CRUCIBLE] ❌ Verification FAILED for session {session_id}")
            logger.warning(f"[CRUCIBLE] Error output: {result['stderr']}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"[CRUCIBLE] Verification exception for session {session_id}: {e}")
        return jsonify({
            'session_id': session_id,
            'success': False,
            'error': str(e),
            'verification_status': 'ERROR',
            'timestamp': time.time()
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


@app.route("/api/v2/status", methods=["GET"])
def memory_service_status():
    """Get detailed memory service status"""
    global memory_service, memory_initialized, memory_initializing
    
    status = {
        'memory_service': {
            'status': "initializing" if memory_initializing else ("available" if memory_initialized else "unavailable"),       
            'initialization_complete': memory_initialized,
            'initialization_in_progress': memory_initializing
        },
        'server': {
            'version': '2.0.0',
            'stage': '2' if memory_initialized else '1',
            'uptime_seconds': int(time.time() - server_start_time)
        }
    }
    
    # Add detailed memory service info if available
    if memory_service:
        try:
            # Get database stats if available
            db_stats = {}
            if memory_dal:
                try:
                    # Use AsyncioLoopManager for cleaner async handling
                    stats = AsyncioLoopManager.run_async(memory_dal.get_stats())
                    db_stats = {
                        'sessions_count': stats.get('sessions_count', 0),
                        'conversations_count': stats.get('conversations_count', 0),
                        'turns_count': stats.get('turns_count', 0)
                    }
                except Exception as e:
                    db_stats = {'error': str(e)}
    
            # Check causal memory status
            causal_status = "unavailable"
            if hasattr(memory_service, 'causal_memory'):
                causal_status = "available" if memory_service.causal_memory._is_available() else "unavailable"
    
            status['memory_service'].update({
                'database': db_stats,
                'causal_memory': causal_status
            })
        except Exception as e:
            status['memory_service']['error'] = str(e)
    
    return jsonify(status)


if __name__ == '__main__':
    # Start the server first, then initialize memory in background
    logger.info("[START] Covenant API Proxy is starting...")
    logger.info(f"[SERVER] Server running on http://{HOST}:{PORT}")
    logger.info("[NOTE] Make sure OPENAI_API_KEY is set in your environment variables")
    
    import signal
    import atexit
    
    def cleanup_resources():
        """Clean up resources before shutdown"""
        logger.info("[SERVER] Shutting down server...")
        if memory_dal and hasattr(memory_dal, 'close'):
            logger.info("[MEMORY] Closing database connections...")
            try:
                # Use AsyncioLoopManager for cleaner async handling
                AsyncioLoopManager.run_async(memory_dal.close())
                logger.info("[MEMORY] Database connections closed successfully")
            except Exception as e:
                logger.error(f"Error closing database connections: {e}")
    
    # Register the cleanup function to be called on exit
    atexit.register(cleanup_resources)
    
    # Handle SIGINT (Ctrl+C) and SIGTERM
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        cleanup_resources()
        sys.exit(0)
    
    # Register signal handlers if on Unix-like system
    if hasattr(signal, 'SIGINT'):
        signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    # Start memory service initialization in a background thread
    memory_thread = threading.Thread(target=initialize_memory_service_background)
    memory_thread.daemon = True
    memory_thread.start()
    
    try:
        logger.info(f"[SERVER] Debug mode: {config.DEBUG}")
        app.run(
            host=HOST,
            port=PORT,
            debug=config.DEBUG,
            use_reloader=False,
            threaded=True  # Enable threading for the Flask app
        )
    except Exception as e:
        logger.error(f"Failed to start Flask server: {e}")
        logger.error("This could be due to:")
        logger.error(f"- Port {PORT} already in use")
        logger.error("- Firewall blocking the connection")
        logger.error("- Insufficient permissions")
        sys.exit(1)

