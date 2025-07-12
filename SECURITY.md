# Security Policy

## Supported Versions

We actively maintain security updates for the following versions:

| Version | Supported          | Notes                   |
| ------- | ------------------ | ----------------------- |
| 0.2.x   | :white_check_mark: | Current stable release  |
| < 0.2.0 | :x:                | Please upgrade to 0.2.x |

## Reporting a Vulnerability

If you discover a security vulnerability in Cogency, please report it responsibly through our coordinated disclosure process.

### Contact Method
Send an email to **tyson.chan@proton.me** with the subject line `SECURITY: Cogency Vulnerability Report`

**Please include:**
- Detailed description of the vulnerability
- Step-by-step reproduction instructions
- Potential impact and attack scenarios
- Affected versions (if known)
- Suggested remediation approaches (optional)
- Your preferred contact method for follow-up

### Response Timeline
- **Acknowledgment:** Within 48 hours of receipt
- **Initial Assessment:** Within 5 business days
- **Regular Updates:** Every 7 days during active investigation
- **Critical Issues:** Expedited response within 24 hours
- **Resolution Target:** 30 days for critical, 90 days for non-critical vulnerabilities

### Security Scope

Given Cogency's cognitive architecture, we're particularly concerned with vulnerabilities in these areas:

#### High Priority
- **Prompt Injection Attacks:** Malicious inputs that manipulate agent reasoning or tool selection
- **Code Execution Vulnerabilities:** Unsafe operations in BaseTool implementations
- **Input Validation Bypass:** Malformed parameters that circumvent tool safety checks
- **Tool Chain Exploitation:** Abuse of multi-tool workflows for privilege escalation

#### Medium Priority  
- **Information Disclosure:** Sensitive data exposure through execution traces or error messages
- **Denial of Service:** Resource exhaustion through malicious tool orchestration
- **Configuration Tampering:** Unauthorized modification of agent behavior or tool access
- **Dependency Vulnerabilities:** Security issues in third-party libraries

#### Documentation & Examples
- **Insecure Usage Patterns:** Examples that demonstrate unsafe implementation practices
- **Misleading Security Guidance:** Documentation that could lead to insecure deployments

### Resolution Process

1. **Triage:** Vulnerability assessment and severity classification
2. **Investigation:** Root cause analysis and impact evaluation  
3. **Development:** Security patch creation and testing
4. **Review:** Internal security review and validation
5. **Coordination:** Timeline discussion with reporter
6. **Release:** Patch deployment and security advisory publication
7. **Disclosure:** Public notification and credit attribution

### Severity Classification

- **Critical:** Remote code execution, privilege escalation, or widespread data exposure
- **High:** Significant security bypass or sensitive information disclosure
- **Medium:** Limited security impact or requires specific conditions
- **Low:** Minor security concerns or theoretical vulnerabilities

### Public Disclosure Policy

We follow responsible disclosure practices:
- **Coordination:** Work with reporters to determine appropriate disclosure timeline
- **Embargo Period:** Minimum 30 days for non-critical issues, negotiable for critical vulnerabilities
- **Public Advisory:** Security advisories published after patch release
- **CVE Assignment:** Request CVE identifiers for significant vulnerabilities when appropriate

### Recognition

Security researchers who responsibly disclose vulnerabilities will be:
- Acknowledged in security advisories and release notes
- Listed in our project security contributors (unless anonymity is preferred)
- Invited to review our security improvements related to their findings

### Out of Scope

The following are generally considered out of scope:
- Vulnerabilities in third-party dependencies (please report directly to maintainers)
- Issues requiring physical access to the system
- Social engineering attacks
- Denial of service attacks requiring excessive resources

### Security Best Practices

When implementing Cogency in production:
- **Input Validation:** Always validate and sanitize tool inputs
- **Execution Isolation:** Run agents in sandboxed environments when possible
- **Trace Sanitization:** Review execution traces for sensitive information before logging
- **Tool Auditing:** Regularly audit custom BaseTool implementations
- **Dependency Management:** Keep dependencies updated and monitor for vulnerabilities

### Questions?

For general security questions or guidance on secure implementation practices, please email tyson.chan@proton.me with the subject `SECURITY: General Inquiry`

---

*This security policy is effective as of July 2025 and will be reviewed quarterly.*