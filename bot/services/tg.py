from functools import wraps
from telegram import Update
from ..services.config import AUTHORIZED_USERS, PROJECTS


def authorized(func):
    """Decorator: silently ignore updates from users not in AUTHORIZED_USERS."""
    @wraps(func)
    async def wrapper(update, context):
        if AUTHORIZED_USERS and update.effective_user.id not in AUTHORIZED_USERS:
            return
        return await func(update, context)
    return wrapper


async def send_long(update: Update, text: str, **kwargs):
    """Send text, splitting into multiple messages if over Telegram's 4096 limit."""
    while text:
        chunk = text[:4000]
        if len(text) > 4000:
            nl = chunk.rfind("\n")
            if nl > 2000:
                chunk = text[:nl]
        await update.message.reply_text(chunk, **kwargs)
        text = text[len(chunk):]


def require_project(args: list, usage: str) -> tuple[str | None, str | None]:
    """Validate project arg. Returns (project_name, error_message). Error is None on success."""
    if not args:
        return None, f"Usage: `{usage}`"
    name = args[0]
    if name not in PROJECTS:
        return None, f"Unknown project. Available: {', '.join(PROJECTS)}"
    return name, None
