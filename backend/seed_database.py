#!/usr/bin/env python3
"""
Seed script for MoD_Data collection

This script loads sample data from the manifest.json file and ingests
all documents into MongoDB Atlas with Voyage AI embeddings.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings
from app.database import init_database, close_database
from app.embeddings import init_embeddings
from app.ingestion import DataIngestion


def main():
    """Main seeding function"""
    print("=" * 60)
    print("MoD Semantic Search - Database Seeding")
    print("=" * 60)

    # Load settings
    print("\n[1/5] Loading configuration...")
    settings = get_settings()
    print(f"  ✓ Database: {settings.mongodb_database}")
    print(f"  ✓ Collection: {settings.mongodb_collection}")
    print(f"  ✓ Voyage Model: {settings.voyage_model}")

    # Initialize services
    print("\n[2/5] Initializing services...")
    db = init_database(settings)
    print("  ✓ MongoDB connected")

    embeddings = init_embeddings(settings)
    print("  ✓ Voyage AI initialized")

    # Create ingestion service
    ingestion = DataIngestion(db, embeddings)

    # Check for existing data
    print("\n[3/5] Checking existing data...")
    existing_count = db.collection.count_documents({})

    if existing_count > 0:
        response = input(
            f"\n  ⚠️  Collection already contains {existing_count} documents.\n"
            "  Do you want to clear it before seeding? (yes/no): "
        )
        if response.lower() in ['yes', 'y']:
            db.collection.delete_many({})
            print("  ✓ Collection cleared")
        else:
            print("  → Keeping existing documents")

    # Find manifest file
    print("\n[4/5] Loading manifest...")
    project_root = Path(__file__).parent.parent
    manifest_path = project_root / "sample_data" / "manifest.json"
    data_dir = project_root / "sample_data"

    if not manifest_path.exists():
        print(f"  ✗ Manifest file not found: {manifest_path}")
        print("  Please ensure sample_data/manifest.json exists")
        sys.exit(1)

    print(f"  ✓ Found manifest: {manifest_path}")

    # Ingest data
    print("\n[5/5] Ingesting documents...")
    print("  This may take a few minutes...")
    print("  Note: Only embeddings and file references will be stored in MongoDB\n")

    # Get base URL from settings if available
    base_url = os.getenv("FILE_BASE_URL", "http://localhost:8000/files")

    stats = ingestion.ingest_from_manifest(
        manifest_path=str(manifest_path),
        data_dir=str(data_dir),
        base_url=base_url
    )

    # Print results
    print("\n" + "=" * 60)
    print("Seeding Complete!")
    print("=" * 60)
    print(f"\n  Total processed: {stats['total']}")
    print(f"  ✓ Successfully ingested: {stats['success']}")
    print(f"  ✗ Failed: {stats['failed']}")
    print(f"\n  By modality:")
    print(f"    • PDFs: {stats['by_modality']['pdf']}")
    print(f"    • Audio: {stats['by_modality']['audio']}")
    print(f"    • Images: {stats['by_modality']['image']}")

    # Final count
    final_count = db.collection.count_documents({})
    print(f"\n  Total documents in collection: {final_count}")

    print("\n✓ Database seeding successful!")
    print("\nNext steps:")
    print("  1. Ensure vector index is created in MongoDB Atlas")
    print("  2. Start the backend: cd backend && uvicorn app.main:app --reload")
    print("  3. Open the frontend: open frontend/index.html")

    # Cleanup
    close_database()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSeeding cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
