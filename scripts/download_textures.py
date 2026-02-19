#!/usr/bin/env python3
"""Download seamless CC0 textures from ambientCG and resize to 512x512.

Usage:
    python3 scripts/download_textures.py

Requires: pip install Pillow requests
"""

import io
import os
import zipfile

import requests
from PIL import Image

TEXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "resources", "textures")

# Curated set of seamless textures from ambientCG (CC0 license)
TEXTURE_IDS = [
    # Wood (4)
    "Wood049",
    "Wood054",
    "Wood066",
    "Wood092",
    # Marble / Stone (5)
    "Marble006",
    "Marble012",
    "Rock049",
    "Rock051",
    "Rock054",
    # Metal (3)
    "Metal032",
    "Metal034",
    "Metal038",
    # Fabric (3)
    "Fabric030",
    "Fabric045",
    "Fabric048",
    # Concrete / Brick (2)
    "Concrete034",
    "Bricks089",
    # Paper (2)
    "Paper004",
    "Paper006",
]

TARGET_SIZE = (512, 512)


def download_texture(texture_id: str) -> bool:
    """Download a single texture from ambientCG, extract color map, resize to 512x512."""
    out_path = os.path.join(TEXTURES_DIR, f"{texture_id}.jpg")
    if os.path.exists(out_path):
        print(f"  Already exists: {texture_id}")
        return True

    url = f"https://ambientcg.com/api/v2/downloads_csv?id={texture_id}&type=Photo"
    print(f"  Fetching download info for {texture_id}...")
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  Failed to get download info for {texture_id}: {e}")
        return False

    # Parse CSV to find 1K JPG download
    lines = resp.text.strip().split("\n")
    download_url = None
    for line in lines[1:]:  # skip header
        parts = line.split(",")
        if len(parts) >= 4:
            link = parts[-1].strip().strip('"')
            # Prefer 1K resolution
            if "1K-JPG" in link or "1K" in link:
                download_url = link
                break
    if not download_url:
        # Fall back to any JPG download
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) >= 4:
                link = parts[-1].strip().strip('"')
                if "JPG" in link:
                    download_url = link
                    break

    if not download_url:
        print(f"  No JPG download found for {texture_id}")
        return False

    print(f"  Downloading {texture_id} from {download_url}...")
    try:
        resp = requests.get(download_url, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print(f"  Download failed for {texture_id}: {e}")
        return False

    # Extract the color/diffuse map from the ZIP
    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            color_file = None
            for name in zf.namelist():
                lower = name.lower()
                if ("color" in lower or "diff" in lower) and lower.endswith(".jpg"):
                    color_file = name
                    break
            if not color_file:
                # Just take the first jpg
                for name in zf.namelist():
                    if name.lower().endswith(".jpg"):
                        color_file = name
                        break
            if not color_file:
                print(f"  No image found in ZIP for {texture_id}")
                return False

            img_data = zf.read(color_file)
    except zipfile.BadZipFile:
        # Not a zip - maybe direct image
        img_data = resp.content

    # Resize to 512x512
    img = Image.open(io.BytesIO(img_data))
    img = img.resize(TARGET_SIZE, Image.LANCZOS)
    img.save(out_path, "JPEG", quality=85)
    print(f"  Saved {texture_id} ({img.size[0]}x{img.size[1]})")
    return True


def main():
    os.makedirs(TEXTURES_DIR, exist_ok=True)
    print(f"Downloading {len(TEXTURE_IDS)} textures to {TEXTURES_DIR}")
    success = 0
    for tid in TEXTURE_IDS:
        if download_texture(tid):
            success += 1
    print(f"\nDone: {success}/{len(TEXTURE_IDS)} textures downloaded.")


if __name__ == "__main__":
    main()
