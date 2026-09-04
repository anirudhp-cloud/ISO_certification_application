# Compares the two per-AI-system engineering document sets.
#
# The organisation runs TWO AI systems under one AIMS — an HR Recruitment App and the
# Vesta AI Companion — and issues documents 10 to 16 separately for each. That is the
# right shape (6.1.2 NOTE 2 says determination is performed per AI system or grouping),
# but it changes what "satisfied" means: a life-cycle requirement is not met by one
# system's procedure, and the two sets can disagree.

import json
import pathlib
import re

P = [p for p in json.loads(pathlib.Path("proto/doc_profiles.json").read_text(encoding="utf-8"))
     if "error" not in p]


def key(profile: dict) -> str:
    return re.sub(r"[^a-z]", "", profile["file"].split("/")[-1].lower())


hr = {key(p): p for p in P if "HR Recruitment" in p["file"]}
vesta = {key(p): p for p in P if "Vesta" in p["file"]}

print(f"HR Recruitment App : {len(hr)} documents, {sum(p['chars'] for p in hr.values()):,} chars")
print(f"Vesta AI Companion : {len(vesta)} documents, {sum(p['chars'] for p in vesta.values()):,} chars")
print()
print(f"{'document':46} {'HR':>8} {'Vesta':>8}   difference")
print("-" * 78)
for k in sorted(set(hr) | set(vesta)):
    a, b = hr.get(k), vesta.get(k)
    name = (a or b)["file"].split("/")[-1][:44]
    hr_chars = f"{a['chars']:,}" if a else "-"
    ve_chars = f"{b['chars']:,}" if b else "-"
    if a and b:
        note = f"{(a['chars'] - b['chars']) / b['chars'] * 100:+.0f}%"
    else:
        note = "ONLY IN VESTA" if b else "ONLY IN HR"
    print(f"{name:46} {hr_chars:>8} {ve_chars:>8}   {note}")

print()
print("=== SECTION HEADINGS, side by side ===")
for k in sorted(set(hr) & set(vesta)):
    a, b = hr[k], vesta[k]
    ha, hb = set(a["headings"]), set(b["headings"])
    if ha != hb:
        print(f"\n  {a['file'].split('/')[-1][:56]}")
        only_hr = sorted(ha - hb)
        only_ve = sorted(hb - ha)
        if only_hr:
            print(f"    only in HR:    {'; '.join(h[:44] for h in only_hr[:6])}")
        if only_ve:
            print(f"    only in Vesta: {'; '.join(h[:44] for h in only_ve[:6])}")

print()
print("=== WHAT EACH SYSTEM IS, from the documents themselves ===")
for label, group in (("HR Recruitment App", hr), ("Vesta AI Companion", vesta)):
    sample = max(group.values(), key=lambda p: p["chars"])
    print(f"\n  {label}  — from {sample['file'].split('/')[-1][:52]}")
    print("   ", " ".join(sample["first_600"].split())[:420])
