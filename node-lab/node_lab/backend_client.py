"""httpx client for the live OpenJustice backend.

Only the three things node-lab cannot compute locally:

  * `POST /files/search`      — chunk-level vector hits for the RAG tool
  * `GET  /files/:id`         — file metadata (name), for prompt rendering
  * `GET  /files/:id/download`— raw bytes, for annotation document text
  * `GET  /_excerpts/:id`     — excerpt title / content / pinpoint

Auth is a `nap_` bearer API key (`HybridAuthGuard` accepts it alongside
session cookies). Set `NODE_LAB_API_KEY` and `NODE_LAB_BACKEND_URL`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


class BackendError(RuntimeError):
    pass


@dataclass
class FileMetadata:
    id: str
    name: str
    mime_type: str | None = None
    preview: str | None = None


@dataclass
class ExcerptRecord:
    id: str
    title: str
    content: str
    pinpoint: str | None = None


@dataclass
class ChunkHit:
    """SOURCE: apps/backend/src/file/vector/file-vector.types.ts :: ChunkSearchResult"""

    file_id: str
    chunk_text: str
    chunk_index: int
    score: float


class BackendClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        *,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = (
            base_url or os.environ.get("NODE_LAB_BACKEND_URL") or ""
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("NODE_LAB_API_KEY")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def _require(self) -> httpx.AsyncClient:
        if not self.configured:
            raise BackendError(
                "Backend access requires NODE_LAB_BACKEND_URL and NODE_LAB_API_KEY "
                "(a `nap_` API key). Use --no-rag and --text-dir to run offline."
            )
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self._timeout,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "BackendClient":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    # -- endpoints --------------------------------------------------------

    async def search_files(
        self,
        query: str,
        *,
        scope: str,
        limit: int | None = None,
        file_filter: dict[str, Any] | None = None,
    ) -> list[ChunkHit]:
        client = self._require()
        body: dict[str, Any] = {"query": query, "scope": scope}
        if limit is not None:
            body["limit"] = limit
        if file_filter:
            body["filter"] = file_filter

        response = await client.post("/files/search", json=body)
        _raise_for_status(response, "POST /files/search")
        payload = response.json()
        return [
            ChunkHit(
                file_id=item["fileId"],
                chunk_text=item.get("chunkText") or "",
                chunk_index=item.get("chunkIndex", 0),
                score=float(item.get("score", 0.0)),
            )
            for item in payload
        ]

    async def get_file_metadata(self, file_id: str) -> FileMetadata:
        client = self._require()
        response = await client.get(f"/files/{file_id}")
        _raise_for_status(response, f"GET /files/{file_id}")
        data = response.json()
        return FileMetadata(
            id=data["id"],
            name=data.get("name") or file_id,
            mime_type=data.get("mimeType"),
            preview=data.get("preview"),
        )

    async def download_file(self, file_id: str) -> tuple[bytes, str]:
        """Raw file bytes + content type.

        Uses `/files/:id/download` rather than
        `/file-library/citations/:id/content`: the download route is documented
        in-code as the "single access-gated download path: handles owner,
        public, and grantee-via-imported-conversation in one helper" — the
        right default for a lab run that may reference files the caller does
        not own.
        """
        client = self._require()
        response = await client.get(f"/files/{file_id}/download")
        _raise_for_status(response, f"GET /files/{file_id}/download")
        content_type = response.headers.get("content-type", "")
        return response.content, content_type

    async def get_excerpt(self, excerpt_id: str) -> ExcerptRecord:
        client = self._require()
        response = await client.get(f"/_excerpts/{excerpt_id}")
        _raise_for_status(response, f"GET /_excerpts/{excerpt_id}")
        data = response.json()
        return ExcerptRecord(
            id=data["id"],
            title=data.get("title") or "",
            content=data.get("content") or "",
            pinpoint=data.get("pinpoint"),
        )


def _raise_for_status(response: httpx.Response, what: str) -> None:
    if response.is_success:
        return
    body = response.text[:500]
    raise BackendError(f"{what} failed with {response.status_code}: {body}")


__all__ = [
    "BackendClient",
    "BackendError",
    "ChunkHit",
    "ExcerptRecord",
    "FileMetadata",
]
