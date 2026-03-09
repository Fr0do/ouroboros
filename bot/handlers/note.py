from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.notion import add_note, add_to_backlog
from ..services.tg import authorized, require_project


@authorized
async def note_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/note <project> <text> — push note to Notion project page."""
    args = context.args or []
    name, err = require_project(args, "/note <project> <text>")
    if err:
        await update.message.reply_text(err, parse_mode="Markdown")
        return
    if len(args) < 2:
        await update.message.reply_text("Usage: `/note <project> <text>`", parse_mode="Markdown")
        return

    text = " ".join(args[1:])
    result = add_note(name, text)
    await update.message.reply_text(result)


@authorized
async def task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/task <description> — add to Notion backlog."""
    args = context.args or []
    if not args:
        await update.message.reply_text("Usage: `/task <description>`", parse_mode="Markdown")
        return

    text = " ".join(args)
    result = add_to_backlog(text)
    await update.message.reply_text(result)


note_cmd = CommandHandler("note", note_handler)
task_cmd = CommandHandler("task", task_handler)
