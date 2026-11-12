"""
Where the original files are kept.

Analogy: the warehouse. The database holds the shelf label (blob_path). The
warehouse holds the box itself. The service only asks the warehouse to store,
fetch, or remove a box by its label.
"""

from functools import lru_cache
from typing import Protocol

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient, ContentSettings

from app.core.config import get_settings
from app.core.errors import api_error


class BlobNotFound(Exception):
    """The requested blob does not exist."""


class BlobStorage(Protocol):
    def save(self, key: str, data: bytes, content_type: str) -> None: ...
    def read(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


class AzureBlobStorage:
    def __init__(self, connection_string: str, container_name: str) -> None:
        service = BlobServiceClient.from_connection_string(connection_string)
        self._container = service.get_container_client(container_name)

    def save(self, key: str, data: bytes, content_type: str) -> None:
        self._container.upload_blob(
            name=key,
            data=data,
            overwrite=False,
            content_settings=ContentSettings(content_type=content_type),
        )

    def read(self, key: str) -> bytes:
        try:
            return self._container.download_blob(key).readall()
        except ResourceNotFoundError as exc:
            raise BlobNotFound(key) from exc

    def delete(self, key: str) -> None:
        try:
            self._container.delete_blob(key)
        except ResourceNotFoundError:
            return


class InMemoryBlobStorage:
    """Test double. Keeps files in a dictionary."""

    def __init__(self) -> None:
        self.blobs: dict[str, bytes] = {}

    def save(self, key: str, data: bytes, content_type: str) -> None:
        self.blobs[key] = data

    def read(self, key: str) -> bytes:
        if key not in self.blobs:
            raise BlobNotFound(key)
        return self.blobs[key]

    def delete(self, key: str) -> None:
        self.blobs.pop(key, None)


@lru_cache
def get_blob_storage() -> BlobStorage:
    settings = get_settings()
    if not settings.azure_storage_connection_string:
        raise api_error(503, "STORAGE_NOT_CONFIGURED", "File storage is not configured on the server.")
    return AzureBlobStorage(settings.azure_storage_connection_string, settings.azure_storage_container)