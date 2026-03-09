"""Shared Notion helpers — thin wrapper over bot/services/notion.py for CLI use."""
from bot.services.notion import add_note, log_experiment, add_to_backlog, get_client, load_page_ids

__all__ = ["add_note", "log_experiment", "add_to_backlog", "get_client", "load_page_ids"]
