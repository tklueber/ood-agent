# Phase 1: Foundation & CLI - Context

**Gathered:** 2026-05-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Python project setup, CLI scaffolding, and configuration management. This phase delivers the minimal project structure and CLI boilerplate that enables Phase 2 to implement actual RAG functionality.

**In scope:** Dependency management, project structure, CLI entry points, configuration loading, stub command implementations.

**Out of scope:** LightRAG integration, actual query/index logic, RAG implementation. Those are Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Package Management
- **D-01:** Use uv as package manager (modern, fast, single binary)
- **D-02:** Python 3.10+ minimum version

### Project Layout
- **D-03:** src/ layout — code in src/ood/
- **D-04:** Full directory structure upfront:
  - `src/ood/` — main package code
  - `docs/` — documentation
  - `tests/` — test suite
  - `scripts/` — utility scripts
  - `examples/` — usage examples
  - `knowledge/` — Markdown knowledge base (default, configurable)
  - `data/` — persistent index data (default, configurable, gitignored)

### CLI Framework
- **D-05:** Typer as CLI framework (type-hint based, excellent error messages)
- **D-06:** Flat command structure: `ood index`, `ood query`, `ood update`, `ood reindex`
- **D-07:** CLI entry point defined in pyproject.toml [project.scripts]
- **D-08:** Auto-generated help text (Typer default)

### Configuration
- **D-09:** All paths configurable with sensible defaults:
  - Default `knowledge/` at project root, user can override via config
  - Default `data/` at project root, user can override via config
  - Default `storage/` inside data/, user can override via config
- **D-10:** .env file for secrets (Cloud LLM credentials), never committed
- **D-11:** Config precedence: CLI args > environment vars > config file > defaults

### CLI Output
- **D-12:** Human-friendly output by default, `--json` flag for machine parsing
- **D-13:** Auto-detect terminal capabilities for color support
- **D-14:** Three verbosity levels: normal (default), `-v` (verbose), `-q` (quiet)
- **D-15:** User-friendly error messages by default, full traceback with `-v`

### Command Stubs
- **D-16:** Phase 1 provides stub implementations that:
  - Accept correct arguments
  - Validate configuration
  - Print placeholder output
  - Return appropriate exit codes
  - Phase 2 will replace stubs with actual RAG logic

### the agent's Discretion
- Exact pyproject.toml structure and metadata
- Specific .gitignore entries beyond data/
- Logging library choice (loguru vs stdlib logging)
- Development tool configuration (ruff, mypy, pytest)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements are fully captured in decisions above and in REQUIREMENTS.md:
- INF-05: System persists index data outside git repository
- INF-06: Configuration managed via .env file (Cloud LLM credentials)
- INF-07: System uses Python 3.10+ with uv or poetry for dependency management

</canonical_refs>

<code_context>
## Existing Code Insights

### Greenfield Project
This is a brand-new project with no existing code. No reusable assets, no established patterns, no integration points.

### Key Constraints from PROJECT.md
- Python-based CLI and API
- Markdown as primary knowledge format
- Secrets exclusively via .env
- CLI-first approach (Web UI deferred to v2)

</code_context>

<specifics>
## Specific Ideas

- CLI should feel professional and polished from day one (Typer + rich output)
- All paths configurable so developers can adapt to their environment
- Clear separation between stub implementations (Phase 1) and real logic (Phase 2+)
- User-friendly defaults: works out of the box without configuration for local testing

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-foundation-cli*
*Context gathered: 2026-05-01*
