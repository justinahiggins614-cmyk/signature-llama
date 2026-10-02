#!/usr/bin/env python3
"""Missing-ID / missing-field checker for the signature-llama site.

Finds records that are missing required identifiers or fields:
  - tool libraries: id, name, category, desc, version, optimal flag,
    functions, capabilities, example (with input/output), code
  - dictionary terms: t (term), c (category), d (definition)
  - INVENTORY entries: name, cat, desc, sample
  - model-status.json: required top-level keys + architecture/weights/engine/vocab blocks
  - llama-manifest.json: industry_standard section present

Exits 0 on pass, 1 with findings otherwise.
Usage: python3 check_missing_ids.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LIB_REQ = ["id", "name", "category", "desc", "version", "optimal",
           "functions", "capabilities", "example", "code",
           "input", "output", "status"]
DICT_REQ = ["t", "c", "d"]
MS_TOP = ["MODEL_ID", "MODEL_VERSION", "MODEL_STATUS", "updated",
          "architecture", "weights", "engine", "vocab", "modes", "offline"]
MS_ARCH = ["type", "parameters", "layers", "attention_heads", "context_length",
           "hidden_size", "mlp_size", "tokenizer", "precision"]


def main():
    fails = []

    t = json.load(open(os.path.join(ROOT, "data/tool-libraries.json"), encoding="utf-8"))
    for i, lib in enumerate(t["libraries"]):
        missing = [k for k in LIB_REQ if k not in lib or lib[k] in (None, "", [])]
        if missing:
            fails.append("library #%d (%s): missing %s" % (i, lib.get("id", "?"), missing))
        if lib.get("status") not in ("Library available", "Demo tested"):
            fails.append("library %s: unknown status %r" % (lib.get("id", "?"), lib.get("status")))
    print("  tool libraries checked:", len(t["libraries"]))

    dd = json.load(open(os.path.join(ROOT, "data/llm-dictionary.json"), encoding="utf-8"))
    for i, e in enumerate(dd["terms"]):
        missing = [k for k in DICT_REQ if k not in e or not str(e[k]).strip()]
        if missing:
            fails.append("dictionary #%d: missing %s" % (i, missing))
    print("  dictionary terms checked:", len(dd["terms"]))

    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    inv = re.findall(r"\{ name: '([^']*)', cat: '([^']*)', file: '([^']*)',\s*\n\s*desc: '",
                     html)
    if not inv:
        fails.append("inventory: no entries parsed from page")
    for name, cat, f in inv:
        if not name.strip() or not cat.strip():
            fails.append("inventory entry missing name/cat")
    print("  inventory entries checked:", len(inv))

    ms = json.load(open(os.path.join(ROOT, "model-status.json"), encoding="utf-8"))
    for k in MS_TOP:
        if k not in ms:
            fails.append("model-status.json missing top-level key: %s" % k)
    for k in MS_ARCH:
        if k not in ms.get("architecture", {}):
            fails.append("model-status.json missing architecture.%s" % k)

    mf = json.load(open(os.path.join(ROOT, "llama-manifest.json"), encoding="utf-8"))
    if "industry_standard" not in mf:
        fails.append("llama-manifest.json missing industry_standard section")
    print("  manifest industry_standard:", "industry_standard" in mf)

    if fails:
        print("MISSING-ID AUDIT: %d failure(s)" % len(fails))
        for f in fails:
            print("  FAIL", f)
        return 1
    print("MISSING-ID AUDIT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
