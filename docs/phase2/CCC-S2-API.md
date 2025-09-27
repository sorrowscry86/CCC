# CCC - Stage 2 API Specification

**Document ID**: CCC-S2-API  
**Version**: 1.0  
**Author**: Codey, The Executor  
**Reviewed by**: Beatrice, The Supervisor  
**Approved by**: Wykeve, Prime Architect  
**Date**: 2024  
**Dependencies**: CCC-S2-ARCHITECTURE.md

---

## API Overview

The Stage 2 API extends the CCC system with comprehensive memory and session management capabilities. All Stage 1 endpoints remain functional for backward compatibility, with new v2 endpoints providing enhanced memory-aware operations.

## Base Configuration

- **Base URL**: `http://127.0.0.1:5111`
- **API Version**: v2
- **Content-Type**: `application/json`
- **Authentication**: Session-based tokens
- **Rate Limiting**: 100 requests/minute per session

## Authentication

### Session Token Format
```json
{
  "session_token": "sess_1234567890abcdef",
  "expires_at": "2024-01-01T12:00:00Z",
  "permissions": ["read", "write", "memory"]
}
```

## API Endpoints

### 1. Session Management

#### Create Session
```http
POST /api/v2/sessions
Content-Type: application/json

{
  "user_preferences": {
    "memory_retention_days": 30,
    "context_depth": 10,
    "auto_summarize": true
  },
  "initial_context": "Optional context string"
}
```

**Response:**
```json
{
  "session_id": "sess_1234567890abcdef",
  "created_at": "2024-01-01T10:00:00Z",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "status": "active"
}
```

#### Get Session Details
```http
GET /api/v2/sessions/{session_id}
Authorization: Bearer {session_token}
```

**Response:**
```json
{
  "session_id": "sess_1234567890abcdef",
  "created_at": "2024-01-01T10:00:00Z",
  "last_active": "2024-01-01T12:30:00Z",
  "conversation_count": 5,
  "total_turns": 47,
  "user_preferences": {
    "memory_retention_days": 30,
    "context_depth": 10,
    "auto_summarize": true
  },
  "status": "active"
}
```

#### Update Session Preferences
```http
PUT /api/v2/sessions/{session_id}/preferences
Authorization: Bearer {session_token}
Content-Type: application/json

{
  "memory_retention_days": 60,
  "context_depth": 15,
  "auto_summarize": false
}
```

**Response:**
```json
{
  "session_id": "sess_1234567890abcdef",
  "updated_preferences": {
    "memory_retention_days": 60,
    "context_depth": 15,
    "auto_summarize": false
  },
  "updated_at": "2024-01-01T12:35:00Z"
}
```

#### Archive Session
```http
POST /api/v2/sessions/{session_id}/archive
Authorization: Bearer {session_token}
```

**Response:**
```json
{
  "session_id": "sess_1234567890abcdef",
  "status": "archived",
  "archived_at": "2024-01-01T12:40:00Z",
  "conversations_archived": 5
}
```

### 2. Conversation Management

#### Start New Conversation
```http
POST /api/v2/conversations
Authorization: Bearer {session_token}
Content-Type: application/json

{
  "session_id": "sess_1234567890abcdef",
  "directive": "Create a Python function to calculate Fibonacci numbers",
  "use_context": true,
  "context_depth": 5
}
```

**Response:**
```json
{
  "conversation_id": "conv_abcdef1234567890",
  "session_id": "sess_1234567890abcdef",
  "directive": "Create a Python function to calculate Fibonacci numbers",
  "created_at": "2024-01-01T12:45:00Z",
  "relevant_context": [
    {
      "conversation_id": "conv_previous123",
      "relevance_score": 0.85,
      "summary": "Previous discussion about recursive algorithms"
    }
  ]
}
```

#### Get Conversation History
```http
GET /api/v2/conversations/{conversation_id}
Authorization: Bearer {session_token}
```

**Response:**
```json
{
  "conversation_id": "conv_abcdef1234567890",
  "session_id": "sess_1234567890abcdef",
  "directive": "Create a Python function to calculate Fibonacci numbers",
  "created_at": "2024-01-01T12:45:00Z",
  "status": "completed",
  "turns": [
    {
      "turn_id": "turn_001",
      "turn_number": 1,
      "agent": "wykeve",
      "content": "Create a Python function to calculate Fibonacci numbers",
      "timestamp": "2024-01-01T12:45:00Z",
      "metadata": {
        "user_input": true
      }
    },
    {
      "turn_id": "turn_002", 
      "turn_number": 2,
      "agent": "beatrice",
      "content": "I'll analyze this directive for creating a Fibonacci function...",
      "timestamp": "2024-01-01T12:45:15Z",
      "metadata": {
        "model": "gpt-4",
        "temperature": 0.7,
        "response_time_ms": 1240
      }
    }
  ]
}
```

#### Add Conversation Turn
```http
POST /api/v2/conversations/{conversation_id}/turns
Authorization: Bearer {session_token}
Content-Type: application/json

{
  "agent": "beatrice",
  "content": "Based on the directive, I recommend...",
  "metadata": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

**Response:**
```json
{
  "turn_id": "turn_003",
  "conversation_id": "conv_abcdef1234567890",
  "turn_number": 3,
  "agent": "beatrice",
  "content": "Based on the directive, I recommend...",
  "timestamp": "2024-01-01T12:46:00Z",
  "stored": true
}
```

### 3. Context Management

#### Get Session Context
```http
GET /api/v2/sessions/{session_id}/context
Authorization: Bearer {session_token}
```

**Response:**
```json
{
  "session_id": "sess_1234567890abcdef",
  "context_summary": "This session has focused on Python programming, particularly algorithms and data structures. Recent conversations have covered recursive functions, optimization techniques, and code clarity.",
  "key_topics": [
    "python programming",
    "algorithms",
    "recursion",
    "optimization"
  ],
  "agent_states": {
    "beatrice": {
      "preferred_analysis_style": "analytical",
      "focus_areas": ["code_quality", "performance"],
      "learning_patterns": [
        "User prefers detailed explanations",
        "Emphasis on best practices"
      ]
    },
    "codey": {
      "preferred_implementation_style": "clean_code",
      "recent_technologies": ["python", "algorithms"],
      "successful_patterns": [
        "Step-by-step implementation",
        "Clear variable naming"
      ]
    }
  },
  "recent_conversations": [
    {
      "conversation_id": "conv_recent001",
      "directive": "Explain bubble sort algorithm",
      "relevance_score": 0.75,
      "created_at": "2024-01-01T11:30:00Z"
    }
  ]
}
```

#### Search Context
```http
POST /api/v2/sessions/{session_id}/context/search
Authorization: Bearer {session_token}
Content-Type: application/json

{
  "query": "python functions",
  "max_results": 5,
  "relevance_threshold": 0.6,
  "time_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-01T23:59:59Z"
  }
}
```

**Response:**
```json
{
  "query": "python functions",
  "results": [
    {
      "conversation_id": "conv_match001",
      "turn_id": "turn_005",
      "relevance_score": 0.92,
      "snippet": "Here's a Python function that demonstrates...",
      "context": "Discussion about function design patterns",
      "timestamp": "2024-01-01T10:15:00Z"
    }
  ],
  "total_matches": 3,
  "search_time_ms": 45
}
```

#### Update Context Summary
```http
PUT /api/v2/sessions/{session_id}/context/summary
Authorization: Bearer {session_token}
Content-Type: application/json

{
  "summary": "Updated context summary based on recent interactions",
  "key_topics": ["python", "algorithms", "web development"],
  "trigger": "manual_update"
}
```

**Response:**
```json
{
  "session_id": "sess_1234567890abcdef",
  "summary_updated": true,
  "updated_at": "2024-01-01T13:00:00Z",
  "previous_summary_archived": true
}
```

### 4. Enhanced Chat Completions

#### Memory-Enhanced Chat Completions
```http
POST /v2/chat/completions
Authorization: Bearer {session_token}
Content-Type: application/json

{
  "session_id": "sess_1234567890abcdef",
  "conversation_id": "conv_abcdef1234567890",
  "model": "gpt-4",
  "messages": [
    {
      "role": "user",
      "content": "Create a Python function to calculate Fibonacci numbers"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "memory_options": {
    "use_context": true,
    "context_depth": 5,
    "include_agent_state": true,
    "auto_store_response": true
  }
}
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1704110400,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Based on your previous interest in recursive algorithms and clean code practices, here's an optimized Fibonacci function...",
        "agent": "beatrice"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 200,
    "total_tokens": 350
  },
  "memory_metadata": {
    "context_used": true,
    "relevant_conversations": 2,
    "agent_state_applied": true,
    "turn_stored": true,
    "turn_id": "turn_new001"
  }
}
```

### 5. Agent State Management

#### Get Agent State
```http
GET /api/v2/sessions/{session_id}/agents/{agent_name}/state
Authorization: Bearer {session_token}
```

**Response:**
```json
{
  "session_id": "sess_1234567890abcdef",
  "agent": "beatrice",
  "state": {
    "personality_traits": {
      "analytical_depth": 0.8,
      "detail_orientation": 0.9,
      "supportive_tone": 0.7
    },
    "learned_patterns": [
      {
        "pattern": "User prefers step-by-step explanations",
        "confidence": 0.85,
        "learned_from": 12
      }
    ],
    "expertise_areas": [
      "code_analysis",
      "quality_assurance", 
      "strategic_planning"
    ],
    "interaction_history": {
      "total_interactions": 47,
      "successful_outcomes": 42,
      "preferred_response_length": "detailed"
    }
  },
  "last_updated": "2024-01-01T12:55:00Z"
}
```

#### Update Agent State
```http
PUT /api/v2/sessions/{session_id}/agents/{agent_name}/state
Authorization: Bearer {session_token}
Content-Type: application/json

{
  "state_updates": {
    "personality_traits": {
      "analytical_depth": 0.85
    },
    "new_learned_pattern": {
      "pattern": "User appreciates code comments",
      "confidence": 0.75
    }
  },
  "update_reason": "positive_feedback_received"
}
```

**Response:**
```json
{
  "session_id": "sess_1234567890abcdef",
  "agent": "beatrice",
  "state_updated": true,
  "updated_fields": ["personality_traits", "learned_patterns"],
  "updated_at": "2024-01-01T13:05:00Z"
}
```

### 6. Memory Analytics

#### Get Memory Statistics
```http
GET /api/v2/sessions/{session_id}/analytics
Authorization: Bearer {session_token}
```

**Response:**
```json
{
  "session_id": "sess_1234567890abcdef",
  "analytics": {
    "memory_usage": {
      "total_conversations": 15,
      "total_turns": 127,
      "storage_size_mb": 2.4,
      "oldest_conversation": "2024-01-01T08:00:00Z"
    },
    "interaction_patterns": {
      "average_conversation_length": 8.5,
      "most_active_agent": "beatrice",
      "preferred_topics": ["programming", "algorithms", "optimization"],
      "response_satisfaction": 0.89
    },
    "context_effectiveness": {
      "context_utilization_rate": 0.76,
      "relevance_accuracy": 0.82,
      "context_hit_rate": 0.71
    }
  }
}
```

### 7. Data Export and Management

#### Export Session Data
```http
POST /api/v2/sessions/{session_id}/export
Authorization: Bearer {session_token}
Content-Type: application/json

{
  "format": "json",
  "include_metadata": true,
  "include_agent_states": true,
  "time_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-01T23:59:59Z"
  }
}
```

**Response:**
```json
{
  "export_id": "export_xyz789",
  "session_id": "sess_1234567890abcdef",
  "format": "json",
  "status": "processing",
  "estimated_completion": "2024-01-01T13:15:00Z",
  "download_url": "/api/v2/exports/export_xyz789/download"
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "MEMORY_SERVICE_ERROR",
    "message": "Failed to retrieve session context",
    "details": {
      "session_id": "sess_1234567890abcdef",
      "operation": "get_context",
      "timestamp": "2024-01-01T13:20:00Z"
    },
    "retry_after": 30
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `SESSION_NOT_FOUND` | 404 | Session ID does not exist |
| `SESSION_EXPIRED` | 401 | Session token has expired |
| `CONVERSATION_NOT_FOUND` | 404 | Conversation ID does not exist |
| `MEMORY_SERVICE_ERROR` | 503 | Memory service temporarily unavailable |
| `CONTEXT_RETRIEVAL_FAILED` | 500 | Failed to retrieve context data |
| `INVALID_SESSION_TOKEN` | 401 | Session token is invalid or malformed |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests for this session |
| `STORAGE_QUOTA_EXCEEDED` | 413 | Session storage limit reached |

## Rate Limiting

### Limits by Endpoint Type
- **Session Management**: 10 requests/minute
- **Conversation Operations**: 30 requests/minute
- **Context Retrieval**: 50 requests/minute
- **Chat Completions**: 20 requests/minute
- **Analytics**: 5 requests/minute

### Rate Limit Headers
```http
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 47
X-RateLimit-Reset: 1704110460
X-RateLimit-Window: 60
```

## Backward Compatibility

### Stage 1 Endpoints
All Stage 1 endpoints remain fully functional:
- `GET /health` - Health check
- `POST /v1/chat/completions` - Basic chat completions

### Migration Strategy
- Stage 1 endpoints continue to work without modification
- New v2 endpoints provide enhanced functionality
- Clients can adopt memory features incrementally
- No breaking changes to existing implementations

## SDK Examples

### JavaScript SDK Usage
```javascript
// Initialize CCC Memory Client
const ccc = new CCCMemoryClient({
  baseUrl: 'http://127.0.0.1:5111',
  apiVersion: 'v2'
});

// Create session with memory
const session = await ccc.createSession({
  memory_retention_days: 30,
  context_depth: 10
});

// Start memory-enhanced conversation
const conversation = await ccc.startConversation({
  session_id: session.session_id,
  directive: "Create a Python function for Fibonacci numbers",
  use_context: true
});

// Execute covenant cycle with memory
const response = await ccc.enhancedChatCompletion({
  session_id: session.session_id,
  conversation_id: conversation.conversation_id,
  messages: [
    { role: "user", content: "Create a Python function for Fibonacci numbers" }
  ],
  memory_options: {
    use_context: true,
    include_agent_state: true
  }
});
```

### Python SDK Usage
```python
from ccc_memory_client import CCCMemoryClient

# Initialize client
client = CCCMemoryClient(
    base_url='http://127.0.0.1:5111',
    api_version='v2'
)

# Create session
session = await client.create_session(
    memory_retention_days=30,
    context_depth=10
)

# Enhanced covenant cycle
response = await client.enhanced_chat_completion(
    session_id=session['session_id'],
    messages=[
        {"role": "user", "content": "Create a Python function for Fibonacci numbers"}
    ],
    memory_options={
        "use_context": True,
        "include_agent_state": True
    }
)
```

---

## Conclusion

The Stage 2 API provides comprehensive memory and context management capabilities while maintaining full backward compatibility with Stage 1. The RESTful design ensures easy integration and scaling, while the memory features enable sophisticated, context-aware interactions that improve with each use.

---

*"A well-designed API is a conversation between human intention and machine capability."* - Wykeve, Prime Architect

**Document Status**: APPROVED  
**Implementation Status**: READY FOR DEVELOPMENT  
**Next Review**: Upon API Implementation Completion