import asyncio
import sys
import os
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler


from ..services.tg import authorized


@authorized
async def update_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/update — git pull and restart the bot."""
    repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    proc = await asyncio.create_subprocess_exec(
        "git", "pull", "--ff-only", "origin", "main",
        cwd=repo_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    out = stdout.decode().strip()

    if "Already up to date" in out:
        await update.message.reply_text("Already up to date.")
        return

    if proc.returncode != 0:
        err = stderr.decode().strip()[:3000]
        await update.message.reply_text(f"Pull failed:\n```\n{err}\n```", parse_mode="Markdown")
        return

    # Truncate to just the summary (file list can be huge)
    summary = out[:2000] if len(out) > 2000 else out
    await update.message.reply_text(f"Pulled:\n```\n{summary}\n```\nRestarting...", parse_mode="Markdown")

    # Re-exec the bot process to pick up new code
    os.execv(sys.executable, [sys.executable, "-m", "bot"])


handler = CommandHandler("update", update_handler)
