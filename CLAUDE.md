<!-- GSD:project-start source:PROJECT.md -->
## Project

**OOD Agent**

Ein RAG-basierter Assistent für ServiceNow-Tickets, der eingehende Fehlerbeschreibungen gegen eine kuratierte Wissensbasis aus Wiki-Exporten, ServiceNow-Fällen, Jira-Bugs und Markdown-Notizen durchsucht und konkrete Lösungswege vorschlägt. Der Agent hilft, wiederkehrende Incidents schneller zu triagieren und zu lösen.

**Core Value:** Operative Tickets werden durch intelligente Suche über verteilte Wissensquellen schneller gelöst – mit konkreten Handlungsempfehlungen, Quellenbelegen und Routing-Logik.

### Constraints

- **Tech Stack**: Python, LightRAG, Cloud-LLM (nach Datenschutzfreigabe) — Markdown bleibt kanonisches Format
- **Data Privacy**: Ticketinhalte dürfen nur an Cloud-LLM gesendet werden, wenn Datenschutzfreigabe vorliegt
- **Security**: Secrets ausschließlich über `.env`, nie in Markdown-Quellen oder Commits
- **Deployment**: MVP läuft lokal, spätere Deployment-Entscheidung (Proxmox/Hetzner/Vercel)
- **Knowledge Format**: Markdown-Dateien mit YAML-Frontmatter als kanonische Wissenseinheit
<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->
## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
