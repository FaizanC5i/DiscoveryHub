"""Deletes every project via the service layer (also clears Azure blobs)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.db.session import get_session_factory
from app.db.models import Project
from app.services import project_service
from app.services.storage.blob_storage import get_blob_storage

SessionFactory = get_session_factory()
storage = get_blob_storage()

with SessionFactory() as db:
    projects = db.scalars(select(Project)).all()
    if not projects:
        print("No projects found.")
    else:
        print(f"Found {len(projects)} project(s). Deleting...")
        for p in projects:
            project_service.delete_project(db, storage, p.owner_id, p.id)
            print(f"  Deleted project {p.id}: {p.name}")
        print("Done. All projects removed.")
