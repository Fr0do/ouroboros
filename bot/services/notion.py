import json
from pathlib import Path
from datetime import datetime
from notion_client import Client
from .config import NOTION_SECRET, ROOT

_client: Client | None = None
_pages: dict | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(auth=NOTION_SECRET)
    return _client


def load_page_ids() -> dict:
    """Load saved page ID mapping from notion_pages.json."""
    global _pages
    if _pages is None:
        p = ROOT / "notion_pages.json"
        if p.exists():
            _pages = json.loads(p.read_text())
        else:
            _pages = {}
    return _pages


def add_note(project: str, text: str) -> str:
    """Append a note block to a project's Notion page."""
    pages = load_page_ids()
    page_id = pages.get(project)
    if not page_id:
        return f"No Notion page found for '{project}'. Run notion_bootstrap.py first."

    client = get_client()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    client.blocks.children.append(
        block_id=page_id,
        children=[{
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": f"[{now}] {text}"}}]
            }
        }]
    )
    return f"Note added to {project}"



def add_to_backlog(text: str) -> str:
    """Add an item to the Ideas & Backlog page."""
    pages = load_page_ids()
    page_id = pages.get("backlog")
    if not page_id:
        return "No backlog page found. Run notion_bootstrap.py first."

    client = get_client()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    client.blocks.children.append(
        block_id=page_id,
        children=[{
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": f"[{now}] {text}"}}],
                "checked": False,
            }
        }]
    )
    return "Added to backlog"
