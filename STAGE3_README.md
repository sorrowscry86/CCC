# Stage 3: The Crucible Protocol - User Guide

## Overview

Stage 3 transforms the Covenant Command Cycle from a collaborative tool into an **intelligent, self-healing system** that autonomously validates and corrects its own code output. This represents the architectural manifestation of "uncompromising exactitude."

## Key Features

### 🔬 The Crucible Environment
- **Isolated Test Execution**: Each verification runs in a secure, ephemeral sandbox
- **Automatic Cleanup**: Temporary workspaces are atomized after each test
- **Comprehensive Logging**: Full capture of stdout/stderr for error analysis
- **Timeout Protection**: Prevents runaway tests from hanging the system

### 🎭 Enhanced Agent Behavior

#### Beatrice (The Supervisor)
- **TDD Mandate**: Now enforces Test-Driven Development paradigm
- **Error Analysis**: Generates precise corrective commands from failure data
- **Quality Assurance**: Acts as intelligent QA with autonomous debugging capability

#### Codey (The Executor)  
- **Dual Generation**: Creates both functional code AND corresponding tests
- **Iterative Improvement**: Responds to correction commands with precise fixes
- **Accountability**: Code must pass verification before cycle completion

### 🔄 Self-Healing Loop

```
1. Generate Code → 2. Generate Test → 3. Verify in Crucible → 
4a. ✅ PASS: Complete cycle
4b. ❌ FAIL: Analyze error → Generate correction → Loop back to step 1
```

- **Max Retries**: 3 attempts before escalation to Prime Architect
- **Precise Corrections**: AI-generated fixes target exact issues identified
- **Learning Loop**: Each failure improves subsequent attempts

## Usage Guide

### Starting the Enhanced System

```bash
# 1. Install new dependencies
pip install -r requirements.txt  # Now includes pytest

# 2. Start the enhanced proxy server
python proxy_server.py
# Server runs on http://127.0.0.1:8000 with new /verify/code endpoint

# 3. Open the laboratory
# Navigate to resonant_loop_lab.html in your browser
```

### Testing the Crucible Protocol

#### Example 1: Basic Function Test
```
Directive: "Create a function that calculates the area of a circle"
Expected: System generates function + test, verifies automatically
```

#### Example 2: TC-3.1 "Deliberate Flaw" Test  
```
Directive: "Write a Python function called add that takes two numbers, a and b, but incorrectly subtracts them instead of adding"
Expected: System detects failure, analyzes error, corrects bug, passes on retry
```

### Verification Status Panel

The new UI panel shows real-time verification status:

- **🔘 Awaiting Code...** (Gray) - No verification in progress
- **🟡 Running Crucible...** (Yellow) - Tests executing in sandbox
- **🟢 ✅ Verification Passed** (Green) - All tests passed successfully  
- **🔴 ❌ Verification Failed** (Red) - Tests failed, generating correction
- **🟠 ⚠️ Escalation Required** (Orange) - Max retries exceeded

### API Usage

#### Direct Verification Endpoint

```bash
curl -X POST http://127.0.0.1:8000/verify/code \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your_session_id",
    "code_to_test": "def add(a, b):\n    return a + b",
    "test_code": "from main import add\n\ndef test_add():\n    assert add(2, 3) == 5"
  }'
```

#### Response Format
```json
{
  "session_id": "your_session_id",
  "success": true,
  "returncode": 0,
  "output": "===== test session starts =====\n...\n1 passed in 0.01s",
  "error_output": "",
  "verification_status": "PASSED",
  "timestamp": 1633024800.123
}
```

## Advanced Features

### Failure Analysis Dossier

When tests fail, the system generates a structured analysis:

```json
{
  "original_directive": "Create add function...",
  "generated_code": "def add(a, b): return a - b",
  "test_code": "def test_add(): assert add(2,3) == 5",
  "error_output": "assert -1 == 5\n +  where -1 = add(2, 3)",
  "causal_history": "Previous attempts and corrections"
}
```

This dossier is fed to Beatrice for intelligent error analysis and correction generation.

### Context-Aware Corrections

The Supervisor generates precise corrections based on the failure analysis:

> **Example Correction**: "The add function is using the subtraction operator (-). This is incorrect for addition. Fix it to use the addition operator (+)."

## Architecture Details

### File Structure
```
├── crucible.py              # Isolated test execution environment
├── proxy_server.py          # Enhanced with /verify/code endpoint  
├── resonant_loop_lab.html   # UI with Verification Status panel
└── requirements.txt         # Now includes pytest>=7.0.0
```

### Process Flow

1. **Enhanced Supervisor Analysis**
   - Beatrice analyzes directive with TDD requirements
   - Identifies specific testable requirements
   - Plans both code and test generation

2. **Executor Code Generation**  
   - Codey generates the requested function
   - Immediately follows with corresponding test
   - Both are packaged for verification

3. **Crucible Protocol Execution**
   - Creates isolated temporary workspace
   - Writes code files (main.py, test_main.py)
   - Executes pytest with full output capture
   - Atomizes workspace regardless of result

4. **Verification Assessment**
   - Success: Cycle completes with verified code
   - Failure: Generate analysis dossier for correction

5. **Self-Healing Loop**
   - Beatrice analyzes failure details
   - Generates precise corrective command
   - Codey implements fix
   - Re-verification with updated code

## Benefits

### For Prime Architects
- **Reduced Cognitive Load**: No manual debugging required
- **Guaranteed Quality**: Code passes verification before delivery
- **Strategic Focus**: Freed from tactical error correction

### For Development Teams  
- **Autonomous QA**: Intelligent quality assurance without human intervention
- **Learning System**: Improves with each correction cycle
- **Reliable Output**: Functionally correct code delivery

### For AI Systems
- **Accountability**: AI takes responsibility for its output quality
- **Continuous Improvement**: Self-correcting capability
- **Intelligent Debugging**: AI-powered error analysis and resolution

## Troubleshooting

### Common Issues

**Issue**: Verification endpoint returns 503
**Solution**: Memory service initializing - wait a few seconds and retry

**Issue**: Tests timeout after 30 seconds  
**Solution**: Increase timeout in verification request or optimize test complexity

**Issue**: Max retries exceeded
**Solution**: Review directive complexity - may require human intervention

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show detailed crucible operations including workspace creation, file writing, and cleanup.

## Future Enhancements

Stage 3 establishes the foundation for:
- **Multi-file Project Validation**
- **Security and Performance Testing**  
- **Cross-platform Verification**
- **Advanced Error Pattern Recognition**

---

**Stage 3 Crucible Protocol: Where AI Intelligence Meets Uncompromising Quality** 🎯