#!/usr/bin/env python3
"""
Create MongoDB Atlas Vector Search Index via Admin API

This script uses the Atlas Admin API to programmatically create the vector search index.
Requires Atlas API public and private keys.
"""

import sys
import os
import json
import requests
from requests.auth import HTTPDigestAuth
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import get_settings


def create_index_via_api(
    public_key: str,
    private_key: str,
    project_id: str,
    cluster_name: str
):
    """
    Create vector search index using Atlas Admin API

    Args:
        public_key: Atlas API public key
        private_key: Atlas API private key
        project_id: Atlas project ID
        cluster_name: Cluster name (e.g., "Cluster0")
    """

    settings = get_settings()

    print("=" * 70)
    print("Creating Vector Search Index via Atlas Admin API")
    print("=" * 70)

    # Atlas Admin API endpoint
    base_url = "https://cloud.mongodb.com/api/atlas/v1.0"
    url = f"{base_url}/groups/{project_id}/clusters/{cluster_name}/fts/indexes"

    # Index definition
    index_definition = {
        "name": settings.vector_index_name,
        "database": settings.mongodb_database,
        "collectionName": settings.mongodb_collection,
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

    print("\n[1/3] Index Configuration:")
    print(json.dumps(index_definition, indent=2))

    print("\n[2/3] Creating index via API...")

    try:
        response = requests.post(
            url,
            auth=HTTPDigestAuth(public_key, private_key),
            headers={"Content-Type": "application/json"},
            json=index_definition
        )

        if response.status_code == 201:
            print("  ✓ Index creation initiated successfully!")
            result = response.json()
            print(f"  Index ID: {result.get('indexID', 'N/A')}")
            print(f"  Status: {result.get('status', 'N/A')}")

            print("\n[3/3] Waiting for index to build...")
            print("  This usually takes 1-2 minutes...")

            # Poll for index status
            index_id = result.get('indexID')
            if index_id:
                for i in range(30):  # Wait up to 5 minutes
                    time.sleep(10)
                    status_url = f"{url}/{index_id}"
                    status_response = requests.get(
                        status_url,
                        auth=HTTPDigestAuth(public_key, private_key)
                    )

                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', 'UNKNOWN')
                        print(f"  Status: {status}")

                        if status == "ACTIVE":
                            print("\n✓ Vector search index is now ACTIVE and ready!")
                            print("\nYou can now run: python3 backend/seed_database.py")
                            return True
                        elif status == "FAILED":
                            print("\n✗ Index creation failed!")
                            print(f"  Error: {status_data.get('error', 'Unknown error')}")
                            return False

                print("\n⚠️  Index is still building. Check Atlas UI for status.")

        elif response.status_code == 409:
            print("  ⚠️  Index already exists!")
            print("  You can proceed to seeding the database.")
            return True

        else:
            print(f"  ✗ Failed to create index")
            print(f"  Status code: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def get_atlas_credentials():
    """Prompt user for Atlas API credentials"""

    print("\nTo create the index programmatically, you need Atlas API credentials.")
    print("\nTo get these credentials:")
    print("  1. Go to: https://cloud.mongodb.com/")
    print("  2. Click on your profile (top right)")
    print("  3. Select 'Organization Access Manager' or 'Project Access Manager'")
    print("  4. Click 'API Keys' → 'Create API Key'")
    print("  5. Give it 'Project Owner' permissions")
    print("  6. Copy the Public Key and Private Key")
    print("\nYou'll also need your Project ID:")
    print("  1. In Atlas, click on your project name")
    print("  2. Click 'Project Settings'")
    print("  3. Copy the Project ID")

    print("\n" + "=" * 70)

    public_key = input("\nEnter Atlas API Public Key (or 'skip' for manual): ").strip()

    if public_key.lower() == 'skip':
        return None, None, None, None

    private_key = input("Enter Atlas API Private Key: ").strip()
    project_id = input("Enter Project ID: ").strip()
    cluster_name = input("Enter Cluster Name [Cluster0]: ").strip() or "Cluster0"

    return public_key, private_key, project_id, cluster_name


def main():
    """Main function"""

    print("=" * 70)
    print("MongoDB Atlas Vector Search Index Creation")
    print("=" * 70)

    print("\nOptions:")
    print("  1. Create via Atlas Admin API (requires API credentials)")
    print("  2. Show manual UI instructions")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        public_key, private_key, project_id, cluster_name = get_atlas_credentials()

        if all([public_key, private_key, project_id, cluster_name]):
            success = create_index_via_api(
                public_key=public_key,
                private_key=private_key,
                project_id=project_id,
                cluster_name=cluster_name
            )

            if success:
                print("\n✓ Setup complete! Run: python3 backend/seed_database.py")
            else:
                print("\n✗ Index creation failed. Try manual method (option 2)")
        else:
            print("\nCancelled. Use option 2 for manual instructions.")

    else:
        show_manual_instructions()


def show_manual_instructions():
    """Show detailed manual UI instructions"""

    settings = get_settings()

    print("\n" + "=" * 70)
    print("MANUAL UI INSTRUCTIONS - STEP BY STEP")
    print("=" * 70)

    print("""
📋 FOLLOW THESE EXACT STEPS:

Step 1: Open Atlas
──────────────────
• Open your browser to: https://cloud.mongodb.com/
• Log in with your credentials
• Make sure you're in the correct organization

Step 2: Select Your Cluster
────────────────────────────
• Click on "Database" in the left sidebar (if not already selected)
• Find your cluster: Cluster0
• Do NOT click "Browse Collections" - we need "Search"

Step 3: Open Search Tab
────────────────────────
• Click on the "Search" tab/button near the top
  (It's next to "Browse Collections", "Metrics", etc.)
• You should see "Atlas Search" page

Step 4: Create Search Index
────────────────────────────
• Click the green "Create Search Index" button
• You'll see two options:
  - Visual Editor
  - JSON Editor
• Select "JSON Editor"
• Click "Next"

Step 5: Configure Index
────────────────────────
• In the JSON editor, DELETE everything and paste this:
""")

    index_json = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 1024,
                "similarity": "cosine"
            }
        ]
    }

    print(json.dumps(index_json, indent=2))

    print(f"""
Step 6: Set Database and Collection
────────────────────────────────────
• Database: {settings.mongodb_database}
• Collection: {settings.mongodb_collection}
• Index Name: {settings.vector_index_name}

Step 7: Create Index
────────────────────
• Review your settings
• Click "Create Search Index" button
• Wait for confirmation message

Step 8: Wait for Build
──────────────────────
• Index will show status "Building" or "Initial Sync"
• Wait 1-2 minutes
• Refresh the page
• Status should change to "Active"

Step 9: Verify
──────────────
• You should see your index listed:
  Name: {settings.vector_index_name}
  Type: vectorSearch
  Status: Active

✓ DONE! Now you can run: python3 backend/seed_database.py

──────────────────────────────────────────────────────────────────
""")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
