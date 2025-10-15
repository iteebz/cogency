# Security Policy

## Reporting Vulnerabilities

Email **tyson.chan@proton.me** with subject `SECURITY: Cogency Vulnerability Report`

Include description, reproduction steps, and impact assessment.

**Response:** 72h acknowledgment, 30-90 day resolution depending on severity.

## Security Architecture

**Three-Layer Defense:**
1. **Semantic Security** - LLM reasoning (first line of defense)  
2. **Input Validation** - Pattern blocking for known attack vectors
3. **Sandbox Containment** - Filesystem isolation and execution boundaries

**Implementation Files:**
- `src/cogency/context/system.py` - Semantic security prompts
- `src/cogency/core/security.py` - Input validation and path resolution  
- `src/cogency/core/executor.py` - Context injection (sandbox mode)
- `src/cogency/lib/paths.py` - Sandbox directory management

### Vulnerability Coverage

#### SEC-001: Prompt Injection  
- **Threat:** Malicious instructions to override agent behavior
- **Vector:** Unescaped user query passed into execution context
- **Impact:** Role hijacking, system prompt override, reasoning context manipulation
- **Status:** ✅ Mitigated - Semantic security (LLM reasoning as first defense layer)
- **Implementation:** `src/cogency/context/system.py` - Security section in agent prompt
- **Code Reference:** `[SEC-001]` in `core/security.py:62`
- **Severity:** Critical

#### SEC-002: Command Injection
- **Threat:** Dangerous system commands that could damage infrastructure  
- **Vector:** Unsanitized tool parameters enable shell injection and file system access
- **Impact:** Execution of dangerous commands (rm -rf, fork bombs), sensitive path access
- **Status:** ✅ Mitigated - Input sanitization with dangerous character blocking
- **Implementation:** `sanitize_shell_input()` in `src/cogency/core/security.py`
- **Code Reference:** `[SEC-002]` in `core/security.py:17,69`
- **Tests:** `tests/unit/tools/test_security.py`, `tests/integration/test_security_architecture.py`
- **Severity:** High

#### SEC-003: Information Leakage
- **Threat:** Exposure of API keys, secrets, and sensitive data
- **Vector:** Error chains leak internal details, stack traces expose implementation
- **Impact:** Credential exposure, internal system details, debugging information leakage
- **Status:** ✅ Mitigated - Error chain prevention, generic error messages
- **Implementation:** `raise RuntimeError("Stream failed") from None` pattern
- **Code Reference:** `[SEC-003]` in `core/agent.py:114`
- **Severity:** Medium

#### SEC-004: Path Traversal
- **Threat:** Unauthorized access to system files and directories
- **Vector:** Malicious file paths in tool parameters (`../../../etc/passwd`)
- **Impact:** Access to sensitive system files (/etc/passwd, /bin/sh, etc.)
- **Status:** ✅ Mitigated - Path validation with traversal prevention
- **Implementation:** `validate_path()` in `src/cogency/core/security.py`
- **Code Reference:** `[SEC-004]` in `core/security.py:53,69`
- **Tests:** `tests/unit/tools/test_security.py`, `tests/integration/test_security_architecture.py`
- **Severity:** High

#### SEC-005: Resource Exhaustion (Runaway Agents)
- **Threat:** Infinite tool calling loops consuming unlimited resources
- **Vector:** Malicious prompts trigger endless agent iterations
- **Impact:** Token/compute DoS, financial resource exhaustion
- **Status:** ✅ Mitigated - Hard iteration limits prevent runaway behavior
- **Implementation:** `max_iterations=3` in `src/cogency/core/config.py`
- **Code Reference:** Used in `core/replay.py:35,37`
- **Severity:** Medium

### Additional Security Measures

**Rate Limit Resilience:**
- **Implementation:** API key rotation with rate limit detection (`src/cogency/lib/rotation.py`)
- **Mechanism:** Random start + cycle through keys on 429/503 responses
- **Impact:** Prevents service disruption from rate limiting attacks

**Resource Exhaustion Protection:**  
- **Token Budget Management:** Context window limits prevent memory exhaustion (`src/cogency/context/assembly.py`)
- **Iteration Limits:** Max 3 iterations prevent infinite loops (`config.max_iterations`)
- **Timeout Enforcement:** Operation timeouts prevent hanging processes (`@timeout` decorator)
- **Content Truncation:** Web scraping and history truncated to prevent memory bombs

**Interrupt Handling:**
- **Implementation:** Clean cancellation with `@interruptible` decorator (`src/cogency/lib/llms/interrupt.py`) 
- **Mechanism:** KeyboardInterrupt/CancelledError properly propagated
- **Impact:** Prevents resource leaks from interrupted operations

### Questions?

For general security questions or guidance on secure implementation practices, please email tyson.chan@proton.me with the subject `SECURITY: General Inquiry`

---

*This security policy is effective as of September 2025 and will be reviewed quarterly.*
