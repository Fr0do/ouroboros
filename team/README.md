# Team — Multi-Agent Coordination

Native Claude Code agent teams are the primary method for multi-agent work.

Docs: https://code.claude.com/docs/en/agent-teams

## Filesystem fallback

When native agent teams are unavailable (e.g. offline, SSH-only environments),
the file-based task queue in `team/tasks/` can still be used:

- Write task YAML files to `team/tasks/` (one per task)
- Workers claim tasks, execute, write results to `team/results/`
- Lifecycle: `pending -> claimed -> done | failed`

This is a fallback — prefer native teams when possible.

## Directory layout

| Path | Purpose |
|---|---|
| `team/tasks/*.yaml` | File-based task queue (fallback) |
| `team/results/*.md` | Completed work artifacts |
