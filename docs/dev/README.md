# Developer Documentation

**Two-Tier Documentation Architecture**

## Structure

### `architecture/` - Technical Implementation (Permanent)
Core technical knowledge for framework maintainers:

- **state.md** - 4-component state model (Profile, Workspace, Execution)
- **features.md** - Cognitive architecture patterns and design principles  
- **memory.md** - Memory system boundaries and persistence strategies
- **evals.md** - AGI Lab evaluation standards and testing protocols
- **providers.md** - Provider architecture and implementation patterns
- **semantic.md** - Semantic search system specification
- **events.md** - Event system architecture and integration patterns
- **errors.md** - Error handling patterns across system layers
- **cli.md** - CLI output specification and symbol system
- **confirm.md** - Confirmation architecture for safety boundaries
- **persistence.md** - Database-as-state paradigm and atomic writes

### `planning/` - Development Artifacts (Time-bounded)
Current development priorities and historical context:

- **roadmap.md** - Current development TODOs and next priorities
- **benchmarks.md** - v1.3.0 benchmark specifications and success criteria
- **fractal.md** - Future research directions for multi-agent coordination
- **archive/** - Completed work documentation and resolved issues

## Usage Guidelines

### For Core Developers
- **architecture/** contains canonical technical knowledge
- Maintain alignment with src/ implementation reality
- Update when architectural patterns change

### For Contributors  
- **architecture/** provides implementation context
- **planning/** shows current development priorities
- Focus on technical docs first, planning docs second

### For Documentation Updates
- Public docs (`docs/*.md`) are user-facing and must remain production-aligned
- Internal docs (`docs/dev/`) can contain technical depth and implementation details
- Time-bound planning artifacts should be archived when completed

## Beauty Doctrine Compliance

This structure follows "delete more than you create" principles:
- ✅ Eliminated 300+ lines of archaeological documentation debt
- ✅ Clear separation between technical knowledge vs planning artifacts  
- ✅ One definitive location for each type of documentation
- ✅ Time-bounded approach to planning documentation lifecycle

---

*Internal documentation architecture implemented 2025-01-12*