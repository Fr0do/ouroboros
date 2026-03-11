# CLAUDE.md — Ouroboros (Meta-Project)

## What Is This
Root governance project for all of Max's research. Contains:
- **OUROBOROS.md** — research meta-protocol (project registry, workflow, principles)
- **bot/** — Telegram control panel for autonomous agent oversight

## Environment
- Local macOS: SSH access to kurkin-1, kurkin-4
- Secrets in .env (TELEGRAM_TOKEN)
- Python deps: python-telegram-bot, python-dotenv

## Model Strategy — Hard Budget Enforcement

**Daily budget**: $20 hard cap. Opus is 30× Haiku, 5× Sonnet — treat every Opus token as premium.

### Opus (the "brain") — ONLY for:
- Architecture decisions, debugging strategy, complex reasoning
- Planning multi-step tasks (then HAND OFF implementation immediately)
- Code review requiring full-project context
- Conversations where transferring context to a subagent costs more than doing it

### Sonnet — THE DEFAULT for all implementation
- **Any code writing or editing** (not just >50 lines — ALL implementation)
- Refactoring, renaming, reformatting, boilerplate
- Tests, docstrings, documentation, config files
- Shell scripts, CI/CD, deployment configs
- **Rule**: Sonnet is the default. Opus implements ONLY <10 line hotfixes.

### Haiku — maximize usage for lightweight work
- All exploration: file search, codebase navigation, grep-and-summarize
- Summarizing files, command output, or search results
- Rote transformations, format conversions
- Reading and reporting on file contents

### Hard Enforcement Rules
1. **Before writing ANY code in Opus**: ask "can a Sonnet subagent do this?" — if yes, delegate
2. **>10 lines of code in Opus = violation** — unless context transfer is provably more expensive
3. **Always use `model: "sonnet"` on Agent tool** for implementation work
4. **Always use `model: "haiku"` on Agent tool** for exploration/search/summary
5. **Session cost check**: run `rtk gain` at start of every session and after heavy operations
6. **If daily spend exceeds $15**: switch to Sonnet-only mode for remaining work, Opus for planning only

## Token Economy

### RTK v0.28.2 (Rust Token Killer)
Active via Claude Code hook — all shell ops auto-proxied (target: 75%+ savings).
- `rtk gain` — check savings dashboard (run at session start + periodically)
- `rtk gain --history` — command-level breakdown
- `rtk discover` — find missed optimization opportunities (run weekly)

### Context Window Discipline
- **Don't read files you won't use** — glob/grep first, read only what's needed
- **Don't re-read files** already in context unless they changed
- **Prefer targeted reads** (offset+limit) over full-file reads for large files
- **Use Explore agents (Haiku)** for broad searches — they don't bloat main context
- **Summarize, don't paste** — when reporting findings, distill; don't dump raw output
- **Batch parallel tool calls** — never make sequential calls that could run in parallel

### Spending Protocol
1. **Session start**: run `rtk gain`, note baseline
2. **Every ~30 min of active work**: mental check — am I delegating enough?
3. **After heavy operations** (multi-file edits, large searches): run `rtk gain`
4. **End of session**: compare savings, note if delegation ratio was healthy
5. **Red flag**: if Opus has written >100 lines of code in a session, something went wrong

## Key Files
| File | Purpose |
|---|---|
| OUROBOROS.md | Global research governance — read first |
| .env | Secrets (gitignored) |
| bot/main.py | Telegram bot entry point |
| bot/services/tg.py | Shared Telegram helpers (send_long, require_project) |
| bot/services/ssh.py | SSH/tmux/GPU operations |
| scripts/auto-dev.sh | Autonomous feature implementation agent |

## Issue Journaling
- **ALWAYS create an issue FIRST** — before writing any code for a feature or non-trivial fix. No exceptions. Even if the user doesn't ask, create the issue, then implement. If you forget, create one retroactively and reference it.
- **Comment progress** on issues: what was done, blockers hit, commit hashes
- **Reference in commits**: `fixes #N` to auto-close, or mention `#N` if work continues
- **Triage at session start**: check `gh issue list --repo Fr0do/ouroboros --state open`

## Feature Dispatch (auto-dev)
- A `UserPromptSubmit` hook (`.claude/hooks/check-auto-dev.sh`) checks for `auto-dev` labeled issues
- If you see "AUTO-DEV" in hook output, pick up the issue immediately
- Comment "Picked up" on the issue to claim it (prevents other agents from duplicating work)
- Implement, commit with `fixes #N`, the label is removed when the issue closes
- See OUROBOROS.md "Feature Dispatch" for full protocol

## Secrets & env.example
- **Never** echo, print, or write actual secrets (tokens, keys, passwords) to files, terminal, or commits
- Every repo that uses `.env` must have an `env.example` with keys only (no values), committed to git
- When adding a new env var: update `env.example` in the same commit
- `.env` is always gitignored; `env.example` is always tracked

## Git Hygiene
- **Bamboo structure**: keep a linear commit history on main — rebase, don't merge
- **No long-lived branches**: work is atomic or stashable; delete branches after merge
- **Rebase frequently**: `git pull --rebase` before pushing; resolve conflicts inline
- **Stash over branch**: for WIP, prefer `git stash` over creating throwaway branches

## Commit Conventions
- Prefix: `[feat]`, `[fix]`, `[doc]`, `[infra]`, `[bot]`, `[s_cot]`
- Include a summary of major edits in commit messages (not just what changed in this repo)
- For remote-only changes (e.g. s_cot training code uploaded via scp), document them in the commit body
- Format: short title line, blank line, bullet list of all significant changes including remote/subproject work
- Always note which subproject was affected and what was changed conceptually

## Subprojects (see OUROBOROS.md for full map)
- s_cot → ~/experiments/s_cot_tex + kurkin-1:/workspace-SR004.nfs2/kurkin/s_cot
- mmred → ~/experiments/mmred + kurkin-1:/workspace-SR004.nfs2/kurkin/mmred
- bbbo → kurkin-1:/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer
