#!/usr/bin/env python3
"""
Download sample placeholder images for demo

Uses placeholder image services to create realistic-looking image files
that can be displayed in the UI.
"""

import os
import requests
from pathlib import Path

def download_placeholder_image(filename, width=800, height=600, text="Military Vehicle"):
    """Download a placeholder image"""

    # Use placeholder.com service
    url = f"https://via.placeholder.com/{width}x{height}/4a5f4d/ffffff?text={text.replace(' ', '+')}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content
        else:
            print(f"  ⚠️  Failed to download {filename}: {response.status_code}")
            return None
    except Exception as e:
        print(f"  ⚠️  Error downloading {filename}: {e}")
        return None


def create_sample_images():
    """Create sample placeholder images"""

    print("=" * 70)
    print("Creating Sample Images")
    print("=" * 70)

    project_root = Path(__file__).parent.parent
    images_dir = project_root / "sample_data" / "images"

    print(f"\nTarget directory: {images_dir}")

    # Remove placeholder files
    print("\n[1/2] Removing placeholder files...")
    for placeholder in images_dir.glob("*.placeholder"):
        placeholder.unlink()
        print(f"  ✓ Removed {placeholder.name}")

    # Image definitions with text overlays
    images = {
        "challenger2_desert.jpg": "Challenger 2 Tank",
        "as90_artillery.jpg": "AS90 Artillery",
        "convoy_formation.jpg": "Military Convoy",
        "warrior_ifv.jpg": "Warrior IFV",
        "ammunition_display.jpg": "120mm Ammunition"
    }

    print("\n[2/2] Creating sample images...")

    for filename, text in images.items():
        filepath = images_dir / filename

        print(f"  Creating {filename}...", end=" ")

        image_data = download_placeholder_image(filename, width=800, height=600, text=text)

        if image_data:
            with open(filepath, 'wb') as f:
                f.write(image_data)
            print(f"✓ ({len(image_data)} bytes)")
        else:
            print("✗ Failed")

    print("\n" + "=" * 70)
    print("Sample Images Created!")
    print("=" * 70)

    print("\n✓ Images are now ready for display in the UI")
    print("\nNote: These are placeholder images for demo purposes.")
    print("Replace them with actual images for production use.")


if __name__ == "__main__":
    try:
        create_sample_images()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
