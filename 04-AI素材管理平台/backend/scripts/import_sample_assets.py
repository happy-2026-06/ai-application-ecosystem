"""Import sample assets into the database.

Run: python scripts/import_sample_assets.py
Pre-requisite: python scripts/generate_sample_assets.py (generates images)
"""
import os
import sys
import json
import asyncio
import hashlib
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use the script's own DB session helper so we don't depend on app context
from app.db.session import AsyncSessionLocal, init_db
from app.models.asset import Asset
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select


SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample-assets")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "uploads", "assets")


async def main():
    await init_db()

    # Find admin user for uploaded_by
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.role == "admin").limit(1))
        admin = result.scalar_one_or_none()
        admin_id = admin.id if admin else None
        await db.commit()

    if not os.path.isdir(SAMPLE_DIR):
        print(f"Sample directory not found: {SAMPLE_DIR}")
        return

    # Get image files
    files = sorted([f for f in os.listdir(SAMPLE_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))])
    print(f"Found {len(files)} sample images")

    # Load metadata if available
    meta_path = os.path.join(SAMPLE_DIR, "sample-metadata.json")
    metadata_map = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                metadata_map[item["name"]] = item

    imported = 0
    for filename in files:
        filepath = os.path.join(SAMPLE_DIR, filename)

        # Check if already imported
        content = open(filepath, "rb").read()
        content_hash = hashlib.sha256(content).hexdigest()

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Asset).where(Asset.original_name == filename))
            existing = result.scalar_one_or_none()
            if existing:
                print(f"  SKIP (exists): {filename}")
                await db.rollback()
                continue

            asset_id = str(uuid.uuid4())
            asset_upload_dir = os.path.join(UPLOAD_DIR, asset_id)
            os.makedirs(asset_upload_dir, exist_ok=True)

            # Copy file to uploads
            dest_path = os.path.join(asset_upload_dir, filename)
            with open(dest_path, "wb") as f:
                f.write(content)

            ext = os.path.splitext(filename)[1].lower()
            mimetypes_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}
            file_type = mimetypes_map.get(ext, "image/jpeg")

            meta = metadata_map.get(filename, {})
            tags = meta.get("tags", [])
            ai_tags = meta.get("ai_tags", tags)
            ai_description = meta.get("ai_description", f"素材: {filename}")

            asset = Asset(
                id=asset_id,
                filename=filename,
                original_name=filename,
                file_type=file_type,
                file_size=len(content),
                file_path=dest_path,
                tags=tags or None,
                ai_tags=ai_tags or None,
                ai_description=ai_description,
                status="ready",
                version=1,
                uploaded_by=admin_id,
            )
            db.add(asset)
            await db.flush()
            await db.commit()
            imported += 1
            print(f"  [{imported}] IMPORTED: {filename} ({len(content)} bytes, tags={ai_tags[:3] if ai_tags else 'none'})")

    print(f"\nDone! Imported {imported} new assets.")


if __name__ == "__main__":
    asyncio.run(main())
