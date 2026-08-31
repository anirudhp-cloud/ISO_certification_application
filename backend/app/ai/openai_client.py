# Wraps Azure OpenAI GPT-4.1 mini calls — JSON-mode, retries, prompt-caching setup.

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from openai import AzureOpenAI
from pydantic import ValidationError

from app.ai.cost_tracker import record_current
from app.ai.pricing import estimate_cost_usd
from app.ai.requirement_catalog import format_requirements_listing
from app.ai.schemas import CombinedEvaluation, MappingResult
from app.config import settings
from app.models.clause import Clause
from prompt_library import get_system_prompt
from prompt_library.reduce_prompt import REDUCE_SYSTEM_PROMPT, build_reduce_user_message

logger = logging.getLogger(f"iso_platform.{__name__}")
MAX_ATTEMPTS = 3

_client = AzureOpenAI(
    azure_endpoint=settings.llm_endpoint,
    api_key=settings.llm_api_key,
    api_version=settings.llm_api_version,
)

# Dev observability: every real map/reduce call dumps its exact prompt (line
# numbered, like `cat -n`) to the console AND to its own timestamped file, so
# you can see exactly what was sent while the app is actually running — not
# just the hardcoded-sample version in tests/test_print_full_prompt.py.
PROMPT_LOG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "prompt_logs"
_SAFE_LABEL_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def _numbered(text: str) -> str:
    lines = text.split("\n")
    width = len(str(len(lines)))
    return "\n".join(f"{i + 1:>{width}} | {line}" for i, line in enumerate(lines))


def _dump_prompt(label: str, system_prompt: str, user_message: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    safe_label = _SAFE_LABEL_RE.sub("_", label)[:80]
    full_text = "\n".join(
        [
            "=" * 100,
            f"SYSTEM MESSAGE (role: system) — {label} — {timestamp} UTC",
            "=" * 100,
            _numbered(system_prompt),
            "",
            "=" * 100,
            "USER MESSAGE (role: user)",
            "=" * 100,
            _numbered(user_message),
        ]
    )
    logger.info(full_text)  # console (via the logger's StreamHandler) + logs/app.log

    PROMPT_LOG_DIR.mkdir(exist_ok=True)
    (PROMPT_LOG_DIR / f"{timestamp}__{safe_label}.txt").write_text(full_text, encoding="utf-8")


def _dump_output(label: str, raw_response: str) -> None:
    try:
        pretty = json.dumps(json.loads(raw_response), indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        pretty = raw_response  # not valid JSON — log as-is so the bad response is still visible
    logger.info("\n".join(["=" * 100, f"LLM OUTPUT — {label}", "=" * 100, _numbered(pretty)]))


def _record_usage(label: str, response) -> None:
    """Pull token usage off the raw API response, price it, print a one-line
    summary, and — if this call happened inside a cost_tracker.tracking()
    block (i.e. a real Analyze request, not the ad-hoc test endpoint) —
    accumulate it into that request's running total."""
    usage = response.usage
    if usage is None:  # defensive — the API always returns this in practice
        return
    cached_tokens = getattr(getattr(usage, "prompt_tokens_details", None), "cached_tokens", 0) or 0
    cost_usd = estimate_cost_usd(usage.prompt_tokens, usage.completion_tokens, cached_tokens)

    logger.info(
        "COST — %s — prompt=%d (cached=%d) completion=%d total=%d tokens — $%.6f",
        label, usage.prompt_tokens, cached_tokens, usage.completion_tokens, usage.total_tokens, cost_usd,
    )
    record_current(label, usage.prompt_tokens, usage.completion_tokens, cached_tokens, cost_usd)


def get_control_mappings(
    standard_id: str,
    document_text: str,
    clauses: list[Clause],
    segment: str,
    *,
    label: str | None = None,
) -> tuple[MappingResult, str]:
    """
    Map one document's text against ONE segment of the given standard — either its
    mandatory clauses or its Annex A controls. Returns (result, prompt_version).

    `standard_id` is whatever the frontend sent (e.g. 'iso42001', 'iso27001',
    'iso9001') — resolving it to the right system prompt is delegated entirely
    to prompt_library.get_system_prompt, so this function never branches on
    the standard itself. `segment` is 'clause' or 'control'; the caller
    (app/ai/clause_mapper.py) runs one call per segment, because the two halves of
    the standard are different kinds of thing and mixing them meant the clause
    evaluation carried Annex B instructions that never applied to it.

    `clauses` must already be filtered to `segment`. Its
    title/description/evidence_requirements are what the LLM actually evaluates
    against, not whatever it happens to remember about the standard from training.
    Put in the SYSTEM message (not the user message) since it's identical for every
    document mapped in one Analyze run — this is the static prefix Azure OpenAI can
    cache across those repeated calls, and splitting into two segments keeps two
    such prefixes rather than making either bigger.

    `label` (e.g. the document's name) only affects the console/prompt_logs
    dump below — purely for dev observability, no effect on the LLM call.
    """
    base_prompt, prompt_version = get_system_prompt(standard_id, segment)
    system_prompt = base_prompt + "\n\n" + format_requirements_listing(clauses, segment)
    call_label = f"map_{segment}__{label or standard_id}"
    _dump_prompt(call_label, system_prompt, document_text)

    last_error: Exception | None = None
    for _ in range(MAX_ATTEMPTS):
        response = _client.chat.completions.create(
            model=settings.llm_deployment,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": document_text},
            ],
        )
        raw = response.choices[0].message.content
        _dump_output(call_label, raw)
        _record_usage(call_label, response)
        try:
            return MappingResult.model_validate(json.loads(raw)), prompt_version
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            continue

    raise RuntimeError(
        f"LLM did not return valid {segment} mapping JSON after {MAX_ATTEMPTS} attempts"
    ) from last_error


def combine_contributions(
    clause_code: str,
    clause_title: str,
    clause_description: str | None,
    contributions: list[dict],
) -> CombinedEvaluation:
    """
    Merge 2+ documents' independent evaluations of the same requirement into
    one combined assessment. Only called when a requirement has more than one
    contributing document — see app/ai/aggregator.py.
    """
    user_message = build_reduce_user_message(clause_code, clause_title, clause_description, contributions)
    _dump_prompt(f"reduce__{clause_code}", REDUCE_SYSTEM_PROMPT, user_message)

    last_error: Exception | None = None
    for _ in range(MAX_ATTEMPTS):
        response = _client.chat.completions.create(
            model=settings.llm_deployment,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": REDUCE_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        raw = response.choices[0].message.content
        _dump_output(f"reduce__{clause_code}", raw)
        _record_usage(f"reduce__{clause_code}", response)
        try:
            return CombinedEvaluation.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            continue

    raise RuntimeError(
        f"LLM did not return valid combine JSON after {MAX_ATTEMPTS} attempts"
    ) from last_error
