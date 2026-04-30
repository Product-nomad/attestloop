"""Mapper agent — v6 task 4 parallel execution.

The Mapper makes one Anthropic call per obligation. v1 ran them
sequentially: 71 obligations × ~11 s/call ≈ 13 min wall-clock. v6
introduces in-agent parallelism — the public sync entrypoint
`map_to_controls` is unchanged, but internally it now runs an async
implementation that fans out 8 calls at a time via a semaphore. With
prompt caching on the controls list (unchanged from v4), the wall-clock
target is ~2 min and total cost is identical within stochastic noise.

Concurrency is bounded inside the agent rather than via LangGraph's
Send / fan-out edges. The graph still shows one Mapper node; the
parallelism is implementation detail. Disk-write race conditions are
avoided by buffering LLMCallLog entries in memory under an asyncio.Lock
and writing the full mapper.json once after asyncio.gather completes.
Per-call failures are caught with `return_exceptions=True` and surfaced
as MapperFailure entries — the audit trail records what errored, the
other 70 calls still produce mappings.
"""
import asyncio
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import anthropic
from anthropic import AsyncAnthropic
from rich.console import Console

from attestloop.llm import (
    MODEL_PRICING,  # noqa: F401  — re-exported for tests / consistency
    _RATE_LIMIT_BACKOFF_SECONDS,
    _RATE_LIMIT_MAX_ATTEMPTS,
    _TIMEOUT_SECONDS,
    _cost_usd,
    _flatten_text,
)
from attestloop.registry import Framework
from attestloop.schemas import (
    Control,
    ControlMapping,
    LLMCallLog,
    MapperFailure,
    MapperInput,
    MapperOutput,
    Obligation,
)

_MODEL = "claude-sonnet-4-6"

# Conservative concurrency cap. Anthropic's per-minute output-token
# limit (~80 K on Sonnet tier 2) and per-minute input-token limit
# (~30 K — but cache reads don't count against it) both constrain how
# fast we can fan out. 8-way is comfortably under both at typical
# Mapper call shapes (~150 output tokens, ~300 uncached input tokens
# per call). Tested up to 12-way without rate-limit issues; cache hit
# rate degrades slightly above 8. Adjustable.
MAPPER_CONCURRENCY = 8

_CONTROLS_HEADER = (
    "## Allowed control catalogue (the only IDs you may return)\n"
    "Each entry is one NIST AI RMF 1.0 subcategory. JSON below.\n"
)

_FAST_RETRY_EXCEPTIONS = (
    anthropic.APITimeoutError,
    anthropic.APIConnectionError,
    anthropic.InternalServerError,
)

_console = Console()


def _format_controls(controls: list[Control]) -> str:
    rows = [
        {
            "id": c.id,
            "function": c.function,
            "category": c.category,
            "subcategory_text": c.subcategory_text,
        }
        for c in controls
    ]
    return json.dumps(rows, indent=2)


def _build_user_message(obligation: Obligation, framework_id: str) -> str:
    return (
        f"Framework: {framework_id}\n\n"
        "--- OBLIGATION ---\n"
        f"{obligation.model_dump_json(indent=2)}\n"
        "--- END ---"
    )


def _build_cached_system_blocks(framework: Framework) -> tuple[list[dict], str]:
    """Construct the cached system block (prompt + controls catalogue).
    Returns (system_blocks, prompt_version_sha256). Identical across all
    Mapper calls in a run, which is what makes prompt caching work."""
    system_prompt_text = framework.mapper_prompt_path.read_text()
    prompt_version = hashlib.sha256(system_prompt_text.encode("utf-8")).hexdigest()

    cached_system_text = (
        f"{system_prompt_text}\n\n"
        f"{_CONTROLS_HEADER}\n"
        f"{_format_controls(framework.controls)}\n"
    )
    blocks: list[dict] = [
        {
            "type": "text",
            "text": cached_system_text,
            "cache_control": {"type": "ephemeral"},
        }
    ]
    return blocks, prompt_version


class MapperCallBuffer:
    """Lock-protected in-memory buffer of LLMCallLog entries for the
    parallel Mapper. Avoids disk-write races between concurrent tasks;
    the buffered list is flushed to mapper.json in one write after
    asyncio.gather completes."""

    def __init__(self) -> None:
        self._calls: list[LLMCallLog] = []
        self._lock = asyncio.Lock()

    async def append(self, log: LLMCallLog) -> None:
        async with self._lock:
            self._calls.append(log)

    def all_calls(self) -> list[LLMCallLog]:
        return list(self._calls)


async def _call_mapper_async(
    obligation: Obligation,
    framework_id: str,
    system_blocks: list[dict],
    prompt_version: str,
    client: AsyncAnthropic,
    buffer: MapperCallBuffer,
) -> list[ControlMapping]:
    """Single async Mapper call. Same retry semantics as the shared
    sync wrapper (one fast retry + up to four 30 s rate-limit backoffs).
    Buffers the LLMCallLog instead of writing to disk."""

    user_message = _build_user_message(obligation, framework_id)
    tool_name = MapperOutput.__name__
    tool = {
        "name": tool_name,
        "description": (
            f"Return the structured {tool_name} for this agent. Always call "
            "this tool exactly once. Do not return free-form text."
        ),
        "input_schema": MapperOutput.model_json_schema(),
    }

    started_at = datetime.now(timezone.utc)
    t0 = time.perf_counter()

    last_err: Exception | None = None
    response = None
    fast_retry_used = False
    rate_limit_attempts = 0

    while True:
        try:
            response = await client.messages.create(
                model=_MODEL,
                max_tokens=8192,
                system=system_blocks,
                messages=[{"role": "user", "content": user_message}],
                tools=[tool],
                tool_choice={"type": "tool", "name": tool_name},
            )
            break
        except anthropic.RateLimitError as e:
            last_err = e
            rate_limit_attempts += 1
            if rate_limit_attempts >= _RATE_LIMIT_MAX_ATTEMPTS:
                raise
            await asyncio.sleep(_RATE_LIMIT_BACKOFF_SECONDS)
            continue
        except _FAST_RETRY_EXCEPTIONS as e:
            last_err = e
            if fast_retry_used:
                raise
            fast_retry_used = True
            continue

    if response is None:
        raise RuntimeError(f"LLM call failed without response: {last_err!r}")

    latency_ms = int((time.perf_counter() - t0) * 1000)

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_block is None:
        raise RuntimeError(
            f"mapper: model did not call the {tool_name} tool; "
            f"stop_reason={response.stop_reason!r}"
        )

    parsed = MapperOutput.model_validate(tool_block.input)

    cache_creation = getattr(response.usage, "cache_creation_input_tokens", None) or 0
    cache_read = getattr(response.usage, "cache_read_input_tokens", None) or 0

    log_entry = LLMCallLog(
        agent="mapper",
        model=_MODEL,
        prompt_version=prompt_version,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        cost_usd=_cost_usd(
            _MODEL,
            response.usage.input_tokens,
            response.usage.output_tokens,
            cache_creation,
            cache_read,
        ),
        latency_ms=latency_ms,
        started_at=started_at,
        prompt=(
            f"SYSTEM:\n{_flatten_text(system_blocks)}\n\n"
            f"USER:\n{user_message}"
        ),
        response=json.dumps(tool_block.input, ensure_ascii=False),
        metadata={
            "obligation_id": obligation.id,
            "returned_mapping_count": len(parsed.mappings),
        },
        cache_creation_input_tokens=cache_creation,
        cache_read_input_tokens=cache_read,
    )
    await buffer.append(log_entry)

    return parsed.mappings


async def _map_one_obligation(
    obligation: Obligation,
    framework: Framework,
    framework_id: str,
    system_blocks: list[dict],
    prompt_version: str,
    client: AsyncAnthropic,
    semaphore: asyncio.Semaphore,
    buffer: MapperCallBuffer,
    valid_ids: set[str],
) -> tuple[Obligation, list[ControlMapping] | Exception]:
    """Wrap a single Mapper call in the concurrency semaphore and the
    same control-id / obligation-id validation the sync version applied.
    Catches all exceptions so one obligation's permanent failure doesn't
    poison the asyncio.gather batch."""
    async with semaphore:
        try:
            mappings = await _call_mapper_async(
                obligation,
                framework_id,
                system_blocks,
                prompt_version,
                client,
                buffer,
            )
        except Exception as e:  # noqa: BLE001 — surface every failure type
            return (obligation, e)

        kept: list[ControlMapping] = []
        for m in mappings:
            if m.control_id not in valid_ids:
                _console.print(
                    f"[yellow]mapper: discarding unknown control_id "
                    f"'{m.control_id}' for obligation "
                    f"'{obligation.id}'.[/yellow]"
                )
                continue
            if m.obligation_id != obligation.id:
                # Defensive: the mapper sometimes echoes back a different
                # obligation_id; rebind to what we actually asked about.
                m = m.model_copy(update={"obligation_id": obligation.id})
            kept.append(m)

        if not kept:
            _console.print(
                f"[yellow]mapper: no high-confidence mapping for obligation "
                f"'{obligation.id}'; recorded as unmapped in the report.[/yellow]"
            )
        return (obligation, kept)


async def _map_to_controls_async(
    obligations: Sequence[Obligation],
    framework: Framework,
    framework_id: str,
    run_dir: Path,
    mapper_concurrency: int = MAPPER_CONCURRENCY,
) -> tuple[list[ControlMapping], list[MapperFailure]]:
    """Async fan-out implementation. Returns (mappings_in_input_order,
    failures). Writes the buffered call log to mapper.json on completion."""

    system_blocks, prompt_version = _build_cached_system_blocks(framework)
    valid_ids = {c.id for c in framework.controls}

    client = AsyncAnthropic(timeout=_TIMEOUT_SECONDS)
    semaphore = asyncio.Semaphore(mapper_concurrency)
    buffer = MapperCallBuffer()

    tasks = [
        _map_one_obligation(
            obligation=obl,
            framework=framework,
            framework_id=framework_id,
            system_blocks=system_blocks,
            prompt_version=prompt_version,
            client=client,
            semaphore=semaphore,
            buffer=buffer,
            valid_ids=valid_ids,
        )
        for obl in obligations
    ]

    _console.print(
        f"[cyan]mapper: dispatching {len(tasks)} obligations with "
        f"concurrency={mapper_concurrency}.[/cyan]"
    )

    results = await asyncio.gather(*tasks)

    # Flush the buffered LLMCallLog list to disk in one write — same
    # shape call_with_logging produces (a JSON list of LLMCallLog
    # entries) so report.aggregate_usage() picks up the costs unchanged.
    log_entries = buffer.all_calls()
    log_path = run_dir / "mapper.json"
    log_path.write_text(
        json.dumps(
            [json.loads(e.model_dump_json()) for e in log_entries],
            indent=2,
        )
    )

    # Reassemble in input order (obligations iteration order is preserved
    # by asyncio.gather's results), then surface failures separately.
    all_mappings: list[ControlMapping] = []
    failures: list[MapperFailure] = []
    for obligation, result in results:
        if isinstance(result, Exception):
            failures.append(
                MapperFailure(obligation_id=obligation.id, error=repr(result))
            )
        else:
            all_mappings.extend(result)

    # Stable secondary sort within each obligation: highest confidence
    # first. The primary order (obligation id, in input sequence) is
    # already preserved by the gather/iteration above; sorting by
    # obligation_id alphabetically would re-order across the input.
    # Use a dict to bucket per obligation, then flatten in input order.
    by_obligation: dict[str, list[ControlMapping]] = {}
    for m in all_mappings:
        by_obligation.setdefault(m.obligation_id, []).append(m)
    ordered: list[ControlMapping] = []
    for obl in obligations:
        bucket = by_obligation.get(obl.id, [])
        bucket.sort(key=lambda m: -m.confidence)
        ordered.extend(bucket)

    return ordered, failures


def map_to_controls(
    input: MapperInput,
    framework: Framework,
    run_dir: Path,
    *,
    mapper_concurrency: int = MAPPER_CONCURRENCY,
) -> MapperOutput:
    """Synchronous public entrypoint — keyword-only `mapper_concurrency`
    keeps the v5 (input, framework, run_dir) positional contract. Wraps
    the async fan-out implementation. Persists mapper_failures.json when
    any obligation errored permanently so the orchestration node can
    pull them onto PipelineState for the report."""
    mappings, failures = asyncio.run(
        _map_to_controls_async(
            input.obligations,
            framework,
            input.framework_id,
            run_dir,
            mapper_concurrency=mapper_concurrency,
        )
    )

    if failures:
        _console.print(
            f"[yellow]mapper: {len(failures)} obligation(s) failed permanently; "
            "recorded in mapper_failures.json.[/yellow]"
        )
        (run_dir / "mapper_failures.json").write_text(
            json.dumps(
                [json.loads(f.model_dump_json()) for f in failures],
                indent=2,
            )
        )

    return MapperOutput(mappings=mappings)
