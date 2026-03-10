"""
/page — update the ouroboros project page with current vitals.

Usage:
  /page  — collect metrics, update HTML, commit & push
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from ..services.tg import authorized
from ..services.page import update_page

logger = logging.getLogger("ouroboros")


@authorized
async def page_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/page — update project page with current vitals."""
    msg = await update.message.reply_text("Updating project page...")

    try:
        result = await update_page()
    except Exception as e:
        logger.error(f"/page failed: {e}")
        await msg.edit_text(f"Error updating page: {e}")
        return

    await msg.edit_text(result)


handler = CommandHandler("page", page_handler)
