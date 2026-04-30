import json
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from pydantic import BaseModel

from attestloop.schemas import LLMCallLog

# USD per million tokens. Public list prices for the named model identifiers.
MODEL_PRICING: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
}

# Assumption: 60 s timeout is per HTTP call to Anthropic; one retry on transient
# errors (timeout, rate limit, 5xx) covers the common flake without masking real
# failures. Non-transient errors (400, auth, schema) raise immediately.
_TIMEOUT_SECONDS = 60.0
_TRANSIENT_EXCEPTIONS = (
    anthropic.APITimeoutError,
    anthropic.APIConnectionError,
    anthropic.RateLimitError,
    anthropic.InternalServerError,
)


def _cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model)
    if pricing is None:
        # Assumption: unknown model means we still log the call but charge $0
        # rather than crash the run. Surfaces as a 0-cost row in the report.
        return 0.0
    return (
        input_tokens * pricing["input"] / 1_000_000.0
        + output_tokens * pricing["output"] / 1_000_000.0
    )


def _append_log(run_dir: Path, agent: str, entry: LLMCallLog) -> None:
    log_path = run_dir / f"{agent}.json"
    if log_path.exists():
        existing = json.loads(log_path.read_text())
    else:
        existing = []
    existing.append(json.loads(entry.model_dump_json()))
    log_path.write_text(json.dumps(existing, indent=2))


def call_with_logging(
    *,
    agent: str,
    model: str,
    system_prompt: str,
    user_message: str,
    output_schema: type[BaseModel],
    run_dir: Path,
    prompt_version: str,
    metadata_factory: Callable[[BaseModel], dict[str, int | float | str]] | None = None,
) -> BaseModel:
    """Call Claude with a single tool whose schema matches output_schema, and
    log the call to run_dir/<agent>.json. If metadata_factory is provided, it
    is called with the parsed result and its return value is recorded on the
    LLMCallLog's metadata field."""

    tool_name = output_schema.__name__
    tool = {
        "name": tool_name,
        "description": (
            f"Return the structured {tool_name} for this agent. Always call "
            "this tool exactly once. Do not return free-form text."
        ),
        "input_schema": output_schema.model_json_schema(),
    }

    client = anthropic.Anthropic(timeout=_TIMEOUT_SECONDS)
    started_at = datetime.now(timezone.utc)
    t0 = time.perf_counter()

    last_err: Exception | None = None
    response = None
    for attempt in range(2):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=8192,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                tools=[tool],
                tool_choice={"type": "tool", "name": tool_name},
            )
            break
        except _TRANSIENT_EXCEPTIONS as e:
            last_err = e
            if attempt == 0:
                continue
            raise
    if response is None:
        # Defensive: loop above either sets response or re-raises. This branch
        # only runs if the exception types change underneath us.
        raise RuntimeError(f"LLM call failed without response: {last_err!r}")

    latency_ms = int((time.perf_counter() - t0) * 1000)

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_block is None:
        raise RuntimeError(
            f"{agent}: model did not call the {tool_name} tool; stop_reason="
            f"{response.stop_reason!r}"
        )

    parsed = output_schema.model_validate(tool_block.input)

    metadata: dict[str, int | float | str] | None = None
    if metadata_factory is not None:
        try:
            metadata = metadata_factory(parsed)
        except Exception:
            # Observability is best-effort; don't fail the call over a metadata bug.
            metadata = None

    log_entry = LLMCallLog(
        agent=agent,
        model=model,
        prompt_version=prompt_version,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        cost_usd=_cost_usd(
            model, response.usage.input_tokens, response.usage.output_tokens
        ),
        latency_ms=latency_ms,
        started_at=started_at,
        prompt=f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_message}",
        response=json.dumps(tool_block.input, ensure_ascii=False),
        metadata=metadata,
    )
    _append_log(run_dir, agent, log_entry)

    return parsed
