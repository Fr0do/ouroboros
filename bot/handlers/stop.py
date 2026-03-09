from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.config import PROJECTS
from ..services.ssh import ssh_exec


async def stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stop <project> — send Ctrl-C to project's tmux session."""
    args = context.args or []
    if not args:
        await update.message.reply_text("Usage: `/stop <project>`", parse_mode="Markdown")
        return

    name = args[0]
    if name not in PROJECTS:
        await update.message.reply_text(f"Unknown project. Available: {', '.join(PROJECTS)}")
        return

    proj = PROJECTS[name]
    await ssh_exec(proj["remote"], f"tmux send-keys -t {proj['tmux']} C-c")
    await update.message.reply_text(f"Sent `Ctrl-C` to *{name}* (`{proj['tmux']}`)", parse_mode="Markdown")


handler = CommandHandler("stop", stop_handler)
