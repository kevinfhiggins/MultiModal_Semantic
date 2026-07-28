#!/usr/bin/env python3
"""
One-off migration: rewrite MoD_Data.file_path to portable relative paths.

Historically file_path was stored as an absolute, machine-specific path
(e.g. /home/<user>/.../sample_data/uploads/foo.jpg) that also pointed at the
wrong subdirectory for most docs. This migration rewrites each file_path to the
relative path (relative to the storage root) where the file actually resolves:

    - "<source_file>"           if the file lives at the storage root / in S3, or
    - "uploads/<source_file>"   if it lives in the uploads/ subdirectory.

A backup of the previous _id -> file_path values is written to a timestamped
JSON file so the change is reversible.

Usage:
    python scripts/migrate_file_paths.py            # apply
    python scripts/migrate_file_paths.py --dry-run  # preview only
    python scripts/migrate_file_paths.py --restore <backup.json>
"""

import sys
import json
import argparse
from pathlib import Path

# Make the backend package importable.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.config import get_settings
from app.database import init_database, close_database
from app.storage import resolve_file


def choose_relative_path(settings, source_file: str) -> str | None:
    """Return the relative path where source_file actually resolves, or None."""
    if resolve_file(settings, source_file) is not None:
        return source_file
    if resolve_file(settings, f"uploads/{source_file}") is not None:
        return f"uploads/{source_file}"
    return None


def restore(collection, backup_path: str):
    from bson import ObjectId

    with open(backup_path) as f:
        backup = json.load(f)
    restored = 0
    for _id, old_path in backup.items():
        collection.update_one({"_id": ObjectId(_id)}, {"$set": {"file_path": old_path}})
        restored += 1
    print(f"✓ Restored file_path on {restored} documents from {backup_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="preview without writing")
    parser.add_argument("--restore", metavar="BACKUP", help="restore from a backup json")
    args = parser.parse_args()

    settings = get_settings()
    db = init_database(settings)
    collection = db.collection

    if args.restore:
        restore(collection, args.restore)
        close_database()
        return

    docs = list(collection.find({}, {"_id": 1, "source_file": 1, "file_path": 1, "modality": 1}))
    print(f"Scanning {len(docs)} documents...\n")

    backup = {}
    to_update = []   # (id, old, new)
    unchanged = 0
    unresolved = []

    for d in docs:
        _id = d["_id"]
        source_file = d.get("source_file", "")
        old_path = d.get("file_path", "") or ""

        new_path = choose_relative_path(settings, source_file)
        if new_path is None:
            unresolved.append((str(_id), d.get("modality"), source_file))
            continue

        backup[str(_id)] = old_path
        if old_path == new_path:
            unchanged += 1
        else:
            to_update.append((_id, old_path, new_path))

    print(f"  to update : {len(to_update)}")
    print(f"  unchanged : {unchanged}")
    print(f"  unresolved: {len(unresolved)} (left as-is)\n")

    # Show a sample of the changes.
    for _id, old, new in to_update[:5]:
        print(f"  {str(_id)[:8]}…  {old!r}\n            -> {new!r}")
    if len(to_update) > 5:
        print(f"  ... and {len(to_update) - 5} more")
    if unresolved:
        print("\n  Unresolved (file not found locally or in S3):")
        for _id, modality, sf in unresolved[:10]:
            print(f"    [{modality}] {sf}")

    if args.dry_run:
        print("\n[dry-run] No changes written.")
        close_database()
        return

    if not to_update:
        print("\nNothing to change.")
        close_database()
        return

    # Write backup before mutating.
    backup_path = REPO_ROOT / "scripts" / "file_path_backup.json"
    with open(backup_path, "w") as f:
        json.dump(backup, f, indent=2)
    print(f"\n✓ Backup written: {backup_path} ({len(backup)} entries)")
    print("  (restore with: python scripts/migrate_file_paths.py --restore "
          f"{backup_path})")

    # Apply updates.
    for _id, _old, new in to_update:
        collection.update_one({"_id": _id}, {"$set": {"file_path": new}})

    print(f"\n✓ Updated file_path on {len(to_update)} documents.")
    close_database()


if __name__ == "__main__":
    main()
