"""Pydantic mirrors of the dialog-flow export shapes node-lab actually reads.

Deliberately partial: only the fields the distilled reasoning node touches are
modelled. Everything else on a node's `config` is preserved verbatim in
`extra` so `node_lab list` can show it and transcripts stay faithful, but it is
never interpreted.

SOURCE (shapes): packages/core/src/dialog-flow/nodes/configs/reasoning-node.config.ts
SOURCE (export): apps/frontend/src/feature/dialog-flow-canvas/lib/dialog-flow-save.ts
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class FactDataType(str, Enum):
    """SOURCE: packages/core/src/dialog-flow/dialog-flow.enum.ts :: DIALOG_FLOW_NODE_DATA_TYPE_ENUM"""

    TEXT = "text"
    NUMBER = "number"
    PERCENTAGE = "percentage"
    CONFIDENCE = "confidence"
    DATE = "date"
    BOOLEAN = "boolean"
    DOCUMENT_UPLOADED = "document_uploaded"
    CUSTOM = "custom"


class SourceType(str, Enum):
    """SOURCE: packages/core/src/dialog-flow/nodes/configs/reasoning-node.config.ts :: SourceType"""

    FILE = "file"
    EXCERPT = "excerpt"


class SourceImportance(str, Enum):
    """SOURCE: packages/core/src/dialog-flow/nodes/configs/reasoning-node.config.ts :: SourceImportance"""

    AUTHORITATIVE = "authoritative"
    ILLUSTRATIVE = "illustrative"


class NodeType(str, Enum):
    REASONING = "reasoning"
    START = "start"
    FACT = "fact"
    SWITCH = "switch"
    OUTCOME = "outcome"


class AnnotationSource(BaseModel):
    """One `{id, type, importance}` entry under `annotations[].sources[]`.

    Shape confirmed against
    apps/backend/src/node-execution/runners/__tests__/annotation-utils.spec.ts.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    type: SourceType
    # Missing importance falls back to AUTHORITATIVE, matching
    # buildAnnotationImportanceLookup — annotation sources are never silently
    # downgraded.
    importance: SourceImportance = SourceImportance.AUTHORITATIVE


class Annotation(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    sources: list[AnnotationSource] = Field(default_factory=list)


class VectorSearchConfig(BaseModel):
    """SOURCE: apps/backend/src/node (VectorSearchConfig).

    `documentScopes` is the load-bearing field: undefined or `[]` means
    retrieval is DISABLED (see tools/rag_search.derive_scope), never a widened
    default.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    enabled: bool = False
    document_scopes: list[Literal["client", "public"]] | None = Field(
        default=None, alias="documentScopes"
    )
    filters: Any | None = None


class ReasoningNodeConfig(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    question: str = ""
    instructions: str = ""
    instructions_tip_tap: Any | None = Field(default=None, alias="instructionsTipTap")
    annotations: list[Annotation] = Field(default_factory=list)
    data_type: FactDataType = Field(default=FactDataType.TEXT, alias="dataType")
    custom_enum_values: list[str] | None = Field(default=None, alias="customEnumValues")
    child_node_ids: list[str] = Field(default_factory=list, alias="childNodeIds")
    vector_search_config: VectorSearchConfig | None = Field(
        default=None, alias="vectorSearchConfig"
    )


class FlowNodeData(BaseModel):
    model_config = ConfigDict(extra="allow")

    label: str = ""
    # Left as a raw dict: only reasoning nodes get parsed into
    # ReasoningNodeConfig, and only when we are about to run them.
    config: dict[str, Any] = Field(default_factory=dict)


class FlowNode(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    type: str
    data: FlowNodeData = Field(default_factory=FlowNodeData)

    @property
    def label(self) -> str:
        return self.data.label

    def reasoning_config(self) -> ReasoningNodeConfig:
        return ReasoningNodeConfig.model_validate(self.data.config)


class FlowEdge(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = ""
    source: str
    target: str
    # Only carries a branch id when the source is a *switch* node; reasoning
    # sources have plain outgoing edges. Switch runners are out of scope, so we
    # read this for display only.
    source_handle: str | None = Field(default=None, alias="sourceHandle")


class DialogFlowMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = ""
    visibility: str = ""


class FlowExport(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: Any | None = None
    exported_at: Any | None = Field(default=None, alias="exportedAt")
    exported_by_user_id: str | None = Field(default=None, alias="exportedByUserId")
    dialog_flow: DialogFlowMeta = Field(
        default_factory=DialogFlowMeta, alias="dialogFlow"
    )
    nodes: list[FlowNode] = Field(default_factory=list)
    edges: list[FlowEdge] = Field(default_factory=list)


class PriorAnswer(BaseModel):
    """One entry in the answers dict handed down to children.

    This is the whole replacement for the production ContextPool /
    FactDictionary. Field names mirror `FactDictionary` entries so
    `format_prior_answers` can be a byte-faithful port of
    `formatFactDictionary` (apps/backend/src/prompt/prompt.utils.ts).
    """

    label: str
    prediction: str
    rationale: str | None = None
    source: str | None = None


class RagHit(BaseModel):
    """One deduped, file-level RAG hit. Mirrors `RagSearchHit`."""

    file_id: str
    name: str
    score: float
    snippet: str | None = None


class AnnotationFile(BaseModel):
    file_id: str
    file_name: str
    #: Body rendered into <Annotated_Context>. See prompts.reasoning_node for
    #: why this carries full text rather than the metadata summary.
    summary: str
    source_type: SourceImportance


class AnnotationExcerpt(BaseModel):
    id: str
    title: str
    text: str
    source_type: SourceImportance
    pinpoint: str | None = None


class AnnotationContext(BaseModel):
    files: list[AnnotationFile] = Field(default_factory=list)
    excerpts: list[AnnotationExcerpt] = Field(default_factory=list)


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0

    def add(self, other: "TokenUsage | None") -> "TokenUsage":
        if other is None:
            return self
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
        )


class PredictionCandidate(BaseModel):
    prediction: str
    probability: float


__all__ = [
    "Annotation",
    "AnnotationContext",
    "AnnotationExcerpt",
    "AnnotationFile",
    "AnnotationSource",
    "DialogFlowMeta",
    "FactDataType",
    "FlowEdge",
    "FlowExport",
    "FlowNode",
    "FlowNodeData",
    "NodeType",
    "PredictionCandidate",
    "PriorAnswer",
    "RagHit",
    "ReasoningNodeConfig",
    "SourceImportance",
    "SourceType",
    "TokenUsage",
    "VectorSearchConfig",
]
