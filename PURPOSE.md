# Purpose

Cogency is a streaming agent framework. This document defines who it's for and what success looks like.

## Origin

**What task triggered building cogency?**

<!-- @human: Fill in the original problem that led to this project -->

## Audience

**Who is the intended user?**

- [ ] Internal infrastructure (swarm tooling only)
- [ ] External developers (open source product)
- [ ] Both (internal-first with external distribution)

<!-- @human: Check one and elaborate if needed -->

## Success

**What does success look like in 6 months?**

<!-- @human: Define measurable outcomes — adoption metrics, capability milestones, or revenue targets -->

## Differentiation

**Why cogency instead of langchain/autogen/crewai?**

Current technical differentiators:
- Stateless context assembly (crash recovery, no state corruption)
- Resume mode via WebSocket (O(n) vs O(n²) token efficiency)
- Protocol/storage separation (clean events, synthesized wire format)

<!-- @human: Which of these matter to the target audience? What problem do they solve that alternatives don't? -->

---

*All cogency work blocked until this document is complete. See decision 6090cf85.*
