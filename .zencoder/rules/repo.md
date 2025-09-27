---
description: Repository Information Overview
alwaysApply: true
---

# Covenant Command Cycle (CCC) Information

## Summary
CCC is a multi-agent AI system with persistent state memory, implementing supervised agentic workflows between Beatrice (Supervisor) and Codey (Executor) through a memory-enabled Flask proxy server. The project focuses on context retention, session management, and agent learning to create a stateful multi-agent system.

## Structure
- **src/**: Core source code with memory, models, services, and utilities
- **database/**: Database schema definitions
- **docs/**: Documentation for Phase 2 implementation
- **examples/**: Example usage scripts
- **.github/**: GitHub-specific configuration files
- **proxy_server.py**: Main entry point for the Flask proxy server
- **resonant_loop_lab.html**: Web interface for the CCC system

## Language & Runtime
**Language**: Python
**Version**: 3.9+
**Build System**: Standard Python package
**Package Manager**: pip

## Dependencies
**Main Dependencies**:
- Flask (2.3.3): Web framework for the proxy server
- Flask-CORS (4.0.0): Cross-origin resource sharing support
- requests (2.31.0): HTTP client for API calls
- python-dotenv (1.0.0): Environment variable management
- aiosqlite (0.17.0+): Async SQLite database operations
- cryptography (3.4.8+): Data encryption capabilities
- openai (1.0.0+): OpenAI API client
- sentence-transformers (2.2.0+): Text embedding generation
- duckdb (0.9.0+): Analytical database for causal memory

## Build & Installation
```bash
# Clone repository
git clone https://github.com/sorrowscry86/CCC.git
cd CCC

# Create and activate virtual environment
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-YourKeyHere"
# Windows (Command Prompt)
set OPENAI_API_KEY=sk-YourKeyHere
# macOS/Linux
export OPENAI_API_KEY='sk-YourKeyHere'
```

## Usage & Operations
**Starting the Proxy Server**:
```bash
python proxy_server.py
```
The server runs on http://127.0.0.1:5111

**API Endpoints**:
- `POST /v1/chat/completions`: Standard chat completions (Stage 1)
- `GET /health`: Health check endpoint
- `POST /api/v2/sessions`: Create memory sessions (Stage 2)
- `GET /api/v2/sessions/{id}`: Retrieve session info (Stage 2)
- `GET /api/v2/sessions/{id}/context`: Get relevant context (Stage 2)
- `POST /v2/chat/completions`: Memory-enhanced chat completions (Stage 2)

**Using the Web Interface**:
Open `resonant_loop_lab.html` in a web browser after starting the proxy server.

## Database
**Type**: SQLite
**Schema**:
- sessions: Stores user session information
- conversations: Stores conversation metadata
- turns: Stores individual conversation turns
- agent_states: Tracks agent learning and state
- context_summaries: Stores processed context for efficient retrieval
- causal_events: Stores cause-and-effect relationships (Causal Memory Core)

## Memory System
**Components**:
- **MemoryDAL**: Data access layer for database operations
- **MemoryService**: High-level memory operations with caching
- **CausalMemoryCore**: Cause-and-effect context recognition
- **Models**: Data models for sessions, conversations, turns, and agent states

## Example Usage
```python
# Initialize memory components
dal = MemoryDAL('demo_memory.db')
await dal.initialize_database()
memory_service = MemoryService(dal)

# Create a session
session = await memory_service.initialize_session({
    'user_name': 'Demo User',
    'preferences': {'context_depth': 10}
})

# Create and store a conversation
conversation = await memory_service.create_conversation(
    session.session_id,
    "Create a Python function that validates email addresses"
)

# Retrieve relevant context
context = await memory_service.get_relevant_context(
    session.session_id,
    "Create a function to validate phone numbers",
    max_context_turns=5
)
```