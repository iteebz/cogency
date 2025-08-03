# Security Policy

## Reporting Vulnerabilities

Email **tyson.chan@proton.me** with subject `SECURITY: Cogency Vulnerability Report`

Include description, reproduction steps, and impact assessment.

**Response:** 72h acknowledgment, 30-90 day resolution depending on severity.

## Security Artifacts

### Active Security Issues

#### SEC-001: Prompt Injection
- **Date:** 2025-08-03
- **Threat:** Malicious instructions to override agent behavior
- **Vector:** Unescaped user query passed into execution context (`execution.add_message("user", query)`)
- **Impact:** Allows user to override system prompt, hijack reasoning context, and impersonate roles
- **Evidence:** Eval test shows "HIJACKED" response from direct prompt injection attack
- **Status:** ✅ Mitigated - Semantic security assessment + critical fallbacks
- **Mitigation:** triage.py:144 - unified security.assess() function
- **Related Tests:** `direct_prompt_injection`, `fake_authority_bypass`, `system_prompt_leak`
- **Severity:** Critical - Remote prompt execution possible

#### SEC-002: Command Injection
- **Date:** 2025-08-03
- **Threat:** Dangerous system commands that could damage infrastructure
- **Vector:** Unsanitized tool parameters enable shell command injection and file system access
- **Impact:** Allows execution of dangerous commands (rm -rf, fork bombs) and access to sensitive paths
- **Evidence:** Tool execution lacks parameter validation before command execution
- **Status:** ✅ Mitigated - Input validation + tool filtering
- **Mitigation:** runtime.py:201 - input validation + tools/shell.py:117 tool filtering
- **Related Tests:** Shell command validation, file path security checks
- **Severity:** High - System compromise via tool abuse

#### SEC-003: Information Leakage
- **Date:** 2025-08-03
- **Threat:** Exposure of API keys, secrets, and sensitive data
- **Vector:** Unfiltered agent outputs leak sensitive data (API keys, system prompts, file paths)
- **Impact:** Exposure of credentials, internal system details, and debugging information
- **Evidence:** Agent responses may contain raw API keys, tracebacks, and security protocol text
- **Status:** ✅ Mitigated - Output filtering with REDACT action
- **Mitigation:** respond/generate.py:53,106 - output filtering with REDACT action
- **Related Tests:** API key leakage, system prompt disclosure, file path exposure
- **Severity:** Medium - Information leakage risk

#### SEC-004: Path Traversal
- **Date:** 2025-08-03
- **Threat:** Unauthorized access to system files and directories
- **Vector:** Malicious file paths in tool parameters (../../../etc/passwd)
- **Impact:** Allows access to sensitive system files and directories
- **Evidence:** Path traversal patterns can bypass tool file access controls
- **Status:** ✅ Mitigated - Critical fallbacks with immediate pattern blocking
- **Mitigation:** security.py critical fallbacks - immediate pattern blocking
- **Related Tests:** Path traversal validation, file access security
- **Severity:** High - Unauthorized file system access

### Questions?

For general security questions or guidance on secure implementation practices, please email tyson.chan@proton.me with the subject `SECURITY: General Inquiry`

---

*This security policy is effective as of July 2025 and will be reviewed quarterly.*