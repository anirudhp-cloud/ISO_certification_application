# Per-assessment cost aggregation. An "assessment" is one API request that
# can trigger multiple LLM calls (org-wide Analyze = one map call per document
# + one reduce call per multi-document clause; per-document Analyze = one map
# call). A route wraps its work in `tracking()`; every LLM call inside that
# scope (however deep — clause_mapper -> openai_client, aggregator ->
# openai_client) records itself automatically via `record_call`, with no
# extra plumbing through function signatures. Built on contextvars rather
# than a global, so concurrent requests never mix up each other's totals.

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass
class LLMCallCost:
    label: str
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int
    cost_usd: float


@dataclass
class CostTracker:
    calls: list[LLMCallCost] = field(default_factory=list)

    def record(self, label: str, prompt_tokens: int, completion_tokens: int, cached_tokens: int, cost_usd: float) -> None:
        self.calls.append(LLMCallCost(label, prompt_tokens, completion_tokens, cached_tokens, cost_usd))

    @property
    def call_count(self) -> int:
        return len(self.calls)

    @property
    def prompt_tokens(self) -> int:
        return sum(c.prompt_tokens for c in self.calls)

    @property
    def completion_tokens(self) -> int:
        return sum(c.completion_tokens for c in self.calls)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def cost_usd(self) -> float:
        return sum(c.cost_usd for c in self.calls)


_current: ContextVar["CostTracker | None"] = ContextVar("cost_tracker", default=None)


@contextmanager
def tracking():
    """Start a fresh tracker for the current request; everything an
    openai_client call records while inside this `with` block lands on it."""
    tracker = CostTracker()
    token = _current.set(tracker)
    try:
        yield tracker
    finally:
        _current.reset(token)


def record_current(label: str, prompt_tokens: int, completion_tokens: int, cached_tokens: int, cost_usd: float) -> None:
    """No-op outside a `tracking()` block (e.g. the ad-hoc /analyze test
    endpoint) — cost tracking is opt-in per route, not forced everywhere."""
    tracker = _current.get()
    if tracker is not None:
        tracker.record(label, prompt_tokens, completion_tokens, cached_tokens, cost_usd)
