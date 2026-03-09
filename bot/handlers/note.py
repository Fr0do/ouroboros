from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.notion import add_note, add_to_backlog


async def note_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/note <project> <text> — push note to Notion project page."""
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Usage: `/note <project> <text>`", parse_mode="Markdown")
        return

    project = args[0]
    text = " ".join(args[1:])
    result = add_note(project, text)
    await update.message.reply_text(result)


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
