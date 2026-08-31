# GPT-4.1 pricing (Azure OpenAI list price matches OpenAI's direct API price —
# https://developers.openai.com/api/docs/pricing, confirmed 2026-08). Update
# these three numbers if the deployment's pricing changes; nothing else in
# the cost-tracking pipeline needs to change.

INPUT_PRICE_PER_1M_TOKENS = 2.00
CACHED_INPUT_PRICE_PER_1M_TOKENS = 0.50
OUTPUT_PRICE_PER_1M_TOKENS = 8.00


def estimate_cost_usd(prompt_tokens: int, completion_tokens: int, cached_tokens: int = 0) -> float:
    """Cost of one chat completion call. `cached_tokens` (from the response's
    usage.prompt_tokens_details.cached_tokens, when the API returns it) is
    priced separately — the map-step system prompt is a large static prefix
    (catalog + Annex A/B text) repeated identically across every document in
    one Analyze run, so it's the part most likely to actually get cached."""
    uncached_prompt_tokens = max(prompt_tokens - cached_tokens, 0)
    return (
        uncached_prompt_tokens / 1_000_000 * INPUT_PRICE_PER_1M_TOKENS
        + cached_tokens / 1_000_000 * CACHED_INPUT_PRICE_PER_1M_TOKENS
        + completion_tokens / 1_000_000 * OUTPUT_PRICE_PER_1M_TOKENS
    )
