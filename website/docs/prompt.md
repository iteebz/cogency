# Cogency OSS Project Requirements & Recommendations

## Autodocs Integration for Landing Page

### Priority: High

The Cogency landing page SEO strategy requires automated API documentation to capture developer search traffic. We need to implement autodocs integration between the OSS project and the marketing site.

### Required Implementation in oss/cogency:

1. **Docstring Standards**
   - Ensure all public classes/methods have comprehensive docstrings
   - Use Google/Sphinx style for consistency
   - Include code examples in docstrings where applicable

2. **API Documentation Generation**
   - Implement `sphinx-autodoc` or similar for Python API docs
   - Generate JSON/markdown output that can be consumed by Astro
   - Consider `pdoc` for simpler HTML generation

3. **Documentation Structure Needed**

   ```
   docs/
   ├── api/
   │   ├── agent.md
   │   ├── llm.md
   │   ├── tools.md
   │   └── streaming.md
   ├── guides/
   │   ├── getting-started.md
   │   ├── custom-tools.md
   │   └── deployment.md
   └── examples/
       ├── basic-agent.md
       ├── streaming-agent.md
       └── production-setup.md
   ```

4. **Build Integration**
   - Add docs generation to CI/CD pipeline
   - Auto-update landing site when docs change
   - Consider GitHub Actions to trigger Astro rebuild

### SEO Impact

- **Target Keywords**: "cogency API documentation", "python AI agent docs", "cogency framework reference"
- **Long-tail Traffic**: Each class/method becomes a searchable page
- **Developer Trust**: Live, accurate documentation builds credibility

### Landing Page Integration Points

1. **Astro Pages to Create**
   - `/docs/api/[...slug].astro` - Dynamic API documentation pages
   - `/docs/guides/[...slug].astro` - Tutorial and guide pages
   - `/examples/[...slug].astro` - Example showcase pages

2. **Navigation Integration**
   - Add docs link to main navigation
   - Create docs sidebar navigation
   - Link from feature pages to relevant docs

3. **Content Strategy**
   - API docs target technical keywords
   - Guides target how-to keywords
   - Examples target implementation keywords

### Technical Requirements for OSS Project

1. **Documentation Toolchain**

   ```bash
   pip install sphinx sphinx-autodoc sphinx-rtd-theme
   # OR
   pip install pdoc3
   # OR
   pip install mkdocs-material mkdocstrings
   ```

2. **Build Script Example**

   ```python
   # scripts/generate_docs.py
   import pdoc
   import json

   def generate_api_docs():
       # Generate docs for cogency package
       modules = ['cogency.agent', 'cogency.llm', 'cogency.tools']
       for module in modules:
           doc = pdoc.doc.Module(pdoc.import_module(module))
           # Convert to JSON/markdown for Astro consumption
   ```

3. **GitHub Actions Integration**
   ```yaml
   # .github/workflows/docs.yml
   name: Generate Documentation
   on:
     push:
       paths: ["cogency/**/*.py"]
   jobs:
     docs:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Generate docs
           run: python scripts/generate_docs.py
         - name: Trigger site rebuild
           # Webhook to rebuild Astro site
   ```

### Content Coherence Issues Identified

**Critical**: The landing site currently contains theoretical examples that may not match actual OSS implementation:

1. **API Verification Needed**:
   - `cogency.tools.CalculatorTool` - verify this class exists
   - `cogency.agent.Agent` constructor signature
   - `agent.stream()` method availability
   - `cogency.nodes.reason` import paths

2. **Example Code Accuracy**:
   - All code examples are placeholder/theoretical
   - Need real working examples from OSS repo
   - Method calls and imports should match actual API

3. **Feature Claims vs Reality**:
   - Site claims 6 core features - verify against actual capabilities
   - Streaming implementation details
   - Auto-discovery mechanism specifics

### Next Steps (Priority Order)

1. **FIRST**: Audit content accuracy against actual OSS codebase
2. Choose documentation tool (recommend pdoc for simplicity)
3. Audit current docstring coverage in OSS project
4. Implement doc generation script
5. Set up automated pipeline
6. Create Astro dynamic pages for consumption

### Immediate Action Items for OSS Project

1. **Content Audit**:
   ```bash
   # In oss/cogency, verify these exist:
   grep -r "class Agent" .
   grep -r "CalculatorTool" .
   grep -r "def stream" .
   find . -name "*.py" -path "*/tools/*"
   ```

2. **Real Examples**:
   - Move working examples from any `/examples/` folder to sync with site
   - Ensure examples in docs actually run against current codebase
   - Test import paths match what's documented on site

---

## Additional Marketing Site Recommendations

### Examples Gallery

Create `/examples/` section showcasing:

- Basic agent setup
- Custom tool development
- Streaming implementations
- Production deployment patterns
- Integration examples (FastAPI, Discord bots, etc.)

### Performance Monitoring

Consider adding:

- Analytics for popular documentation pages
- Search functionality across docs
- User feedback on documentation quality

### Community Features

- GitHub stars/contributors display
- Community examples submission
- Discord/community links integration
