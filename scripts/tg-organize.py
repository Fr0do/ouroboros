#!/usr/bin/env python3
"""Telegram chat organizer — audit, categorize, and restructure folders/pins.

Usage:
    python scripts/tg-organize.py                  # audit current state
    python scripts/tg-organize.py --plan           # show proposed changes
    python scripts/tg-organize.py --apply          # apply changes (interactive confirm)
    python scripts/tg-organize.py --config folders.yaml  # use custom folder config
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv
from telethon import TelegramClient, functions, types
from telethon.tl.types import (
    Channel,
    Chat,
    DialogFilter,
    DialogFilterDefault,
    InputPeerChannel,
    InputPeerChat,
    InputPeerUser,
    User,
)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION = str(Path(__file__).resolve().parent.parent / ".tg_session")

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)
log = logging.getLogger("tg-organize")

# ── Default folder blueprint ────────────────────────────────────────────
DEFAULT_FOLDERS = {
    "Research": {
        "keywords": ["arxiv", "paper", "neurips", "icml", "iclr", "acl", "emnlp",
                      "research", "lab", "phd", "science", "ml", "ai", "deep learning"],
        "flags": {"groups": True, "broadcasts": True},
        "pin": [],
    },
    "Work": {
        "keywords": ["work", "team", "project", "office", "meeting", "standup",
                      "sprint", "jira", "task", "deadline"],
        "flags": {"groups": True},
        "pin": [],
    },
    "Channels": {
        "keywords": [],
        "flags": {"broadcasts": True},
        "auto_type": "channel",
        "pin": [],
    },
    "Bots": {
        "keywords": [],
        "flags": {"bots": True},
        "auto_type": "bot",
        "pin": [],
    },
    "Groups": {
        "keywords": [],
        "flags": {"groups": True},
        "auto_type": "group",
        "exclude_in": ["Research", "Work"],
        "pin": [],
    },
    "Personal": {
        "keywords": [],
        "flags": {"contacts": True, "non_contacts": True},
        "auto_type": "private",
        "exclude_in": ["Research", "Work", "Bots"],
        "pin": [],
    },
}

# ── Helpers ──────────────────────────────────────────────────────────────

def classify_entity(entity) -> str:
    """Return a type string: private, bot, group, supergroup, channel."""
    if isinstance(entity, User):
        return "bot" if entity.bot else "private"
    if isinstance(entity, Channel):
        return "channel" if entity.broadcast else "supergroup"
    if isinstance(entity, Chat):
        return "group"
    return "unknown"


def entity_title(entity) -> str:
    if isinstance(entity, User):
        parts = [entity.first_name or "", entity.last_name or ""]
        name = " ".join(p for p in parts if p)
        return name or entity.username or str(entity.id)
    return getattr(entity, "title", None) or str(entity.id)


def to_input_peer(entity):
    if isinstance(entity, User):
        return InputPeerUser(entity.id, entity.access_hash or 0)
    if isinstance(entity, Channel):
        return InputPeerChannel(entity.id, entity.access_hash or 0)
    if isinstance(entity, Chat):
        return InputPeerChat(entity.id)
    return None


def days_since(dt) -> int:
    if dt is None:
        return 9999
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).days


# ── Audit ────────────────────────────────────────────────────────────────

async def audit(client: TelegramClient) -> dict:
    """Fetch all dialogs and current folders, return structured audit."""
    dialogs = await client.get_dialogs(limit=None)
    log.info(f"Fetched {len(dialogs)} dialogs")

    chats = []
    for d in dialogs:
        entity = d.entity
        chats.append({
            "id": d.id,
            "title": entity_title(entity),
            "type": classify_entity(entity),
            "unread": d.unread_count,
            "pinned": d.pinned,
            "archived": d.archived,
            "muted": d.dialog.notify_settings.mute_until is not None
                     if hasattr(d.dialog, "notify_settings") and d.dialog.notify_settings else False,
            "last_activity": d.date,
            "days_inactive": days_since(d.date),
            "entity": entity,
        })

    # Current folders
    result = await client(functions.messages.GetDialogFiltersRequest())
    filters = result.filters if hasattr(result, "filters") else result
    folders = []
    for f in filters:
        if isinstance(f, DialogFilterDefault):
            folders.append({"id": 0, "title": "All Chats", "builtin": True})
            continue
        if isinstance(f, DialogFilter):
            folders.append({
                "id": f.id,
                "title": f.title if isinstance(f.title, str) else f.title.text,
                "pinned_count": len(f.pinned_peers),
                "include_count": len(f.include_peers),
                "exclude_count": len(f.exclude_peers),
                "flags": {
                    "contacts": f.contacts,
                    "non_contacts": f.non_contacts,
                    "groups": f.groups,
                    "broadcasts": f.broadcasts,
                    "bots": f.bots,
                    "exclude_muted": f.exclude_muted,
                    "exclude_read": f.exclude_read,
                    "exclude_archived": f.exclude_archived,
                },
                "builtin": False,
            })

    return {"chats": chats, "folders": folders}


def print_audit(data: dict):
    chats = data["chats"]
    folders = data["folders"]

    # Stats
    by_type = defaultdict(int)
    for c in chats:
        by_type[c["type"]] += 1
    pinned = [c for c in chats if c["pinned"]]
    archived = [c for c in chats if c["archived"]]
    dead = [c for c in chats if c["days_inactive"] > 90 and not c["pinned"]]

    print("\n" + "=" * 60)
    print("  TELEGRAM AUDIT")
    print("=" * 60)
    print(f"\n  Total dialogs: {len(chats)}")
    for t, n in sorted(by_type.items()):
        print(f"    {t}: {n}")
    print(f"\n  Pinned: {len(pinned)}")
    for c in pinned:
        print(f"    * {c['title']} ({c['type']})")
    print(f"\n  Archived: {len(archived)}")
    print(f"  Inactive >90d: {len(dead)}")

    print(f"\n  Current folders ({len(folders)}):")
    for f in folders:
        if f["builtin"]:
            print(f"    [{f['id']}] {f['title']} (default)")
        else:
            print(f"    [{f['id']}] {f['title']}  "
                  f"pinned={f['pinned_count']} include={f['include_count']} "
                  f"exclude={f['exclude_count']}")
            flags_on = [k for k, v in f["flags"].items() if v]
            if flags_on:
                print(f"         flags: {', '.join(flags_on)}")

    if dead:
        print(f"\n  Dead chats (>90 days, candidates for archive):")
        for c in sorted(dead, key=lambda x: -x["days_inactive"])[:20]:
            print(f"    {c['days_inactive']:>4}d  {c['title']} ({c['type']})")
        if len(dead) > 20:
            print(f"    ... and {len(dead) - 20} more")

    print()


# ── Planning ─────────────────────────────────────────────────────────────

def load_folder_config(path: str | None) -> dict:
    if path:
        with open(path) as f:
            return yaml.safe_load(f)
    return DEFAULT_FOLDERS


def plan_changes(data: dict, folder_config: dict) -> list[dict]:
    """Generate a list of changes to apply."""
    chats = data["chats"]
    existing = {f["title"]: f for f in data["folders"] if not f.get("builtin")}
    changes = []

    # Build assignment: which chats go to which folder
    assignments = defaultdict(list)  # folder_name -> [chat]
    assigned_ids = set()

    # Pass 1: keyword matching (highest priority)
    for fname, fconf in folder_config.items():
        keywords = [k.lower() for k in fconf.get("keywords", [])]
        if not keywords:
            continue
        for c in chats:
            if c["id"] in assigned_ids or c["archived"]:
                continue
            title_lower = c["title"].lower()
            if any(kw in title_lower for kw in keywords):
                assignments[fname].append(c)
                assigned_ids.add(c["id"])

    # Pass 2: type-based matching
    for fname, fconf in folder_config.items():
        auto_type = fconf.get("auto_type")
        if not auto_type:
            continue
        exclude_in = set(fconf.get("exclude_in", []))
        already_in_excluded = set()
        for ex_folder in exclude_in:
            already_in_excluded.update(c["id"] for c in assignments.get(ex_folder, []))

        for c in chats:
            if c["id"] in assigned_ids or c["archived"]:
                continue
            if c["id"] in already_in_excluded:
                continue
            if c["type"] == auto_type:
                assignments[fname].append(c)
                assigned_ids.add(c["id"])
            elif auto_type == "group" and c["type"] == "supergroup":
                assignments[fname].append(c)
                assigned_ids.add(c["id"])

    # Generate folder create/update changes
    next_id = max((f["id"] for f in data["folders"] if not f.get("builtin")), default=1) + 1
    for fname, fconf in folder_config.items():
        folder_chats = assignments.get(fname, [])
        if fname in existing:
            changes.append({
                "action": "update_folder",
                "name": fname,
                "id": existing[fname]["id"],
                "chats": folder_chats,
                "flags": fconf.get("flags", {}),
            })
        else:
            changes.append({
                "action": "create_folder",
                "name": fname,
                "id": next_id,
                "chats": folder_chats,
                "flags": fconf.get("flags", {}),
            })
            next_id += 1

    # Archive dead chats (>180 days inactive, not pinned, not already archived)
    dead = [c for c in chats
            if c["days_inactive"] > 180 and not c["pinned"] and not c["archived"]]
    if dead:
        changes.append({
            "action": "archive",
            "chats": dead,
        })

    return changes


def print_plan(changes: list[dict]):
    print("\n" + "=" * 60)
    print("  PROPOSED CHANGES")
    print("=" * 60)

    for ch in changes:
        if ch["action"] in ("create_folder", "update_folder"):
            verb = "CREATE" if ch["action"] == "create_folder" else "UPDATE"
            print(f"\n  [{verb}] Folder: {ch['name']} (id={ch['id']})")
            flags = [k for k, v in ch.get("flags", {}).items() if v]
            if flags:
                print(f"    Auto-include: {', '.join(flags)}")
            if ch["chats"]:
                print(f"    Explicitly include ({len(ch['chats'])} chats):")
                for c in ch["chats"][:15]:
                    print(f"      + {c['title']} ({c['type']})")
                if len(ch["chats"]) > 15:
                    print(f"      ... +{len(ch['chats']) - 15} more")
            else:
                print("    (flag-based only, no explicit chats)")

        elif ch["action"] == "archive":
            print(f"\n  [ARCHIVE] {len(ch['chats'])} dead chats (>180 days inactive):")
            for c in sorted(ch["chats"], key=lambda x: -x["days_inactive"])[:10]:
                print(f"    → {c['title']} ({c['days_inactive']}d)")
            if len(ch["chats"]) > 10:
                print(f"    ... +{len(ch['chats']) - 10} more")

    print()


# ── Apply ────────────────────────────────────────────────────────────────

async def apply_changes(client: TelegramClient, changes: list[dict]):
    for ch in changes:
        if ch["action"] in ("create_folder", "update_folder"):
            include_peers = []
            pinned_peers = []
            for c in ch.get("chats", []):
                ip = to_input_peer(c["entity"])
                if ip:
                    include_peers.append(ip)

            flags = ch.get("flags", {})
            title = ch["name"]

            # Build title as TextWithEntities for newer Telegram API
            try:
                title_obj = types.TextWithEntities(text=title, entities=[])
            except Exception:
                title_obj = title

            dialog_filter = DialogFilter(
                id=ch["id"],
                title=title_obj,
                pinned_peers=pinned_peers,
                include_peers=include_peers,
                exclude_peers=[],
                contacts=flags.get("contacts", False),
                non_contacts=flags.get("non_contacts", False),
                groups=flags.get("groups", False),
                broadcasts=flags.get("broadcasts", False),
                bots=flags.get("bots", False),
                exclude_muted=False,
                exclude_read=False,
                exclude_archived=True,
            )

            verb = "Creating" if ch["action"] == "create_folder" else "Updating"
            log.info(f"{verb} folder: {title} (id={ch['id']})")
            await client(functions.messages.UpdateDialogFilterRequest(
                id=ch["id"],
                filter=dialog_filter,
            ))

        elif ch["action"] == "archive":
            log.info(f"Archiving {len(ch['chats'])} dead chats")
            for c in ch["chats"]:
                try:
                    await client.edit_folder(c["entity"], 1)
                except Exception as e:
                    log.warning(f"  Failed to archive {c['title']}: {e}")

    # Reorder folders
    folder_ids = [ch["id"] for ch in changes
                  if ch["action"] in ("create_folder", "update_folder")]
    if folder_ids:
        try:
            log.info(f"Setting folder order: {folder_ids}")
            await client(functions.messages.UpdateDialogFiltersOrderRequest(
                order=folder_ids,
            ))
        except Exception as e:
            log.warning(f"Folder reorder failed (non-critical): {e}")

    log.info("Done!")


# ── Main ─────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Telegram chat organizer")
    parser.add_argument("--plan", action="store_true", help="Show proposed changes")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    parser.add_argument("--config", type=str, help="YAML folder config file")
    args = parser.parse_args()

    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.start()
    log.info("Connected to Telegram")

    data = await audit(client)
    print_audit(data)

    if args.plan or args.apply:
        folder_config = load_folder_config(args.config)
        changes = plan_changes(data, folder_config)
        print_plan(changes)

        if args.apply:
            answer = input("\nApply these changes? [y/N] ")
            if answer.strip().lower() == "y":
                await apply_changes(client, changes)
            else:
                print("Aborted.")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
