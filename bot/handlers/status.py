from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.config import PROJECTS
from ..services.ssh import ssh_exec, gpu_status


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show status of all projects: tmux session + GPU."""
    lines = ["*OuroSSS Status*\n"]

    for name, proj in PROJECTS.items():
        host = proj["remote"]
        tmux = proj["tmux"]

        # Check tmux
        check = await ssh_exec(host, f"tmux has-session -t {tmux} 2>&1 && echo RUNNING || echo STOPPED", timeout=10)
        status_emoji = "🟢" if "RUNNING" in check else "🔴"
        lines.append(f"{status_emoji} *{name}* — `{check.strip()}`")

    # GPU status (once per unique host)
    hosts_seen = set()
    for proj in PROJECTS.values():
        h = proj["remote"]
        if h not in hosts_seen:
            hosts_seen.add(h)
            gpu = await gpu_status(h)
            lines.append(f"\n*GPU ({h})*:\n```\n{gpu}\n```")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


handler = CommandHandler("status", status_handler)
