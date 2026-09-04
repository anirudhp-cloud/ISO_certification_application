# How large a single call this deployment will actually accept.
#
# Backoff only helps if the quota FREES UP while you wait. If one request is bigger
# than the whole per-minute allowance, it can never succeed no matter how patient the
# retry is - so the ceiling has to be measured, not waited out.
import sys, time
sys.path.insert(0, ".")
import tiktoken
from app.ai.openai_client import _client
from app.config import settings
from proto.corpus import load_corpus
from proto.prompt_v5 import build_system
from proto.unit_ai_policy import UNIT, render_unit

enc = tiktoken.get_encoding("o200k_base")
corpus = load_corpus()
user = render_unit(UNIT)

for n in (4, 8, 12, 16, 20, 29):
    subset = corpus[:n]
    system = build_system(subset)
    size = len(enc.encode(system)) + len(enc.encode(user))
    try:
        r = _client.chat.completions.create(
            model=settings.llm_deployment, response_format={"type": "json_object"},
            temperature=0, seed=settings.llm_seed, max_tokens=50,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user + "\n\nReply {\"ok\":true} only."}])
        print(f"  {n:>2} documents  ~{size:>7,} tokens  OK", flush=True)
    except Exception as exc:
        print(f"  {n:>2} documents  ~{size:>7,} tokens  {type(exc).__name__}", flush=True)
    time.sleep(12)
