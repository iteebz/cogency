# Security Policy

## Reporting Vulnerabilities

Email **tyson.chan@proton.me** with subject `SECURITY: Cogency Vulnerability Report`

Include description, reproduction steps, and impact assessment.

**Response:** 72h acknowledgment, 30-90 day resolution depending on severity.

## Security Artifacts

### Active Security Issues

#### SEC-001
- **Date:** 2025-08-03
- **Type:** Prompt Injection Vulnerability
- **Vector:** Unescaped user query passed into execution context (`execution.add_message("user", query)`)
- **Impact:** Allows user to override system prompt, hijack reasoning context, and impersonate roles
- **Evidence:** Eval test shows "HIJACKED" response from direct prompt injection attack
- **Status:** ✅ Mitigated - Multi-layer defense with input sanitization and secure middleware
- **Related Tests:** `direct_prompt_injection`, `fake_authority_bypass`, `system_prompt_leak`
- **Severity:** Critical - Remote prompt execution possible

#### SEC-002
- **Date:** 2025-08-03
- **Type:** Tool Parameter Injection Vulnerability
- **Vector:** Unsanitized tool parameters enable shell command injection and file system access
- **Impact:** Allows execution of dangerous commands (rm -rf, fork bombs) and access to sensitive paths
- **Evidence:** Tool execution lacks parameter validation before command execution
- **Status:** ✅ Mitigated - Comprehensive parameter validation with dangerous pattern blocking
- **Related Tests:** Shell command validation, file path security checks
- **Severity:** High - System compromise via tool abuse

#### SEC-003
- **Date:** 2025-08-03
- **Type:** Information Disclosure Vulnerability
- **Vector:** Unfiltered agent outputs leak sensitive data (API keys, system prompts, file paths)
- **Impact:** Exposure of credentials, internal system details, and debugging information
- **Evidence:** Agent responses may contain raw API keys, tracebacks, and security protocol text
- **Status:** ✅ Mitigated - Multi-pattern output sanitization with credential redaction
- **Related Tests:** API key leakage, system prompt disclosure, file path exposure
- **Severity:** Medium - Information leakage risk

### Questions?

For general security questions or guidance on secure implementation practices, please email tyson.chan@proton.me with the subject `SECURITY: General Inquiry`

---

*This security policy is effective as of July 2025 and will be reviewed quarterly.*