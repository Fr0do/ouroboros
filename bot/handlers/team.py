"""Handler for /team — multi-agent task queue management."""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.team import load_tasks, load_task, save_task, task_summary_line, format_task_detail
from ..services.tg import send_long


async def team_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/team [id|reset <id>] — view task queue or task details."""
    args = context.args or []

    # /team — list all tasks
    if not args:
        tasks = load_tasks()
        if not tasks:
            await update.message.reply_text("No tasks in queue. Leader hasn't dispatched yet.")
            return

        by_status = {"pending": [], "claimed": [], "done": [], "failed": []}
        for t in tasks:
            by_status.get(t.get("status", ""), by_status["pending"]).append(t)

        lines = ["*Team Task Queue*\n"]
        for status in ("claimed", "pending", "failed", "done"):
            group = by_status[status]
            if group:
                lines.append(f"*{status.upper()}* ({len(group)})")
                for t in group:
                    lines.append(task_summary_line(t))
                lines.append("")

        total = len(tasks)
        done = len(by_status["done"])
        lines.append(f"_{done}/{total} complete_")
        await send_long(update, "\n".join(lines), parse_mode="Markdown")
        return

    # /team reset <id> — reset task to pending
    if args[0] == "reset" and len(args) > 1:
        task = load_task(args[1])
        if not task:
            await update.message.reply_text(f"Task `{args[1]}` not found.", parse_mode="Markdown")
            return
        task["status"] = "pending"
        task["claimed_by"] = None
        task["completed"] = None
        task["result_file"] = None
        save_task(task)
        await update.message.reply_text(f"Task `{args[1]}` reset to pending.", parse_mode="Markdown")
        return

    # /team <id> — show task details
    task = load_task(args[0])
    if not task:
        await update.message.reply_text(f"Task `{args[0]}` not found.", parse_mode="Markdown")
        return
    await send_long(update, format_task_detail(task), parse_mode="Markdown")


handler = CommandHandler("team", team_handler)
