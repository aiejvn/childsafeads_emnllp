"""SOURCE: apps/backend/src/prompt/context-file-format.ts

Canonical rendering for a file reference injected into an LLM prompt. Ported
function-for-function: the assembled string is what must match, not just the
prompt constants.
"""

from __future__ import annotations


def format_context_file_entry(
    *,
    file_id: str,
    name: str,
    body: str,
    body_label: str = "summary",
    meta: str | None = None,
) -> str:
    """Render one file entry as::

        - fileId=<id> name="<name>"[ <meta>]
            <bodyLabel>: <body>
    """
    meta_part = f" {meta}" if meta else ""
    return f'- fileId={file_id} name="{name}"{meta_part}\n    {body_label}: {body}'


__all__ = ["format_context_file_entry"]
