"""fileId -> parsed text, and the `<Annotated_Context>` inputs built from it.

Resolution order, first hit wins:

  1. `--text-dir <dir>/<fileId>.txt`  — local override, fully offline
  2. `.cache/<fileId>.txt`            — anything fetched on a previous run
  3. live backend                     — `GET /files/:id/download`, parsed here

Every backend fetch is written to `.cache/`, so a second run of the same node
is offline and byte-stable.

Caveat: `pypdf` text extraction is NOT byte-identical to the Node `pdf-parse`
path the backend uses. When that matters, drop a hand-checked `.txt` into
`--text-dir` and node-lab will never look further.
"""

from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .backend_client import BackendClient, BackendError
from .types import (
    Annotation,
    AnnotationContext,
    AnnotationExcerpt,
    AnnotationFile,
    SourceImportance,
    SourceType,
)

#: Cap on annotation document text inlined into the prompt. Production streams
#: full documents through the `read_file` tool instead; with that tool unported
#: the text goes straight into <Annotated_Context>, so it needs a ceiling.
ANNOTATION_FILE_BODY_CAP = 60000


def clean_pdf_text(text: str) -> str:
    """SOURCE: apps/backend/src/file/file-parser.service.ts :: cleanPdfText"""
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


@dataclass
class ResolvedFile:
    file_id: str
    name: str
    text: str
    origin: str  # "text-dir" | "cache" | "backend"


class DocumentResolver:
    def __init__(
        self,
        *,
        backend: BackendClient,
        cache_dir: Path,
        text_dir: Path | None = None,
    ) -> None:
        self.backend = backend
        self.cache_dir = cache_dir
        self.text_dir = text_dir
        self._files: dict[str, ResolvedFile] = {}
        self._excerpts: dict[str, AnnotationExcerpt] = {}

    # -- files ------------------------------------------------------------

    async def resolve_file(self, file_id: str) -> ResolvedFile:
        cached = self._files.get(file_id)
        if cached is not None:
            return cached

        resolved = await self._resolve_file_uncached(file_id)
        self._files[file_id] = resolved
        return resolved

    async def _resolve_file_uncached(self, file_id: str) -> ResolvedFile:
        if self.text_dir is not None:
            override = self.text_dir / f"{file_id}.txt"
            if override.exists():
                name = self._sidecar_name(self.text_dir, file_id) or file_id
                return ResolvedFile(
                    file_id=file_id,
                    name=name,
                    text=override.read_text(encoding="utf-8"),
                    origin="text-dir",
                )

        cache_text = self.cache_dir / f"{file_id}.txt"
        if cache_text.exists():
            name = self._sidecar_name(self.cache_dir, file_id) or file_id
            return ResolvedFile(
                file_id=file_id,
                name=name,
                text=cache_text.read_text(encoding="utf-8"),
                origin="cache",
            )

        meta = await self.backend.get_file_metadata(file_id)
        content, content_type = await self.backend.download_file(file_id)
        text = _parse_bytes(content, content_type, meta.name)

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_text.write_text(text, encoding="utf-8")
        (self.cache_dir / f"{file_id}.json").write_text(
            json.dumps({"id": file_id, "name": meta.name}, indent=2),
            encoding="utf-8",
        )
        return ResolvedFile(
            file_id=file_id, name=meta.name, text=text, origin="backend"
        )

    @staticmethod
    def _sidecar_name(directory: Path, file_id: str) -> str | None:
        sidecar = directory / f"{file_id}.json"
        if not sidecar.exists():
            return None
        try:
            return json.loads(sidecar.read_text(encoding="utf-8")).get("name")
        except (json.JSONDecodeError, OSError):
            return None

    # -- excerpts ---------------------------------------------------------

    async def resolve_excerpt(
        self, excerpt_id: str, importance: SourceImportance
    ) -> AnnotationExcerpt:
        cached = self._excerpts.get(excerpt_id)
        if cached is not None:
            return cached

        record = await self.backend.get_excerpt(excerpt_id)
        resolved = AnnotationExcerpt(
            id=record.id,
            title=record.title,
            text=record.content,
            source_type=importance,
            pinpoint=record.pinpoint,
        )
        self._excerpts[excerpt_id] = resolved
        return resolved


def build_importance_lookup(
    annotations: list[Annotation],
) -> dict[str, SourceImportance]:
    """SOURCE: annotation-utils.ts :: buildAnnotationImportanceLookup

    AUTHORITATIVE wins on conflict (same id cited at two importances) and a
    missing id falls back to AUTHORITATIVE — annotation sources are never
    silently downgraded.
    """
    lookup: dict[str, SourceImportance] = {}
    for ann in annotations:
        for source in ann.sources:
            prior = lookup.get(source.id)
            if prior is None or source.importance is SourceImportance.AUTHORITATIVE:
                lookup[source.id] = source.importance
    return lookup


def collect_source_ids(
    annotations: list[Annotation], source_type: SourceType
) -> list[str]:
    """SOURCE: annotation-utils.ts :: collectAnnotationFileIds / ...ExcerptIds

    Per-requirement scoping (`scopeAnnotationsToParagraphs`) is NOT ported:
    it exists to give each sub-agent only the docs for its slice, and the
    sub-agent fan-out is gone. The single analysis call gets every annotation
    source.
    """
    seen: list[str] = []
    known: set[str] = set()
    for ann in annotations:
        for source in ann.sources:
            if source.type is source_type and source.id not in known:
                known.add(source.id)
                seen.append(source.id)
    return seen


async def build_annotation_context(
    annotations: list[Annotation],
    resolver: DocumentResolver,
    *,
    on_warning: object = None,
) -> AnnotationContext:
    """Fetch every annotation source and shape it for the prompt builder.

    Replaces `buildAnnotationContext` + `fetchAnnotationSources`, whose inputs
    (FileRecord / Excerpt service objects) do not exist here. A source that
    cannot be resolved is reported and skipped rather than aborting the run —
    a lab run against a flow exported from another tenant will legitimately
    hit files the caller cannot read.
    """
    importance = build_importance_lookup(annotations)
    warn = on_warning if callable(on_warning) else (lambda _msg: None)

    files: list[AnnotationFile] = []
    for file_id in collect_source_ids(annotations, SourceType.FILE):
        try:
            resolved = await resolver.resolve_file(file_id)
        except BackendError as error:
            warn(f"annotation file {file_id} unresolved: {error}")
            continue
        files.append(
            AnnotationFile(
                file_id=file_id,
                file_name=resolved.name,
                summary=resolved.text[:ANNOTATION_FILE_BODY_CAP],
                source_type=importance.get(
                    file_id, SourceImportance.AUTHORITATIVE
                ),
            )
        )

    excerpts: list[AnnotationExcerpt] = []
    for excerpt_id in collect_source_ids(annotations, SourceType.EXCERPT):
        try:
            excerpts.append(
                await resolver.resolve_excerpt(
                    excerpt_id,
                    importance.get(excerpt_id, SourceImportance.AUTHORITATIVE),
                )
            )
        except BackendError as error:
            warn(f"annotation excerpt {excerpt_id} unresolved: {error}")

    return AnnotationContext(files=files, excerpts=excerpts)


def _parse_bytes(content: bytes, content_type: str, file_name: str) -> str:
    if "pdf" in content_type.lower() or file_name.lower().endswith(".pdf"):
        return clean_pdf_text(_parse_pdf(content))
    # Everything else is treated as text; the backend's DOCX path is not
    # ported (drop a .txt into --text-dir for those).
    return clean_pdf_text(content.decode("utf-8", errors="replace"))


def _parse_pdf(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


__all__ = [
    "ANNOTATION_FILE_BODY_CAP",
    "DocumentResolver",
    "ResolvedFile",
    "build_annotation_context",
    "build_importance_lookup",
    "clean_pdf_text",
    "collect_source_ids",
]
