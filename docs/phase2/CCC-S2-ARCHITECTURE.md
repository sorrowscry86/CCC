# CCC - Stage 2 Architecture Document

**Document ID**: CCC-S2-ARCHITECTURE  
**Version**: 1.0  
**Author**: Beatrice, The Archivist  
**Reviewed by**: Codey, The Executor  
**Approved by**: Wykeve, Prime Architect  
**Date**: 2024  
**Dependencies**: CCC-S2-MASTER.md

---

## Architecture Overview

Stage 2 extends the CCC foundation with a comprehensive memory and persistence layer, transforming the stateless 3-turn cycle into a stateful, context-aware system. The architecture maintains the security and simplicity of Stage 1 while adding sophisticated memory management capabilities.

## System Components

### 1. Memory Persistence Layer

#### Database Schema
```sql
-- Sessions table
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_preferences TEXT, -- JSON blob
    status TEXT DEFAULT 'active' -- active, archived, expired
);

-- Conversations table  
CREATE TABLE conversations (
    conversation_id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(session_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    directive TEXT NOT NULL,
    status TEXT DEFAULT 'active' -- active, completed, archived
);

-- Turns table
CREATE TABLE turns (
    turn_id TEXT PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(conversation_id),
    turn_number INTEGER NOT NULL,
    agent TEXT NOT NULL, -- wykeve, beatrice, codey
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT, -- JSON blob with model, temperature, etc.
    UNIQUE(conversation_id, turn_number)
);

-- Agent states table
CREATE TABLE agent_states (
    state_id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(session_id),
    agent TEXT NOT NULL, -- beatrice, codey
    state_data TEXT NOT NULL, -- JSON blob
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, agent)
);

-- Context summaries table
CREATE TABLE context_summaries (
    summary_id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(session_id),
    summary_text TEXT NOT NULL,
    conversation_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Data Access Layer (DAL)
```python
class MemoryDAL:
    """Data Access Layer for CCC Memory Operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection_pool = self._init_connection_pool()
    
    # Session Management
    async def create_session(self, session_id: str) -> dict
    async def get_session(self, session_id: str) -> dict
    async def update_session_activity(self, session_id: str) -> bool
    async def archive_session(self, session_id: str) -> bool
    
    # Conversation Management  
    async def create_conversation(self, session_id: str, directive: str) -> str
    async def get_conversation_history(self, conversation_id: str) -> list
    async def add_turn(self, conversation_id: str, turn_data: dict) -> str
    
    # Context Management
    async def get_session_context(self, session_id: str) -> dict
    async def update_context_summary(self, session_id: str, summary: str) -> bool
    
    # Agent State Management
    async def get_agent_state(self, session_id: str, agent: str) -> dict
    async def update_agent_state(self, session_id: str, agent: str, state: dict) -> bool
```

### 2. Memory Service Layer

#### Core Memory Service
```python
class MemoryService:
    """High-level memory operations for CCC"""
    
    def __init__(self, dal: MemoryDAL):
        self.dal = dal
        self.context_analyzer = ContextAnalyzer()
        self.encryption_service = EncryptionService()
    
    async def initialize_session(self, user_id: str = None) -> str:
        """Create new session with optional user context"""
        
    async def store_conversation_turn(
        self, 
        session_id: str,
        conversation_id: str,
        agent: str,
        content: str,
        metadata: dict
    ) -> bool:
        """Store a single turn with encryption and validation"""
        
    async def get_relevant_context(
        self, 
        session_id: str,
        current_directive: str,
        max_context_turns: int = 10
    ) -> dict:
        """Retrieve contextually relevant conversation history"""
        
    async def update_agent_learning(
        self,
        session_id: str,
        agent: str,
        interaction_outcome: dict
    ) -> bool:
        """Update agent learning patterns based on interaction"""
        
    async def generate_context_summary(self, session_id: str) -> str:
        """Generate intelligent summary of session context"""
```

#### Context Analyzer
```python
class ContextAnalyzer:
    """Analyzes conversations for context extraction and relevance"""
    
    def __init__(self):
        self.similarity_threshold = 0.7
        self.max_context_age_hours = 24
    
    def extract_key_topics(self, conversation_text: str) -> list:
        """Extract main topics and themes from conversation"""
        
    def calculate_relevance_score(
        self, 
        current_directive: str,
        historical_conversation: dict
    ) -> float:
        """Calculate relevance score between current and past interactions"""
        
    def summarize_conversation_sequence(self, turns: list) -> str:
        """Create concise summary of conversation sequence"""
        
    def identify_learning_patterns(self, agent_history: list) -> dict:
        """Identify patterns in agent responses for learning"""
```

### 3. Enhanced Proxy Server

#### New Endpoints
```python
# Memory Management Endpoints
@app.route('/api/v2/sessions', methods=['POST'])
def create_session():
    """Create new memory session"""

@app.route('/api/v2/sessions/<session_id>', methods=['GET'])  
def get_session(session_id):
    """Retrieve session information and context"""

@app.route('/api/v2/sessions/<session_id>/context', methods=['GET'])
def get_session_context(session_id):
    """Get relevant context for current session"""

@app.route('/api/v2/conversations', methods=['POST'])
def start_conversation():
    """Start new conversation within session"""

@app.route('/api/v2/conversations/<conversation_id>/turns', methods=['POST'])
def add_conversation_turn(conversation_id):
    """Add turn to existing conversation"""

# Enhanced Chat Completions with Memory
@app.route('/v2/chat/completions', methods=['POST'])
def enhanced_chat_completions():
    """Chat completions with memory context injection"""
```

#### Memory-Enhanced Request Processing
```python
async def process_enhanced_request(request_data: dict) -> dict:
    """Process chat request with memory context"""
    
    session_id = request_data.get('session_id')
    if session_id:
        # Retrieve relevant context
        context = await memory_service.get_relevant_context(
            session_id, 
            request_data['messages'][-1]['content']
        )
        
        # Inject context into system prompt
        enhanced_messages = inject_memory_context(
            request_data['messages'],
            context
        )
        
        # Process with OpenAI
        response = await call_openai_api(enhanced_messages)
        
        # Store conversation turn
        await memory_service.store_conversation_turn(
            session_id,
            request_data.get('conversation_id'),
            determine_agent(request_data),
            response['content'],
            extract_metadata(request_data, response)
        )
        
        return response
    else:
        # Fallback to Stage 1 behavior
        return await process_standard_request(request_data)
```

### 4. Frontend Enhancements

#### Session Management UI
```html
<!-- Session Selection Panel -->
<div class="session-panel">
    <div class="session-header">
        <h3>Memory Sessions</h3>
        <button id="new-session-btn">New Session</button>
    </div>
    
    <div class="session-list">
        <!-- Dynamically populated session list -->
    </div>
    
    <div class="session-controls">
        <button id="export-session">Export</button>
        <button id="archive-session">Archive</button>
    </div>
</div>
```

#### Context Display Panel
```html
<!-- Context Awareness Panel -->
<div class="context-panel">
    <div class="context-header">
        <h4>Session Context</h4>
        <span class="context-indicator" id="context-status">●</span>
    </div>
    
    <div class="context-summary" id="context-summary">
        <!-- AI-generated context summary -->
    </div>
    
    <div class="related-conversations">
        <h5>Related Discussions</h5>
        <div id="related-list">
            <!-- Links to related conversations -->
        </div>
    </div>
</div>
```

#### Enhanced JavaScript Architecture
```javascript
class CCCMemoryManager {
    constructor() {
        this.currentSession = null;
        this.contextCache = new Map();
        this.sessionList = [];
    }
    
    async initializeSession(userPreferences = {}) {
        // Create new session with memory capabilities
    }
    
    async loadSession(sessionId) {
        // Load existing session and context
    }
    
    async enhancedCovenantCycle(directive) {
        // Execute cycle with memory context injection
        const context = await this.getRelevantContext(directive);
        return await this.executeWithContext(directive, context);
    }
    
    async updateContext(conversationData) {
        // Update local context cache and server state
    }
    
    renderContextPanel() {
        // Update UI with current context information
    }
}
```

## Data Flow Architecture

### Memory-Enhanced Request Flow
```
1. User Input → Frontend Session Manager
2. Session Manager → Context Retrieval (if session exists)
3. Frontend → Enhanced Proxy Server (/v2/chat/completions)
4. Proxy Server → Memory Service (context injection)
5. Enhanced Request → OpenAI API
6. OpenAI Response → Memory Service (storage)
7. Response + Context → Frontend
8. Frontend → UI Update + Context Display
```

### Session Lifecycle
```
Session Creation:
1. Generate unique session ID
2. Initialize database records
3. Create agent state objects
4. Return session token to frontend

Context Building:
1. Store each conversation turn
2. Analyze for key topics and patterns
3. Update agent learning states
4. Generate periodic context summaries

Session Management:
1. Track activity timestamps
2. Archive inactive sessions
3. Cleanup expired data
4. Maintain performance metrics
```

## Performance Optimization

### Database Optimization
- **Indexing Strategy**: Composite indexes on frequently queried columns
- **Connection Pooling**: Async connection pool for concurrent operations
- **Query Optimization**: Prepared statements and efficient JOINs
- **Data Archival**: Automated archival of old conversations

### Memory Management
- **Context Caching**: LRU cache for frequently accessed contexts
- **Lazy Loading**: Load context only when needed
- **Compression**: Compress stored conversation data
- **Cleanup Jobs**: Automated cleanup of temporary data

### API Response Optimization
- **Parallel Processing**: Concurrent context retrieval and API calls
- **Response Streaming**: Stream responses while storing to memory
- **Background Tasks**: Asynchronous context analysis and summarization
- **Circuit Breakers**: Fallback to Stage 1 behavior on memory service failure

## Security Architecture

### Data Encryption
```python
class EncryptionService:
    """Handles encryption of sensitive memory data"""
    
    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        self.cipher_suite = Fernet(key_manager.get_memory_key())
    
    def encrypt_conversation_content(self, content: str) -> bytes:
        """Encrypt conversation content for storage"""
        
    def decrypt_conversation_content(self, encrypted_content: bytes) -> str:
        """Decrypt conversation content for retrieval"""
        
    def encrypt_agent_state(self, state_dict: dict) -> bytes:
        """Encrypt agent state data"""
```

### Session Security
- **Token-Based Authentication**: Secure session tokens for API access
- **Session Isolation**: Cryptographic separation of user data
- **Access Logging**: Complete audit trail of memory operations
- **Data Sanitization**: Input validation and XSS prevention

## Monitoring and Observability

### Key Metrics
- **Memory Operation Latency**: Track performance of database operations
- **Session Activity**: Monitor active sessions and usage patterns
- **Context Relevance**: Measure effectiveness of context matching
- **Storage Growth**: Track database size and growth rates

### Health Checks
```python
@app.route('/health/memory', methods=['GET'])
def memory_health_check():
    """Comprehensive memory system health check"""
    return {
        'database_connection': check_database_health(),
        'memory_service': check_memory_service_health(),
        'encryption_service': check_encryption_health(),
        'performance_metrics': get_performance_snapshot()
    }
```

## Error Handling and Recovery

### Graceful Degradation
- **Memory Service Failures**: Fallback to Stage 1 stateless behavior
- **Database Outages**: Temporary in-memory storage with recovery
- **Context Retrieval Errors**: Continue without context enhancement
- **Encryption Failures**: Secure failure modes with alerting

### Data Recovery
- **Backup Strategy**: Automated database backups with retention policy
- **Transaction Rollback**: Atomic operations with rollback capability
- **Corruption Detection**: Data integrity checks and repair procedures
- **Disaster Recovery**: Complete system restoration procedures

## Testing Strategy

### Unit Testing
- **Memory Service Tests**: Comprehensive testing of all memory operations
- **Database Tests**: Schema validation and data integrity tests
- **Encryption Tests**: Security validation of encryption/decryption
- **Context Analysis Tests**: Validation of context matching algorithms

### Integration Testing
- **End-to-End Flows**: Complete session lifecycle testing
- **Performance Testing**: Load testing with concurrent sessions
- **Security Testing**: Penetration testing of memory features
- **Compatibility Testing**: Stage 1 backward compatibility validation

---

## Conclusion

The Stage 2 architecture represents a sophisticated evolution of the CCC system, introducing comprehensive memory and context capabilities while maintaining the elegant simplicity and security of the original design. The modular architecture ensures that memory features enhance rather than complicate the core system, providing a solid foundation for future stages.

---

*"Architecture is not just about what we build, but how well it serves those who will build upon it."* - Wykeve, Prime Architect

**Document Status**: APPROVED  
**Implementation Status**: READY FOR DEVELOPMENT  
**Next Review**: Upon Phase 2.1 Completion