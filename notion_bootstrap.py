"""One-time Notion workspace setup for Ouroboros.

Creates the page hierarchy:
  Ouroboros (root)
  ├── Research Timeline
  ├── s_cot
  ├── long-vqa (MMReD)
  ├── bbbo
  ├── Ideas & Backlog
  └── Infrastructure

Saves page IDs to notion_pages.json.
"""
import json
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

import os
from notion_client import Client

NOTION_SECRET = os.environ["NOTION_SECRET"]
client = Client(auth=NOTION_SECRET)

CHILD_PAGES = {
    "timeline": "Research Timeline",
    "s_cot": "s_cot — Spectral-R1",
    "long-vqa": "long-vqa — MMReD Benchmark",
    "bbbo": "bbbo — GeneralOptimizer",
    "backlog": "Ideas & Backlog",
    "infra": "Infrastructure",
}


def find_or_create_root() -> str:
    """Search for existing Ouroboros page or create one."""
    results = client.search(query="Ouroboros", filter={"property": "object", "value": "page"}).get("results", [])

    for page in results:
        title_parts = page.get("properties", {}).get("title", {}).get("title", [])
        if title_parts and "Ouroboros" in title_parts[0].get("plain_text", ""):
            print(f"Found existing root page: {page['id']}")
            return page["id"]

    # Create as a top-level page (requires integration to have access to a parent page)
    # For internal integrations, we create in the workspace
    page = client.pages.create(
        parent={"type": "workspace", "workspace": True},
        properties={
            "title": [{"type": "text", "text": {"content": "Ouroboros"}}]
        },
        icon={"type": "emoji", "emoji": "🐍"},
    )
    print(f"Created root page: {page['id']}")
    return page["id"]


def create_child_pages(root_id: str) -> dict:
    """Create child pages under root. Returns {key: page_id} mapping."""
    page_ids = {"root": root_id}

    for key, title in CHILD_PAGES.items():
        # Check if already exists
        existing = client.blocks.children.list(block_id=root_id).get("results", [])
        found = False
        for block in existing:
            if block.get("type") == "child_page" and title in block.get("child_page", {}).get("title", ""):
                page_ids[key] = block["id"]
                print(f"  Found existing: {title} -> {block['id']}")
                found = True
                break

        if not found:
            page = client.pages.create(
                parent={"page_id": root_id},
                properties={
                    "title": [{"type": "text", "text": {"content": title}}]
                },
            )
            page_ids[key] = page["id"]
            print(f"  Created: {title} -> {page['id']}")

    return page_ids


def main():
    print("Bootstrapping Notion workspace for Ouroboros...\n")
    root_id = find_or_create_root()
    page_ids = create_child_pages(root_id)

    out_path = ROOT / "notion_pages.json"
    out_path.write_text(json.dumps(page_ids, indent=2))
    print(f"\nSaved page mapping to {out_path}")
    print(json.dumps(page_ids, indent=2))


if __name__ == "__main__":
    main()
