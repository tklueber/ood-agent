# Phase 1: Foundation & CLI - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-01
**Phase:** 01-foundation-cli
**Areas discussed:** Project structure, CLI framework, CLI output style

---

## Project Structure

| Option | Description | Selected |
|--------|-------------|----------|
| uv (Recommended) | Modern, fast, single binary - growing adoption for 2025+ projects | ✓ |
| poetry | Mature, widely used, extensive plugin ecosystem | |
| pip classic | pip + requirements.txt | |
| You decide | Your call | |

**User's choice:** uv (Recommended)
**Notes:** Modern tooling preferred for greenfield project

---

| Option | Description | Selected |
|--------|-------------|----------|
| src/ layout (Recommended) | Package code in src/ood/, cleaner separation, standard for libraries | ✓ |
| Flat layout | ood/ at project root, simpler for single-package apps | |
| You decide | Your call | |

**User's choice:** src/ layout (Recommended)
**Notes:** Cleaner separation between source and other files

---

| Option | Description | Selected |
|--------|-------------|----------|
| Entry point in pyproject.toml (Recommended) | pyproject.toml [project.scripts] ood = "ood.cli:main" | ✓ |
| Standalone script | Separate ood script in bin/ or scripts/ | |
| You decide | Your call | |

**User's choice:** Entry point in pyproject.toml (Recommended)
**Notes:** Standard uv/poetry pattern

---

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal (Recommended) | Flatter structure, put tests and docs at top level | |
| Full structure | Add docs/, tests/, scripts/, examples/ upfront | ✓ |
| You decide | Your call | |

**User's choice:** Full structure
**Notes:** User prefers complete structure from the start

---

| Option | Description | Selected |
|--------|-------------|----------|
| data/ at root (Recommended) | Keep it at project root as documented in PROJECT.md | |
| User data directory | ~/.ood-agent/ or XDG data dir for multi-user systems | |
| You decide | Your call | |

**User's choice:** Custom (user-configurable with fallback)
**Notes:** Standard folder as fallback, but user-definable via configuration

---

| Option | Description | Selected |
|--------|-------------|----------|
| At root (Recommended) | Project root - simple, visible, easy to find | |
| Nested location | Inside src/ or data/ - cleaner separation | |
| You decide | Your call | |

**User's choice:** Custom (user-configurable with fallback)
**Notes:** User-definable but with default folder fallback

---

## CLI Framework

| Option | Description | Selected |
|--------|-------------|----------|
| Typer (Recommended) | Modern, type-hint based, excellent error messages, less boilerplate | ✓ |
| Click | Mature, explicit, more verbose but very flexible | |
| argparse | Stdlib, no dependencies, more manual work | |
| You decide | Your call | |

**User's choice:** Typer (Recommended)
**Notes:** Modern approach with better DX

---

| Option | Description | Selected |
|--------|-------------|----------|
| Flat commands (Recommended) | ood index, ood query, ood update, ood reindex - clean | ✓ |
| Grouped commands | ood knowledge index, ood knowledge query - grouped | |
| You decide | Your call | |

**User's choice:** Flat commands (Recommended)
**Notes:** Simpler command structure for CLI tool

---

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-generated (Recommended) | Concise docstrings, auto-generated help - Typer default | ✓ |
| Rich help | Rich formatted help with examples and usage patterns | |
| You decide | Your call | |

**User's choice:** Auto-generated (Recommended)
**Notes:** Typer default is sufficient

---

## CLI Output Style

| Option | Description | Selected |
|--------|-------------|----------|
| Smart default (Recommended) | Human-friendly output by default, JSON with --json flag | ✓ |
| JSON only | Always JSON for machine parsing | |
| Plain text | Plain text, no formatting | |
| You decide | Your call | |

**User's choice:** Smart default (Recommended)
**Notes:** Flexible output for both human and machine consumption

---

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-detect (Recommended) | Auto-detect terminal support, colorize when available | ✓ |
| Always colored | Always use colors | |
| Never colored | Never use colors | |
| You decide | Your call | |

**User's choice:** Auto-detect (Recommended)
**Notes:** Respect terminal capabilities

---

| Option | Description | Selected |
|--------|-------------|----------|
| Three levels (Recommended) | Normal output by default, -v for verbose, -q for quiet | ✓ |
| Two levels | Minimal by default, -v to add more | |
| You decide | Your call | |

**User's choice:** Three levels (Recommended)
**Notes:** Standard CLI pattern

---

| Option | Description | Selected |
|--------|-------------|----------|
| Friendly (Recommended) | User-friendly errors, technical details with -v | ✓ |
| Full traceback | Always show full traceback | |
| You decide | Your call | |

**User's choice:** Friendly (Recommended)
**Notes:** Better UX for end users, developers can use -v flag

---

## the agent's Discretion

- Exact pyproject.toml structure and metadata
- Specific .gitignore entries beyond data/
- Logging library choice
- Development tool configuration

## Deferred Ideas

None — discussion stayed within phase scope
