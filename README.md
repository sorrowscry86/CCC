# CCC - Covenant Command Cycle

**Stage 1: The Resonant Loop** - A precisely architected multi-agent AI system implementing a supervised agentic workflow between Beatrice (Supervisor) and Codey (Executor) through a secure Flask proxy server.

## Project Overview

The Covenant Command Cycle represents a foundational proof-of-concept for supervised agentic workflows. This Stage 1 implementation establishes a stable, secure connection between two distinct AI agents that collaborate through a defined 3-turn cycle to execute high-level directives from the Prime Architect.

## Architecture

```
Prime Architect → Beatrice (Supervisor) → Codey (Executor) → Beatrice (Review)
     ↓                    ↓                      ↓                    ↓
  Directive          Analysis &            Implementation      Final Assessment
                     Guidance
```

**Data Flow:**
```
Browser Client (HTML) → Local Proxy Server (Python) → OpenAI API → Local Proxy Server → Browser Client
```

## Core Components

### 🛡️ Secure Proxy Server (`proxy_server.py`)
- **Endpoint**: `POST /v1/chat/completions` (mirroring OpenAI API structure)
- **Security**: Reads `OPENAI_API_KEY` from environment variables only
- **Health Check**: `GET /health` for system monitoring
- **Port**: `http://127.0.0.1:5111` (as specified)

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

## Project Status: Stage 1 Complete

This implementation fully satisfies the Master Document requirements for Stage 1: The Resonant Loop. Future stages will introduce:
- **Stage 2**: Persistent state memory and context retention
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

This implementation follows the specifications outlined in:
- **Document ID**: CCC-S1-MASTER
- **Version**: 1.0
- **Author**: Beatrice, The Archivist
- **Approved by**: Wykeve, Prime Architect

---

*"This stage is not merely a technical exercise; it is the fundamental proof-of-concept for the entire CCC architecture."* - Master Document
