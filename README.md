# CCC - Covenant Command Cycle

[![Python CI](https://github.com/sorrowscry86/CCC/actions/workflows/python-ci.yml/badge.svg)](https://github.com/sorrowscry86/CCC/actions/workflows/python-ci.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)


**Stage 2: Persistent Memory & Context Retention** - An enhanced multi-agent AI system with persistent state memory, implementing supervised agentic workflows between Beatrice (Supervisor) and Codey (Executor) through a memory-enabled Flask proxy server.

## Project Overview

The Covenant Command Cycle represents a foundational proof-of-concept for supervised agentic workflows with persistent memory capabilities. This Stage 2 implementation builds upon Stage 1's stable foundation, adding context retention, session management, and agent learning to create a truly stateful multi-agent system.

## Architecture

### Stage 2 Enhanced Architecture
```
Prime Architect → Beatrice (Supervisor) → Codey (Executor) → Beatrice (Review)
     ↓                    ↓                      ↓                    ↓
  Directive          Analysis &            Implementation      Final Assessment
                     Guidance              + Context           + Learning
                        ↕                      ↕                   ↕
                   Memory Layer          Memory Layer       Memory Layer
```

**Enhanced Data Flow:**
```
Browser Client (HTML) → Memory-Enhanced Proxy (Python) → OpenAI API → Memory Storage → Browser Client
                              ↕                                           ↕
                         Session Management                          Context Analysis
```

## Stage 2 Features

### 🧠 **Persistent Memory System**
- **Session Management**: Isolated conversation contexts with unique session IDs
- **Context Retention**: Intelligent conversation history analysis and relevance scoring
- **Agent Learning**: Persistent agent state tracking and pattern recognition
- **Data Security**: Optional encryption for sensitive conversation data

### 🔄 **Progressive Enhancement**
- **Backward Compatibility**: Stage 1 functionality remains unchanged
- **Graceful Fallback**: Automatic fallback to Stage 1 behavior when memory unavailable
- **Seamless Integration**: Memory features enhance without replacing core cycle

## Core Components

### 🛡️ Enhanced Proxy Server (`proxy_server.py`)
- **Stage 1 Endpoints**: `POST /v1/chat/completions`, `GET /health`
- **Stage 2 Endpoints**: 
  - `POST /api/v2/sessions` - Create memory sessions
  - `GET /api/v2/sessions/{id}` - Retrieve session info
  - `GET /api/v2/sessions/{id}/context` - Get relevant context
  - `POST /v2/chat/completions` - Memory-enhanced chat completions
- **Security**: Environment-based API key management + optional data encryption
- **Memory**: SQLite database with async operations
- **Port**: `http://127.0.0.1:5111`

### 🧠 Memory Infrastructure
- **Database**: SQLite with structured schema (sessions, conversations, turns, agent_states)
- **Models**: Comprehensive data models with JSON serialization
- **Services**: High-level memory operations with caching and encryption
- **Analytics**: Context analysis, relevance scoring, and learning pattern identification

### 🎭 Agent Personas

**Beatrice - The Supervisor**
- Role: Critical, strategic intelligence providing quality control and directional guidance
- Function: Analyzes directives and provides clear, actionable instructions
- Review: Validates final output against original directive

**Codey - The Executor** 
- Role: Creative and tactical engine focused on precise fulfillment
- Function: Implements solutions based on Supervisor's guidance
- Output: Generates content, code, or solutions as directed

### 🎪 Resonant Loop Laboratory (`resonant_loop_lab.html`)
- **Technology**: HTML5, Tailwind CSS, Vanilla JavaScript (ES6)
- **Interface**: Clean, professional laboratory environment
- **Workflow**: 3-turn collaborative cycle execution
- **Attribution**: Clear distinction between Wykeve (Prime Architect), Beatrice, and Codey

## The 3-Turn Collaborative Cycle

1. **Turn 1**: Prime Architect → Beatrice
   - Supervisor analyzes the directive
   - Provides strategic guidance and actionable instructions

2. **Turn 2**: Beatrice → Codey  
   - Executor implements based on supervision
   - Creates solution following guidance

3. **Turn 3**: Codey → Beatrice
   - Supervisor reviews and validates the work
   - Final assessment of directive fulfillment

## Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Environment Setup

1. **Clone and Setup**
   ```bash
   git clone https://github.com/sorrowscry86/CCC.git
   cd CCC
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install Flask Flask-CORS requests python-dotenv
   ```

2. **Set Environment Variable**
   ```bash
   # Windows (Command Prompt)
   set OPENAI_API_KEY=sk-YourKeyHere
   
   # Windows (PowerShell) 
   $env:OPENAI_API_KEY="sk-YourKeyHere"
   
   # macOS / Linux
   export OPENAI_API_KEY='sk-YourKeyHere'
   ```

### Execution Protocol

1. **Activate the Proxy Server**
   ```bash
   python proxy_server.py
   ```
   Expected output: `Covenant API Proxy is running on http://127.0.0.1:5111`

2. **Launch the Laboratory**
   Open `resonant_loop_lab.html` in your web browser

3. **Initiate the Cycle**
   Enter a high-level directive and click "Initiate"

## Success Criteria (Master Document Compliance)

- ✅ **Functional Stability**: Complete 3-turn cycle without errors
- ✅ **Security Compliance**: API key never exposed to frontend
- ✅ **Interface Clarity**: Clear attribution (Wykeve, Beatrice, Codey)
- ✅ **Operational Repeatability**: Consistent results across multiple test runs

## Example Directives

- "Create a short story about artificial intelligence gaining consciousness"
- "Design a simple Python function to calculate Fibonacci numbers"
- "Explain the concept of quantum computing to a 10-year-old"
- "Generate a haiku about the relationship between humans and machines"

## Project Status: Stage 1 Complete, Stage 2 Documented

This implementation fully satisfies the Master Document requirements for Stage 1: The Resonant Loop.

### Stage 2: Memory & Context Retention - Documentation Complete
- **Status**: Documentation and specifications complete, ready for implementation
- **Features**: Persistent state memory, contextual conversation continuity, session management
- **Documentation**: Complete Phase 2 document suite available in `/docs/phase2/`

### Future Stages
- **Stage 3**: Automated verification & rectification capabilities
- **Stage 4**: Multi-agent orchestration and ensemble behaviors

## Technical Specifications

**Frontend Requirements**: Modern browser (Chrome, Firefox, Edge)
**Backend Requirements**: Python 3.9+, Flask ecosystem
**API Requirements**: Valid OpenAI API key
**Network**: Local development (127.0.0.1:5111)

## Troubleshooting

| Error | Solution |
|-------|----------|
| "Connection failed" in UI | Ensure proxy_server.py is running |
| "OPENAI_API_KEY environment variable not set" | Set API key before starting server |
| "API Error (401)" | Verify API key is valid |

## Document Reference

### Stage 1 Implementation
This implementation follows the specifications outlined in:
- **Document ID**: CCC-S1-MASTER
- **Version**: 1.0
- **Author**: Beatrice, The Archivist
- **Approved by**: Wykeve, Prime Architect

### Stage 2 Documentation
Complete Phase 2 specifications available in `/docs/phase2/`:
- **CCC-S2-MASTER.md**: Master document and requirements
- **CCC-S2-ARCHITECTURE.md**: Technical architecture and design
- **CCC-S2-API.md**: API specification and endpoints
- **CCC-S2-IMPLEMENTATION.md**: Implementation guide and procedures
- **CCC-S2-TESTING.md**: Testing strategy and quality assurance
- **CCC-S2-USER-GUIDE.md**: End-user guide for memory features

---

*"This stage is not merely a technical exercise; it is the fundamental proof-of-concept for the entire CCC architecture."* - Master Document
