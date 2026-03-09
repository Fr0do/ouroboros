from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.config import PROJECTS
from ..services.ssh import ssh_tmux_capture
from ..services.tg import require_project


async def logs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/logs <project> [n=20] — tail last n lines from tmux."""
    name, err = require_project(context.args or [], "/logs <project> [lines]")
    if err:
        await update.message.reply_text(err, parse_mode="Markdown")
        return

    n = int(context.args[1]) if len(context.args) > 1 else 20
    proj = PROJECTS[name]
    output = await ssh_tmux_capture(proj["remote"], proj["tmux"], lines=n)

    if len(output) > 3900:
        output = output[-3900:]

    await update.message.reply_text(f"*{name}* logs:\n```\n{output}\n```", parse_mode="Markdown")


handler = CommandHandler("logs", logs_handler)
