# PLAN.md — Claude Code Agent Execution Plan

> Run this from `~/experiments/ouroboros` with: `claude --resume` or `claude "execute PLAN.md"`
> Env: local macOS terminal with SSH access to kurkin-1/kurkin-4

---

## Phase 0: Self-Setup

```
0.1  Read OUROBOROS.md — understand the full project graph
0.2  Read ~/.claude/RTK.md — confirm rtk is working (`rtk --version`, `rtk gain`)
0.3  Verify SSH: `ssh kurkin-1 "echo ok && hostname"`
0.4  Verify SSH: `ssh kurkin-4 "echo ok && hostname"`
0.5  Create ~/experiments/ouroboros/.env with:
       TELEGRAM_TOKEN=<from .env>
       NOTION_SECRET=<from .env>
       NOTION_INTEGRATION_ID=<from .env>
0.6  git init ~/experiments/ouroboros (if not already a repo)
0.7  Create .gitignore: .env, __pycache__, *.pyc, .DS_Store, node_modules/
```

---

## Phase 1: Deploy CLAUDE.md Files to Remotes

```
1.1  scp ~/experiments/s_cot_tex/s_cot/CLAUDE.md kurkin-1:/workspace-SR004.nfs2/kurkin/s_cot/CLAUDE.md
1.2  scp ~/experiments/bbbo_GeneralOptimizer_CLAUDE.md kurkin-1:/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer/CLAUDE.md
1.3  SSH to kurkin-1 and verify both files landed:
       ssh kurkin-1 "cat /workspace-SR004.nfs2/kurkin/s_cot/CLAUDE.md | head -5"
       ssh kurkin-1 "cat /workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer/CLAUDE.md | head -5"
1.4  Create CLAUDE.md for long-vqa remote (copy from local):
       scp ~/experiments/long-vqa/CLAUDE.md kurkin-1:/workspace-SR004.nfs2/kurkin/long-vqa/CLAUDE.md
1.5  Verify NFS visibility from kurkin-4:
       ssh kurkin-4 "cat /workspace-SR004.nfs2/kurkin/s_cot/CLAUDE.md | head -3"
```

---

## Phase 2: Notion Workspace Bootstrap

```
2.1  pip install notion-client --break-system-packages (or use uv)
2.2  Write ~/experiments/ouroboros/notion_bootstrap.py:
       - Load .env (NOTION_SECRET)
       - Connect to Notion API (notion_client.Client)
       - Search for existing pages: client.search(query="Ouroboros")
       - If no root page found:
           a. Create root page "Ouroboros" in the connected workspace
           b. Create child pages: "Research Timeline", "s_cot", "long-vqa (MMReD)", "bbbo", "Ideas & Backlog", "Infrastructure"
       - Print created page IDs
       - Save page ID mapping to ~/experiments/ouroboros/notion_pages.json
2.3  Run notion_bootstrap.py, verify pages created
2.4  Write ~/experiments/ouroboros/notion_client_lib.py:
       - Helper functions: log_experiment(project, config, metrics), add_note(project, text), get_timeline()
       - Used by Telegram bot and future autonomous agents
2.5  Test: call log_experiment("s_cot", {"model": "test"}, {"acc": 0.5}) and verify page updated
```

---

## Phase 3: Telegram Bot — Antigravity Control Panel

```
3.1  pip install python-telegram-bot notion-client python-dotenv --break-system-packages
3.2  Create ~/experiments/ouroboros/bot/ directory structure:
       bot/
       ├── __init__.py
       ├── main.py              # Entry point, Application setup
       ├── handlers/
       │   ├── __init__.py
       │   ├── status.py        # /status — show all project states
       │   ├── run.py           # /run <project> <cmd> — execute on remote via SSH
       │   ├── stop.py          # /stop <project> — kill tmux session on remote
       │   ├── logs.py          # /logs <project> [n] — tail remote tmux/ClearML logs
       │   ├── note.py          # /note <project> <text> — push note to Notion
       │   ├── task.py          # /task <description> — add to Notion backlog
       │   └── sync.py          # /sync <project> — scp results from remote to local
       ├── services/
       │   ├── __init__.py
       │   ├── ssh.py           # SSH command executor (asyncio subprocess)
       │   ├── notion.py        # Notion API wrapper (from notion_client_lib.py)
       │   └── config.py        # Load .env, project registry
       └── requirements.txt

3.3  Implement bot/services/config.py:
       - Load .env for tokens
       - Project registry dict:
           PROJECTS = {
             "s_cot": {"remote": "kurkin-1", "path": "/workspace-SR004.nfs2/kurkin/s_cot", "tmux": "cot", "conda": "kurkin_313_torch"},
             "long-vqa": {"remote": "kurkin-1", "path": "/workspace-SR004.nfs2/kurkin/long-vqa", "tmux": "vqa", "conda": "kurkin_313_torch"},
             "bbbo": {"remote": "kurkin-1", "path": "/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer", "tmux": "bbbo", "conda": "kurkin_313_torch"},
           }
       - AUTHORIZED_USERS = [<Max's Telegram user ID>]  # get via /start command first run

3.4  Implement bot/services/ssh.py:
       - async def ssh_exec(host: str, command: str, timeout: int = 30) -> str
       - Uses asyncio.create_subprocess_exec("ssh", host, command)
       - Returns stdout, handles timeout/errors gracefully
       - async def ssh_tmux_send(host: str, session: str, command: str) -> str
       - Sends keys to tmux session: ssh host "tmux send-keys -t {session} '{command}' Enter"

3.5  Implement handlers:

     /status:
       - For each project in registry: ssh_exec(remote, f"tmux has-session -t {tmux} 2>&1 && echo RUNNING || echo STOPPED")
       - Also check: ssh_exec(remote, f"nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader | head -1")
       - Format as compact message: project | status | GPU%

     /run <project> [cmd]:
       - If cmd given: ssh_tmux_send(remote, tmux, f"conda activate {conda} && cd {path} && {cmd}")
       - If no cmd: ssh_tmux_send(remote, tmux, f"conda activate {conda} && cd {path} && bash train.sh")
       - Reply: "Sent to {project}. Use /logs {project} to monitor."

     /stop <project>:
       - ssh_exec(remote, f"tmux send-keys -t {tmux} C-c")
       - Reply: "Sent Ctrl-C to {project}/{tmux}"

     /logs <project> [n=20]:
       - ssh_exec(remote, f"tmux capture-pane -t {tmux} -p | tail -{n}")
       - Return last n lines as code block

     /note <project> <text>:
       - Call notion.add_note(project, text)
       - Reply: "Logged to Notion: {project}"

     /task <text>:
       - Call notion.add_to_backlog(text)
       - Reply: "Added to backlog"

     /sync <project>:
       - Run scp from remote to local for known result paths
       - Reply with file list transferred

3.6  Implement bot/main.py:
       - python-telegram-bot v20+ (async)
       - Register all handlers
       - Add auth middleware: check message.from_user.id in AUTHORIZED_USERS
       - Run with application.run_polling()

3.7  Test bot locally:
       - python -m bot.main
       - Send /start from Telegram to get user ID, add to AUTHORIZED_USERS
       - Test /status, /logs s_cot, /note s_cot "test note"

3.8  Create systemd user service or tmux session for bot persistence:
       - tmux new -d -s ouroboros "cd ~/experiments/ouroboros && python -m bot.main"

3.9  Commit everything: git add -A && git commit -m "ouroboros v0.1: telegram bot + notion integration"
```

---

## Phase 4: Continue s_cot Autonomous Work

```
4.1  SSH to kurkin-1
4.2  cd /workspace-SR004.nfs2/kurkin/s_cot
4.3  Read CLAUDE.md (just deployed)
4.4  conda activate kurkin_313_torch
4.5  Check current state:
       - tmux ls (any existing sessions?)
       - ls spectral-r1-checkpoints/ (any completed runs?)
       - git log --oneline -10
4.6  If no active training:
       - Review train.sh config (model size, spectral_beta, lr)
       - Start training: bash train.sh
       - Monitor first 100 steps for loss convergence
4.7  While training:
       - Review paper sections in ~/experiments/s_cot_tex/sections/
       - Check if results tables need updating
       - Run gen_viz.py to refresh figures if new data available
4.8  Log status to Notion via:
       python -c "
       from notion_client import Client
       import os, json
       # ... quick status update to s_cot page
       "
       OR via Telegram: send message to bot with /note s_cot "Training started: 7B, beta=0.1, lr=5e-5"
```

---

## Phase 5: Harden & Iterate

```
5.1  Add error handling to Telegram bot (retry SSH, timeout messages)
5.2  Add /gpu command: show nvidia-smi from all remotes
5.3  Add /clearml command: query ClearML API for latest experiment metrics
5.4  Add scheduled Notion updates (daily summary of all project states)
5.5  Update OUROBOROS.md with any new conventions discovered during execution
5.6  Consider: cron job or launchd agent to auto-restart bot on reboot
```

---

## Execution Notes for Claude Code Agent

- **Always read CLAUDE.md** in any project before touching it
- **RTK is active** — your shell commands are already optimized
- **Commit early, commit often** — working state before experiments
- **Notion is the memory** — if it's not logged, it didn't happen
- **Telegram is the nerve** — fast status, fast control
- **NFS is shared** — changes on kurkin-1 are visible on kurkin-4 immediately
- **If blocked**: log the blocker to Notion + send Telegram message, move to next task

---

## Quick Start (copy-paste into Claude Code)

```
Read ~/experiments/ouroboros/PLAN.md and execute it phase by phase.
Start with Phase 0, verify everything works, then proceed.
Skip any step that's already done. Log progress to Notion after each phase.
```
