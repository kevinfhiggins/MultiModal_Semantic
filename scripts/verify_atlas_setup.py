#!/usr/bin/env python3
"""
Verify MongoDB Atlas and Vector Search setup
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from pymongo import MongoClient
from app.config import get_settings


def verify_setup():
    """Verify MongoDB Atlas connection and configuration"""

    print("=" * 70)
    print("MongoDB Atlas Setup Verification")
    print("=" * 70)

    settings = get_settings()

    print("\n[1/5] Testing MongoDB connection...")
    try:
        client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("  ✓ MongoDB connection successful")
    except Exception as e:
        print(f"  ✗ MongoDB connection failed: {e}")
        return False

    print("\n[2/5] Checking database and collection...")
    db = client[settings.mongodb_database]
    collection = db[settings.mongodb_collection]

    try:
        count = collection.count_documents({})
        print(f"  ✓ Database: {settings.mongodb_database}")
        print(f"  ✓ Collection: {settings.mongodb_collection}")
        print(f"  ℹ️  Document count: {count}")
    except Exception as e:
        print(f"  ✗ Error accessing collection: {e}")
        return False

    print("\n[3/5] Checking for sample document...")
    try:
        sample = collection.find_one()
        if sample:
            print("  ✓ Sample document found")
            print(f"    • Title: {sample.get('title', 'N/A')}")
            print(f"    • Modality: {sample.get('modality', 'N/A')}")
            print(f"    • Has embedding: {'embedding' in sample}")
            if 'embedding' in sample:
                print(f"    • Embedding dimensions: {len(sample['embedding'])}")
        else:
            print("  ⚠️  No documents in collection (run seeding script)")
    except Exception as e:
        print(f"  ✗ Error reading document: {e}")

    print("\n[4/5] Checking vector search index...")
    try:
        # Try to list indexes (note: this won't show Atlas Search indexes directly)
        indexes = list(collection.list_indexes())
        print(f"  ℹ️  Regular indexes found: {len(indexes)}")

        print("\n  ⚠️  Vector Search indexes are managed in Atlas UI")
        print("     Go to Atlas → Search tab to verify index creation")
        print(f"     Expected index name: {settings.vector_index_name}")
    except Exception as e:
        print(f"  ⚠️  Could not list indexes: {e}")

    print("\n[5/5] Testing vector search (if index exists)...")
    try:
        # Try a simple vector search query
        test_embedding = [0.1] * settings.vector_dimension

        pipeline = [
            {
                "$vectorSearch": {
                    "index": settings.vector_index_name,
                    "path": "embedding",
                    "queryVector": test_embedding,
                    "numCandidates": 10,
                    "limit": 1
                }
            }
        ]

        result = list(collection.aggregate(pipeline))

        if result:
            print("  ✓ Vector search is working!")
            print("  ✓ Index is properly configured")
        else:
            print("  ⚠️  Vector search returned no results")
            print("     This is normal if collection is empty")

    except Exception as e:
        error_msg = str(e)
        if "index" in error_msg.lower() or "not found" in error_msg.lower():
            print("  ✗ Vector search index not found")
            print("  ⚠️  Please create the index in Atlas UI:")
            print("     1. Go to https://cloud.mongodb.com/")
            print("     2. Select your cluster")
            print("     3. Click 'Search' tab")
            print("     4. Create index with name: vector_index")
            print("     5. Use the configuration from create_atlas_vector_index.py")
        else:
            print(f"  ⚠️  Vector search test failed: {e}")

    print("\n" + "=" * 70)
    print("Setup Verification Complete")
    print("=" * 70)

    if count == 0:
        print("\n⚠️  Next step: Run database seeding")
        print("   python3 backend/seed_database.py")
    else:
        print("\n✓ Your setup appears to be ready!")
        print("  Start the application with: ./RUN.sh")

    client.close()
    return True


if __name__ == "__main__":
    try:
        verify_setup()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
