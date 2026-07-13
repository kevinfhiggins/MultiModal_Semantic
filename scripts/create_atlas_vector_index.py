#!/usr/bin/env python3
"""
Create MongoDB Atlas Vector Search Index

This script creates the vector search index on MongoDB Atlas using the Admin API.
"""

import sys
import os
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from pymongo import MongoClient
from app.config import get_settings


def create_vector_search_index():
    """
    Create vector search index on MongoDB Atlas

    Note: This creates the index definition in the collection, but the actual
    Atlas Search index must be created through the Atlas UI or Atlas Admin API.
    """

    print("=" * 70)
    print("MongoDB Atlas Vector Search Index Configuration")
    print("=" * 70)

    # Load settings
    settings = get_settings()

    print("\n[1/3] Connecting to MongoDB Atlas...")
    client = MongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_database]
    collection = db[settings.mongodb_collection]

    try:
        # Test connection
        client.admin.command('ping')
        print(f"  ✓ Connected to: {settings.mongodb_database}.{settings.mongodb_collection}")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        sys.exit(1)

    print("\n[2/3] Vector Index Configuration...")

    index_definition = {
        "name": settings.vector_index_name,
        "type": "vectorSearch",
        "definition": {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": settings.vector_dimension,
                    "similarity": "cosine"
                }
            ]
        }
    }

    print(f"  Index Name: {settings.vector_index_name}")
    print(f"  Vector Field: embedding")
    print(f"  Dimensions: {settings.vector_dimension}")
    print(f"  Similarity: cosine")

    print("\n[3/3] Next Steps - CREATE INDEX IN ATLAS UI")
    print("=" * 70)
    print("\nThe vector search index MUST be created through MongoDB Atlas UI.")
    print("Follow these steps:\n")

    print("1. Go to: https://cloud.mongodb.com/")
    print("2. Select your cluster (Cluster0)")
    print("3. Click on 'Search' tab")
    print("4. Click 'Create Search Index'")
    print("5. Select 'JSON Editor'")
    print("6. Use this configuration:\n")

    json_config = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 1024,
                "similarity": "cosine"
            }
        ]
    }

    print(json.dumps(json_config, indent=2))

    print("\n7. Set:")
    print(f"   • Index Name: {settings.vector_index_name}")
    print(f"   • Database: {settings.mongodb_database}")
    print(f"   • Collection: {settings.mongodb_collection}")

    print("\n8. Click 'Create Search Index'")
    print("\n9. Wait 1-2 minutes for index to build")

    print("\n" + "=" * 70)
    print("After creating the index, verify with:")
    print("  python3 scripts/verify_atlas_setup.py")
    print("=" * 70)

    # Save configuration to file
    config_file = Path(__file__).parent / "atlas_index_config.json"
    with open(config_file, 'w') as f:
        json.dump({
            "index_name": settings.vector_index_name,
            "database": settings.mongodb_database,
            "collection": settings.mongodb_collection,
            "definition": json_config
        }, f, indent=2)

    print(f"\n✓ Configuration saved to: {config_file}")

    client.close()


if __name__ == "__main__":
    try:
        create_vector_search_index()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
