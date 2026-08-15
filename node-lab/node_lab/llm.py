"""Raw-API LLM layer mirroring `packages/ai/src/client.ts` semantics.

The point of node-lab is fidelity to the TS client's *behaviour*, not to its
implementation, so this module re-creates the handful of things the Vercel AI
SDK does implicitly:

  * step budget            -> client.ts:105  (`hasTools ? 10 : 2`)
  * structured output      -> client.ts:110-118 (`Output.object`)
  * prompt-cache breakpoint-> packages/ai/src/cache.ts:29 (ephemeral, ttl 1h)
  * 429 backoff            -> packages/ai/src/retry.ts:17-21 (4 / 1000ms / x3)

Providers: Anthropic and OpenAI. Bedrock model ids are recognised by the
registry but rejected at call time — a lab run has no AWS credential path.
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import re
import threading
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from .types import TokenUsage

# ============================================
# Model registry
# ============================================

Provider = Literal["anthropic", "openai", "bedrock"]

# SOURCE: packages/ai/src/models.ts :: MODEL_REGISTRY
MODEL_REGISTRY: dict[str, tuple[Provider, str]] = {
    # Anthropic (direct API)
    "claude-opus-4-7": ("anthropic", "claude-opus-4-7"),
    "claude-opus-4-6": ("anthropic", "claude-opus-4-6"),
    "claude-sonnet-4-6": ("anthropic", "claude-sonnet-4-6"),
    "claude-haiku-4-5": ("anthropic", "claude-haiku-4-5-20251001"),
    # OpenAI
    "gpt-5.4": ("openai", "gpt-5.4"),
    "gpt-5.4-mini": ("openai", "gpt-5.4-mini"),
    "gpt-5.4-nano": ("openai", "gpt-5.4-nano"),
    "gpt-4o-mini": ("openai", "gpt-4o-mini"),
    # Bedrock — listed so `--model` validation gives a useful error rather than
    # "unknown model"; calling one raises.
    "bedrock-claude-opus-4-7": ("bedrock", "us.anthropic.claude-opus-4-7"),
    "bedrock-claude-opus-4-6": ("bedrock", "us.anthropic.claude-opus-4-6-v1"),
    "bedrock-claude-sonnet-4-6": ("bedrock", "us.anthropic.claude-sonnet-4-6"),
    "bedrock-claude-haiku-4-5": (
        "bedrock",
        "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    ),
    "bedrock-mistral-large": ("bedrock", "mistral.mistral-large-3-675b-instruct"),
    "bedrock-minimax-m2.5": ("bedrock", "minimax.minimax-m2.5"),
    "bedrock-kimi-k2.5": ("bedrock", "moonshotai.kimi-k2.5"),
}

# SOURCE: packages/core/src/llm/index.constant.ts :: UTILITY_MODEL
UTILITY_MODEL = "gpt-5.4-nano"

DEFAULT_MODEL = "claude-sonnet-4-6"


def resolve_provider(model: str) -> Provider:
    entry = MODEL_REGISTRY.get(model)
    if entry is None:
        raise ValueError(f"Unknown model ID: {model}")
    return entry[0]


# ============================================
# Retry — packages/ai/src/retry.ts
# ============================================

MAX_RETRIES = 4
BASE_DELAY_MS = 1000
BACKOFF_MULTIPLIER = 3


def _is_rate_limit_error(error: BaseException) -> bool:
    """Provider-agnostic 429 detection, mirroring `isRateLimitError`."""
    status = getattr(error, "status_code", None) or getattr(error, "status", None)
    if status == 429:
        return True
    cause = error.__cause__
    while cause is not None:
        c_status = getattr(cause, "status_code", None) or getattr(cause, "status", None)
        if c_status == 429:
            return True
        cause = cause.__cause__
    message = str(error)
    return "429" in message and re.search(r"rate.?limit", message, re.I) is not None


def _add_jitter(delay_ms: float) -> float:
    """+/-25%, same band as `addJitter`."""
    return delay_ms * (0.75 + random.random() * 0.5)


async def _with_rate_limit_retry(fn: Callable[[], Awaitable[Any]]) -> Any:
    last: BaseException | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return await fn()
        except Exception as error:  # noqa: BLE001 — re-raised below
            if not _is_rate_limit_error(error):
                raise
            last = error
            if attempt < MAX_RETRIES:
                delay = BASE_DELAY_MS * (BACKOFF_MULTIPLIER**attempt)
                await asyncio.sleep(_add_jitter(delay) / 1000)
    assert last is not None
    raise last


# ============================================
# Messages, tools, results
# ============================================


@dataclass
class SystemMessage:
    content: str
    #: True marks an Anthropic ephemeral cache breakpoint. Only worth setting
    #: on LARGE, byte-identical, module-level constants.
    cached: bool = False


def cached_system_message(content: str) -> SystemMessage:
    """SOURCE: packages/ai/src/cache.ts :: cachedSystemMessage

    The 1-hour TTL is part of the contract, not a tuning knob: flow runs are
    often spaced further apart than the 5-minute default and the 1h break-even
    (3 reads) is reliably cleared across a node's analysis + reflection calls.
    No-op on OpenAI.
    """
    return SystemMessage(content=content, cached=True)


@dataclass
class ToolSpec:
    name: str
    description: str
    #: JSON Schema for the tool input.
    input_schema: dict[str, Any]
    execute: Callable[[dict[str, Any]], Awaitable[str]]


@dataclass
class ToolExecution:
    tool_name: str
    args: dict[str, Any]
    result: str


@dataclass
class GenerateConfig:
    """SOURCE: packages/ai/src/types.ts :: ClientConfig"""

    temperature: float | None = 0
    max_output_tokens: int | None = None
    #: OpenAI GPT-5-class reasoning effort. On those models the AI SDK silently
    #: drops `temperature` unless this is "none"; we mirror that below.
    reasoning_effort: Literal["none", "low", "medium", "high", "xhigh"] | None = None


@dataclass
class GenerateResult:
    text: str = ""
    object: dict[str, Any] | None = None
    usage: TokenUsage = field(default_factory=TokenUsage)
    steps: int = 0
    tool_executions: list[ToolExecution] = field(default_factory=list)
    #: True when the loop hit its step budget before the model produced a final
    #: answer. Verification asserts this stays False on normal runs.
    hit_step_cap: bool = False
    aborted: bool = False


class Aborted(Exception):
    pass


# `abortSignal` -> a plain threading.Event; no NodeExecutionContext port.
AbortSignal = threading.Event

ANTHROPIC_EXTENDED_CACHE_TTL_BETA = "extended-cache-ttl-2025-04-11"
ANTHROPIC_STRUCTURED_OUTPUTS_BETA = "structured-outputs-2025-11-13"

# Default output tokens. The AI SDK leaves this to the provider; Anthropic's
# Messages API requires an explicit value, so pick one large enough for a full
# rationale.
DEFAULT_MAX_OUTPUT_TOKENS = 16000


class LLMClient:
    """Async client over the Anthropic and OpenAI SDKs.

    `structured_mode` selects how the final structured object is produced:

      * "native" — provider-native structured output. This is what
        `Output.object({schema, name, description})` compiles to
        (client.ts:110-118): OpenAI `response_format.json_schema`, Anthropic
        `output_config.format.json_schema`. Preferred, and the default.
      * "tool"   — a schema-shaped tool the model calls to finish. Used as an
        automatic fallback when the installed SDK / API version rejects
        `output_config`, so an older `anthropic` package still runs.

    The AI SDK hides this choice entirely; recreating it explicitly is the one
    place node-lab must reproduce SDK behaviour rather than call semantics.
    """

    def __init__(
        self,
        *,
        anthropic_api_key: str | None = None,
        openai_api_key: str | None = None,
        structured_mode: Literal["native", "tool", "auto"] = "auto",
    ) -> None:
        self._anthropic_api_key = anthropic_api_key or os.environ.get(
            "ANTHROPIC_API_KEY"
        )
        self._openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self._structured_mode = structured_mode
        self._anthropic: Any = None
        self._openai: Any = None

    # -- provider handles -------------------------------------------------

    def _anthropic_client(self) -> Any:
        if self._anthropic is None:
            if not self._anthropic_api_key:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY is not set — required for claude-* models."
                )
            from anthropic import AsyncAnthropic

            self._anthropic = AsyncAnthropic(api_key=self._anthropic_api_key)
        return self._anthropic

    def _openai_client(self) -> Any:
        if self._openai is None:
            if not self._openai_api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY is not set — required for gpt-* models."
                )
            from openai import AsyncOpenAI

            self._openai = AsyncOpenAI(api_key=self._openai_api_key)
        return self._openai

    # -- public API -------------------------------------------------------

    async def generate_object(
        self,
        *,
        model: str,
        system: SystemMessage | str,
        prompt: str,
        schema: dict[str, Any],
        schema_name: str,
        schema_description: str = "",
        tools: Sequence[ToolSpec] | None = None,
        config: GenerateConfig | None = None,
        abort_signal: AbortSignal | None = None,
    ) -> GenerateResult:
        # SOURCE: client.ts:105 — `const maxSteps = hasTools ? 10 : 2`.
        # The 15 belongs to generate_text (client.ts:425); do not conflate.
        max_steps = 10 if tools else 2
        return await self._run(
            model=model,
            system=system,
            prompt=prompt,
            tools=tools or [],
            config=config or GenerateConfig(),
            max_steps=max_steps,
            abort_signal=abort_signal,
            schema=schema,
            schema_name=schema_name,
            schema_description=schema_description,
        )

    async def generate_text(
        self,
        *,
        model: str,
        system: SystemMessage | str,
        prompt: str,
        tools: Sequence[ToolSpec] | None = None,
        config: GenerateConfig | None = None,
        max_steps: int = 15,  # SOURCE: client.ts:425 — `options.maxSteps ?? 15`
        abort_signal: AbortSignal | None = None,
    ) -> GenerateResult:
        return await self._run(
            model=model,
            system=system,
            prompt=prompt,
            tools=tools or [],
            config=config or GenerateConfig(),
            max_steps=max_steps,
            abort_signal=abort_signal,
            schema=None,
            schema_name="",
            schema_description="",
        )

    # -- dispatch ---------------------------------------------------------

    async def _run(self, **kw: Any) -> GenerateResult:
        provider = resolve_provider(kw["model"])
        if provider == "anthropic":
            return await self._run_anthropic(**kw)
        if provider == "openai":
            return await self._run_openai(**kw)
        raise RuntimeError(
            f"Provider '{provider}' is not supported by node-lab "
            f"(model {kw['model']!r}). Use a claude-* or gpt-* model."
        )

    # -- shared helpers ---------------------------------------------------

    @staticmethod
    def _check_abort(signal: AbortSignal | None) -> None:
        if signal is not None and signal.is_set():
            raise Aborted()

    @staticmethod
    def _system_text(system: SystemMessage | str) -> SystemMessage:
        return system if isinstance(system, SystemMessage) else SystemMessage(system)

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any] | None:
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None
        return parsed if isinstance(parsed, dict) else None

    # -- Anthropic --------------------------------------------------------

    async def _run_anthropic(
        self,
        *,
        model: str,
        system: SystemMessage | str,
        prompt: str,
        tools: Sequence[ToolSpec],
        config: GenerateConfig,
        max_steps: int,
        abort_signal: AbortSignal | None,
        schema: dict[str, Any] | None,
        schema_name: str,
        schema_description: str,
    ) -> GenerateResult:
        client = self._anthropic_client()
        _, provider_model_id = MODEL_REGISTRY[model]
        sys_msg = self._system_text(system)

        system_blocks: list[dict[str, Any]] = [{"type": "text", "text": sys_msg.content}]
        if sys_msg.cached:
            system_blocks[0]["cache_control"] = {"type": "ephemeral", "ttl": "1h"}

        betas: list[str] = []
        if sys_msg.cached:
            betas.append(ANTHROPIC_EXTENDED_CACHE_TTL_BETA)

        use_native = schema is not None and self._structured_mode in ("native", "auto")
        tool_defs = [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in tools
        ]
        if schema is not None and not use_native:
            tool_defs.append(
                {
                    "name": schema_name,
                    "description": schema_description
                    or "Return the final structured result.",
                    "input_schema": schema,
                }
            )

        messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        result = GenerateResult()
        by_name = {t.name: t for t in tools}

        for step in range(max_steps):
            self._check_abort(abort_signal)
            result.steps = step + 1

            kwargs: dict[str, Any] = {
                "model": provider_model_id,
                "system": system_blocks,
                "messages": messages,
                "max_tokens": config.max_output_tokens or DEFAULT_MAX_OUTPUT_TOKENS,
            }
            if config.temperature is not None:
                kwargs["temperature"] = config.temperature
            if tool_defs:
                kwargs["tools"] = tool_defs
            if use_native:
                kwargs["output_config"] = {
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "schema": schema,
                    }
                }

            local_betas = list(betas)
            if use_native:
                local_betas.append(ANTHROPIC_STRUCTURED_OUTPUTS_BETA)

            async def call() -> Any:
                target = client.beta.messages if local_betas else client.messages
                extra = {"betas": local_betas} if local_betas else {}
                return await target.create(**kwargs, **extra)

            try:
                response = await _with_rate_limit_retry(call)
            except Exception as error:  # noqa: BLE001
                if (
                    use_native
                    # Only "auto" degrades. An explicit `--structured-output
                    # native` must fail loudly rather than silently changing
                    # how the final object is produced.
                    and self._structured_mode == "auto"
                    and _is_unsupported_param(error, "output_config")
                ):
                    # Installed SDK / API version predates provider-native
                    # structured output. Fall back to the schema-shaped tool
                    # for the rest of the process, and retry from the top.
                    self._structured_mode = "tool"
                    return await self._run_anthropic(
                        model=model,
                        system=system,
                        prompt=prompt,
                        tools=tools,
                        config=config,
                        max_steps=max_steps,
                        abort_signal=abort_signal,
                        schema=schema,
                        schema_name=schema_name,
                        schema_description=schema_description,
                    )
                raise

            usage = getattr(response, "usage", None)
            if usage is not None:
                result.usage = result.usage.add(
                    TokenUsage(
                        input_tokens=getattr(usage, "input_tokens", 0) or 0,
                        output_tokens=getattr(usage, "output_tokens", 0) or 0,
                    )
                )

            blocks = list(response.content)
            text = "".join(b.text for b in blocks if getattr(b, "type", "") == "text")
            tool_uses = [b for b in blocks if getattr(b, "type", "") == "tool_use"]

            # Schema-shaped-tool path: a call to the schema tool IS the answer.
            if schema is not None and not use_native:
                final = next((b for b in tool_uses if b.name == schema_name), None)
                if final is not None:
                    result.object = dict(final.input)
                    result.text = text
                    return result

            executable = [b for b in tool_uses if b.name in by_name]
            if not executable:
                result.text = text
                if schema is not None:
                    result.object = self._parse_json(text)
                    if result.object is None and not use_native:
                        # Model stopped without calling the schema tool. One
                        # forced extraction call, no user tools offered.
                        result.object = await self._anthropic_force_object(
                            client=client,
                            provider_model_id=provider_model_id,
                            system_blocks=system_blocks,
                            betas=betas,
                            messages=messages + [{"role": "assistant", "content": blocks}],
                            schema=schema,
                            schema_name=schema_name,
                            schema_description=schema_description,
                            config=config,
                            result=result,
                        )
                return result

            messages.append({"role": "assistant", "content": blocks})
            tool_results = []
            for block in executable:
                self._check_abort(abort_signal)
                args = dict(block.input)
                output = await by_name[block.name].execute(args)
                result.tool_executions.append(
                    ToolExecution(tool_name=block.name, args=args, result=output)
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                    }
                )
            messages.append({"role": "user", "content": tool_results})

        result.hit_step_cap = True
        return result

    async def _anthropic_force_object(
        self,
        *,
        client: Any,
        provider_model_id: str,
        system_blocks: list[dict[str, Any]],
        betas: list[str],
        messages: list[dict[str, Any]],
        schema: dict[str, Any],
        schema_name: str,
        schema_description: str,
        config: GenerateConfig,
        result: GenerateResult,
    ) -> dict[str, Any] | None:
        kwargs: dict[str, Any] = {
            "model": provider_model_id,
            "system": system_blocks,
            "messages": messages
            + [
                {
                    "role": "user",
                    "content": f"Return the final result by calling `{schema_name}`.",
                }
            ],
            "max_tokens": config.max_output_tokens or DEFAULT_MAX_OUTPUT_TOKENS,
            "tools": [
                {
                    "name": schema_name,
                    "description": schema_description
                    or "Return the final structured result.",
                    "input_schema": schema,
                }
            ],
            "tool_choice": {"type": "tool", "name": schema_name},
        }

        async def call() -> Any:
            target = client.beta.messages if betas else client.messages
            extra = {"betas": betas} if betas else {}
            return await target.create(**kwargs, **extra)

        response = await _with_rate_limit_retry(call)
        usage = getattr(response, "usage", None)
        if usage is not None:
            result.usage = result.usage.add(
                TokenUsage(
                    input_tokens=getattr(usage, "input_tokens", 0) or 0,
                    output_tokens=getattr(usage, "output_tokens", 0) or 0,
                )
            )
        for block in response.content:
            if getattr(block, "type", "") == "tool_use" and block.name == schema_name:
                return dict(block.input)
        return None

    # -- OpenAI -----------------------------------------------------------

    async def _run_openai(
        self,
        *,
        model: str,
        system: SystemMessage | str,
        prompt: str,
        tools: Sequence[ToolSpec],
        config: GenerateConfig,
        max_steps: int,
        abort_signal: AbortSignal | None,
        schema: dict[str, Any] | None,
        schema_name: str,
        schema_description: str,
    ) -> GenerateResult:
        client = self._openai_client()
        _, provider_model_id = MODEL_REGISTRY[model]
        sys_msg = self._system_text(system)

        # The `anthropic` cache breakpoint is a no-op here, exactly as the
        # provider option is ignored on non-Anthropic providers in the TS.
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": sys_msg.content},
            {"role": "user", "content": prompt},
        ]

        tool_defs = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.input_schema,
                },
            }
            for t in tools
        ]
        by_name = {t.name: t for t in tools}
        result = GenerateResult()

        for step in range(max_steps):
            self._check_abort(abort_signal)
            result.steps = step + 1

            kwargs: dict[str, Any] = {
                "model": provider_model_id,
                "messages": messages,
            }
            if config.reasoning_effort is not None:
                kwargs["reasoning_effort"] = config.reasoning_effort
            # Mirror the AI SDK: `temperature` is dropped on GPT-5 reasoning
            # models unless reasoningEffort is "none" (intentional API
            # behaviour, see synthesis-pipeline.ts).
            if config.temperature is not None and config.reasoning_effort in (
                None,
                "none",
            ):
                kwargs["temperature"] = config.temperature
            if config.max_output_tokens is not None:
                kwargs["max_completion_tokens"] = config.max_output_tokens
            if tool_defs:
                kwargs["tools"] = tool_defs
            if schema is not None:
                kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "description": schema_description,
                        "schema": schema,
                        "strict": True,
                    },
                }

            response = await _with_rate_limit_retry(
                lambda: client.chat.completions.create(**kwargs)
            )

            usage = getattr(response, "usage", None)
            if usage is not None:
                result.usage = result.usage.add(
                    TokenUsage(
                        input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                        output_tokens=getattr(usage, "completion_tokens", 0) or 0,
                    )
                )

            message = response.choices[0].message
            calls = [c for c in (message.tool_calls or []) if c.function.name in by_name]

            if not calls:
                result.text = message.content or ""
                if schema is not None:
                    result.object = self._parse_json(result.text)
                return result

            messages.append(message.model_dump(exclude_none=True))
            for call in calls:
                self._check_abort(abort_signal)
                args = self._parse_json(call.function.arguments) or {}
                output = await by_name[call.function.name].execute(args)
                result.tool_executions.append(
                    ToolExecution(
                        tool_name=call.function.name, args=args, result=output
                    )
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": output,
                    }
                )

        result.hit_step_cap = True
        return result


def _is_unsupported_param(error: BaseException, param: str) -> bool:
    """True when the SDK/API rejected `param` as unknown (vs. a real failure)."""
    if isinstance(error, TypeError) and param in str(error):
        return True
    message = str(error).lower()
    return param in message and any(
        marker in message
        for marker in ("unexpected", "unknown", "unsupported", "not permitted", "extra")
    )


__all__ = [
    "Aborted",
    "AbortSignal",
    "DEFAULT_MODEL",
    "GenerateConfig",
    "GenerateResult",
    "LLMClient",
    "MODEL_REGISTRY",
    "SystemMessage",
    "ToolExecution",
    "ToolSpec",
    "UTILITY_MODEL",
    "cached_system_message",
    "resolve_provider",
]
