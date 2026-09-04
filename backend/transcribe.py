# One-time: transcribe the clause pages of the licensed ISO/IEC 42001 PDF so the
# obligation catalogue can be derived from the standard's own "shall" wording rather
# than a paraphrase of it. The PDF is a scan with no text layer and no OCR is
# installed, so the vision model does the transcription. Output is cached per page,
# so a rate limit costs one page rather than the run.
import sys, base64, time, pathlib
sys.path.insert(0, '.')
import fitz
from app.ai.openai_client import _client
from app.config import settings

OUT = pathlib.Path("iso_text")
OUT.mkdir(exist_ok=True)
d = fitz.open("../729214984-ISO-42001.pdf")

PROMPT = ("This is one page of ISO/IEC 42001:2023, from a licensed copy. Set out its content as plain text: clause/annex numbers and headings exactly as printed, every requirement or guidance statement it makes (one per line, in the wording used), and every NOTE. Do not summarise or reorder. Mark unreadable regions [illegible]. I am building a conformity checklist from it.")

def transcribe(i, attempt=0):
    target = OUT / f"page_{i+1:03d}.txt"
    if target.exists() and target.stat().st_size > 50:
        return "cached"
    png = d[i].get_pixmap(dpi=170).tobytes("png")
    b64 = base64.b64encode(png).decode()
    try:
        r = _client.chat.completions.create(
            model=settings.llm_deployment, temperature=0, seed=settings.llm_seed,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}])
    except Exception as exc:
        if attempt < 5:
            time.sleep(8 * (attempt + 1))
            return transcribe(i, attempt + 1)
        return f"FAILED {type(exc).__name__}"
    target.write_text(r.choices[0].message.content, encoding="utf-8")
    return f"{r.usage.prompt_tokens}in/{r.usage.completion_tokens}out"

for i in list(range(0, 12)) + list(range(32, 61)):   # front matter, terms, Annex B onward
    print(f"page {i+1:>3}: {transcribe(i)}", flush=True)
    time.sleep(1.5)
print("DONE")
