from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.config import PROJECTS
from ..services.ssh import ssh_tmux_send


async def run_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/run <project> [custom command]"""
    args = context.args or []
    if not args:
        await update.message.reply_text("Usage: `/run <project> [command]`", parse_mode="Markdown")
        return

    name = args[0]
    if name not in PROJECTS:
        await update.message.reply_text(f"Unknown project. Available: {', '.join(PROJECTS)}")
        return

    proj = PROJECTS[name]
    custom_cmd = " ".join(args[1:]) if len(args) > 1 else proj["train_cmd"]
    full_cmd = f"conda activate {proj['conda']} && cd {proj['path']} && {custom_cmd}"

    result = await ssh_tmux_send(proj["remote"], proj["tmux"], full_cmd)
    await update.message.reply_text(
        f"Sent to *{name}* (`{proj['tmux']}`):\n`{custom_cmd}`\n\nUse `/logs {name}` to monitor.",
        parse_mode="Markdown",
    )


handler = CommandHandler("run", run_handler)
