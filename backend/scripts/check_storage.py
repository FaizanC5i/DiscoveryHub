"""Checks that the storage connection string works and the container exists. Run from backend/."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from azure.storage.blob import BlobServiceClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402

settings = get_settings()
client = BlobServiceClient.from_connection_string(settings.azure_storage_connection_string)
container = client.get_container_client(settings.azure_storage_container)
print("Account:", client.account_name)
print("Container exists:", container.exists())