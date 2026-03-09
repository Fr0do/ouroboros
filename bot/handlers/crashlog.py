"""
/crashlog <project> [lines] — dump tmux scrollback for crash debugging.

Captures up to N screens of history (default 2000 lines), saves to a
timestamped file on remote, and sends the last portion via Telegram.
"""
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.config import PROJECTS
from ..services.ssh import ssh_tmux_dump, ssh_exec


def _extract_crash_context(text: str, tail: int = 150) -> str:
    """Extract the most useful portion: last N lines, prioritising tracebacks."""
    lines = text.splitlines()
    if not lines:
        return "(empty)"

    # Find the last traceback start
    tb_start = None
    for i in range(len(lines) - 1, -1, -1):
        if re.match(r"Traceback \(most recent call last\)", lines[i]):
            tb_start = i
            break

    if tb_start is not None:
        # Include some context before traceback + everything after
        start = max(0, tb_start - 20)
        context = lines[start:]
    else:
        # No traceback found — just take the tail
        context = lines[-tail:]

    return "\n".join(context)


async def crashlog_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/crashlog <project> [lines=2000] — dump tmux scrollback for debugging."""
    args = context.args or []
    if not args:
        await update.message.reply_text(
            "Usage: `/crashlog <project> [lines]`\n"
            "Dumps tmux scrollback, saves to file, sends crash context.",
            parse_mode="Markdown",
        )
        return

    name = args[0]
    if name not in PROJECTS:
        await update.message.reply_text(f"Unknown project. Available: {', '.join(PROJECTS)}")
        return

    history_lines = int(args[1]) if len(args) > 1 else 2000
    proj = PROJECTS[name]
    host = proj["remote"]
    session = proj["tmux"]

    await update.message.reply_text(f"Capturing {history_lines} lines from *{name}* tmux...", parse_mode="Markdown")

    # Save with timestamp
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"{proj['path']}/crashlogs/{ts}.log"

    text = await ssh_tmux_dump(host, session, history_lines=history_lines, save_path=save_path)

    if not text.strip():
        await update.message.reply_text(f"No output from tmux session `{session}`.", parse_mode="Markdown")
        return

    total_lines = len(text.splitlines())
    crash_context = _extract_crash_context(text)

    # Check if there's a traceback
    has_traceback = "Traceback (most recent call last)" in crash_context

    header = f"*{name}* crashlog — {total_lines} lines captured"
    if has_traceback:
        header += " (traceback found)"
    header += f"\nSaved: `{save_path}`"

    # Send in chunks if needed
    await update.message.reply_text(header, parse_mode="Markdown")

    # Send the crash context
    if len(crash_context) > 3900:
        # Split into multiple messages
        remaining = crash_context
        while remaining:
            chunk = remaining[:3900]
            if len(remaining) > 3900:
                nl = chunk.rfind("\n")
                if nl > 2000:
                    chunk = remaining[:nl]
            await update.message.reply_text(f"```\n{chunk}\n```", parse_mode="Markdown")
            remaining = remaining[len(chunk):]
    else:
        await update.message.reply_text(f"```\n{crash_context}\n```", parse_mode="Markdown")

    # If we found a traceback, also extract just the error line
    if has_traceback:
        lines = crash_context.splitlines()
        error_lines = [l for l in lines if re.match(r"^\w*(Error|Exception|Fault)", l)]
        if error_lines:
            await update.message.reply_text(f"Error: `{error_lines[-1]}`", parse_mode="Markdown")


handler = CommandHandler("crashlog", crashlog_handler)
