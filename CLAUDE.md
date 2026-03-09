# CLAUDE.md — Ouroboros (Meta-Project)

## What Is This
Root governance project for all of Max's research. Contains:
- **OUROBOROS.md** — research meta-protocol (project registry, workflow, principles)
- **PLAN.md** — executable agent plan (run this phase by phase)
- **bot/** — Telegram control panel for autonomous agent oversight
- **notion_bootstrap.py** — Notion workspace initializer
- **notion_client_lib.py** — shared Notion helpers

## Quick Start
```bash
# First run:
cat PLAN.md  # read the full plan
# Then execute Phase 0 → Phase 1 → ... sequentially
```

## Environment
- Local macOS: SSH access to kurkin-1, kurkin-4
- Secrets in .env (TELEGRAM_TOKEN, NOTION_SECRET)
- Python deps: python-telegram-bot, notion-client, python-dotenv

## Model Strategy
- **Plan with Opus, implement with Sonnet**: For non-trivial tasks, use Opus for planning/architecture, then delegate implementation to Sonnet subagents (cheaper, faster for code writing)
- If Opus rate limits are not a concern, Opus implementation is fine
- Heavy code generation, refactoring, and boilerplate → prefer Sonnet subagents
- Design decisions, debugging strategy, complex reasoning → keep in Opus

## RTK
Active via Claude Code hook. All shell ops auto-optimized.

## Key Files
| File | Purpose |
|---|---|
| OUROBOROS.md | Global research governance — read first |
| PLAN.md | Step-by-step agent execution plan |
| .env | Secrets (gitignored) |
| bot/main.py | Telegram bot entry point |
| notion_bootstrap.py | One-time Notion workspace setup |
| notion_client_lib.py | Shared Notion API helpers |
| notion_pages.json | Auto-generated page ID mapping |

## Commit Conventions
- Include a summary of major edits in commit messages (not just what changed in this repo)
- For remote-only changes (e.g. s_cot training code uploaded via scp), document them in the commit body
- Format: short title line, blank line, bullet list of all significant changes including remote/subproject work
- Always note which subproject was affected and what was changed conceptually

## Subprojects (see OUROBOROS.md for full map)
- s_cot → ~/experiments/s_cot_tex + kurkin-1:/workspace-SR004.nfs2/kurkin/s_cot
- long-vqa → ~/experiments/long-vqa + kurkin-1:/workspace-SR004.nfs2/kurkin/long-vqa
- bbbo → kurkin-1:/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer
