from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.config import PROJECTS
from ..services.ssh import ssh_tmux_capture


async def logs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/logs <project> [n=20] — tail last n lines from tmux."""
    args = context.args or []
    if not args:
        await update.message.reply_text("Usage: `/logs <project> [lines]`", parse_mode="Markdown")
        return

    name = args[0]
    if name not in PROJECTS:
        await update.message.reply_text(f"Unknown project. Available: {', '.join(PROJECTS)}")
        return

    n = int(args[1]) if len(args) > 1 else 20
    proj = PROJECTS[name]
    output = await ssh_tmux_capture(proj["remote"], proj["tmux"], lines=n)

    # Telegram message limit is 4096 chars
    if len(output) > 3900:
        output = output[-3900:]

    await update.message.reply_text(f"*{name}* logs:\n```\n{output}\n```", parse_mode="Markdown")


handler = CommandHandler("logs", logs_handler)
