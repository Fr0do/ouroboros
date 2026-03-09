# Team — Multi-Agent Orchestration

Lightweight file-based coordination for parallel Claude Code terminals.

## How it works

```
User (Telegram / CLI)
  │
  ▼
Leader (terminal 0)          ← reads OUROBOROS.md, plans work, writes tasks
  ├── Worker 1 (terminal 1)  ← picks up task, works, writes result
  ├── Worker 2 (terminal 2)
  └── Worker N (terminal N)
```

- **Leader** decomposes work into task files in `team/tasks/`
- **Workers** claim tasks, execute, write results to `team/results/`
- **Sync** happens through the filesystem — no server, no sockets
- **Telegram bot** provides oversight via `/team` command

## Task lifecycle

```
pending → claimed → done | failed
```

## Files

| Path | Purpose |
|---|---|
| `team/config.yaml` | Team size, roles, project assignments |
| `team/tasks/*.yaml` | Task queue (one file per task) |
| `team/results/*.md` | Completed work artifacts |
| `team/LEADER.md` | Instructions for the leader terminal |
| `team/WORKER.md` | Instructions for worker terminals |
