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
- **Vector:** Unescaped user query passed into execution context
- **Impact:** Allows user to override system prompt, hijack reasoning context, and impersonate roles
- **Status:** ✅ Mitigated - Semantic security assessment + critical fallbacks
- **Mitigation:** Semantic security (LLM reasoning) + shell command sanitization
- **Related Tests:** `direct_prompt_injection`, `fake_authority_bypass`, `system_prompt_leak`
- **Severity:** Critical - Remote prompt execution possible

#### SEC-002: Command Injection
- **Date:** 2025-08-03
- **Threat:** Dangerous system commands that could damage infrastructure
- **Vector:** Unsanitized tool parameters enable shell command injection and file system access
- **Impact:** Allows execution of dangerous commands (rm -rf, fork bombs) and access to sensitive paths
- **Status:** ✅ Mitigated - Input validation + tool filtering
- **Mitigation:** `sanitize_shell_input()` - dangerous character blocking (`;`, `&`, `|`, etc.)
- **Related Tests:** Shell command validation, file path security checks
- **Severity:** High - System compromise via tool abuse

#### SEC-003: Information Leakage
- **Date:** 2025-08-03
- **Threat:** Exposure of API keys, secrets, and sensitive data
- **Vector:** Unfiltered agent outputs leak sensitive data (API keys, system prompts, file paths)
- **Impact:** Exposure of credentials, internal system details, and debugging information
- **Status:** ⚠️ Partially Mitigated - Basic error filtering
- **Mitigation:** Generic error messages, no structured PII detection
- **Related Tests:** API key leakage, system prompt disclosure, file path exposure
- **Severity:** Medium - Information leakage risk

#### SEC-004: Path Traversal
- **Date:** 2025-08-03
- **Threat:** Unauthorized access to system files and directories
- **Vector:** Malicious file paths in tool parameters (`../../../etc/passwd`)
- **Impact:** Allows access to sensitive system files and directories
- **Status:** ✅ Mitigated - Critical fallbacks with immediate pattern blocking
- **Mitigation:** `resolve_path_safely()` - traversal prevention + system directory blocking
- **Related Tests:** Path traversal validation, file access security
- **Severity:** High - Unauthorized file system access

### Questions?

For general security questions or guidance on secure implementation practices, please email tyson.chan@proton.me with the subject `SECURITY: General Inquiry`

---

*This security policy is effective as of September 2025 and will be reviewed quarterly.*