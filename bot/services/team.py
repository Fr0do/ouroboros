"""Team task queue — filesystem-based multi-agent coordination."""
import yaml
from pathlib import Path

TEAM_DIR = Path(__file__).resolve().parent.parent.parent / "team"
TASKS_DIR = TEAM_DIR / "tasks"
RESULTS_DIR = TEAM_DIR / "results"


def load_tasks() -> list[dict]:
    """Load all task YAML files, sorted by id."""
    tasks = []
    for f in TASKS_DIR.glob("*.yaml"):
        if f.name == ".gitkeep":
            continue
        with open(f) as fh:
            task = yaml.safe_load(fh)
            if task:
                tasks.append(task)
    return sorted(tasks, key=lambda t: t.get("id", ""))


def load_task(task_id: str) -> dict | None:
    """Load a single task by ID."""
    path = TASKS_DIR / f"{task_id}.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        return yaml.safe_load(f)


def save_task(task: dict):
    """Write task dict back to YAML file."""
    path = TASKS_DIR / f"{task['id']}.yaml"
    with open(path, "w") as f:
        yaml.dump(task, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def task_summary_line(t: dict) -> str:
    """One-line summary: status icon + id + title."""
    icons = {"pending": "⏳", "claimed": "🔧", "done": "✅", "failed": "❌"}
    icon = icons.get(t.get("status", ""), "❓")
    tid = t.get("id", "?")
    title = t.get("title", "untitled")
    worker = ""
    if t.get("claimed_by"):
        worker = f" (w{t['claimed_by']})"
    return f"{icon} `{tid}` {title}{worker}"


def format_task_detail(t: dict) -> str:
    """Multi-line task detail for Telegram."""
    lines = [
        f"*Task {t['id']}*: {t['title']}",
        f"Status: {t['status']} | Priority: {t.get('priority', 'normal')}",
        f"Project: {t.get('project', '—')}",
    ]
    if t.get("assigned_to"):
        lines.append(f"Assigned to: worker {t['assigned_to']}")
    if t.get("claimed_by"):
        lines.append(f"Claimed by: worker {t['claimed_by']}")
    if t.get("depends_on"):
        lines.append(f"Depends on: {', '.join(t['depends_on'])}")
    if t.get("context"):
        ctx = t["context"].strip()
        if len(ctx) > 800:
            ctx = ctx[:800] + "…"
        lines.append(f"\n```\n{ctx}\n```")
    return "\n".join(lines)
