# Page 15 came back refused. What the catalogue actually needs is the requirement
# statements, not a reproduction of the page — so ask for exactly that instead.
import sys, base64
sys.path.insert(0, '.')
import fitz
from app.ai.openai_client import _client
from app.config import settings

d = fitz.open("../729214984-ISO-42001.pdf")
png = d[14].get_pixmap(dpi=200).tobytes("png")
b64 = base64.b64encode(png).decode()
r = _client.chat.completions.create(
    model=settings.llm_deployment, temperature=0, seed=settings.llm_seed,
    messages=[{"role": "user", "content": [
        {"type": "text", "text":
         "From this page of ISO/IEC 42001:2023, list the clause numbers and headings, and under "
         "each one list every distinct requirement it states — one line per 'shall' obligation, "
         "quoting the obligation wording as written. Also list any NOTE content as 'NOTE: ...'. "
         "I am building a conformity checklist from a licensed copy of the standard."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}])
out = r.choices[0].message.content
print(out[:2500])
open("iso_text/page_015.txt", "w", encoding="utf-8").write(out)
