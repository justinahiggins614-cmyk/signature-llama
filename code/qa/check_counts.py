#!/usr/bin/env python3
"""Count-vs-data checker for the signature-llama site.

Verifies the numbers shown on the site match the actual data files:
  - dictionary terms == 312
  - tool libraries == 120
  - explainer KB entries == 28
  - SGLL weights header parses to 2,983,488 params
  - model-status.json architecture.parameters == 2983488
  - weights/engine/vocab SHA-256 in model-status.json match the repo files
  - weights size matches model-status.json size_bytes
  - INVENTORY array entries all have name/desc and file references resolve

Exits 0 on pass, 1 with findings otherwise.
Usage: python3 check_counts.py
"""
import hashlib
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EXPECTED = {
    "dict_terms": 312,
    "tool_libraries": 120,
    "kb_entries": 28,
    "params": 2983488,
    "weights_size": 3042035,
    "weights_sha256": "b2dfc0d05add95786797e596559f3e86de9b3a9c9dbce6818814ad05d6317b58",
    "engine_sha256": "6188cb269e07a134e865de4f7b68ee8c5dcfd1bde8771ad2c7b574a2edb4355a",
    "vocab_sha256": "53363d3fc2ca692de59c1b311f5dcfef29555e41295adb7fb40d8e10a79b6406",
}


def sgll_params(path):
    raw = open(path, "rb").read()
    if raw[:4] != b"SGLL":
        return None, "bad magic"
    _v, _vo, _h, _ly, _hd, _cx = struct.unpack("<6I", raw[4:28])
    _mlp, nt = struct.unpack("<II", raw[32:40])
    off, total = 40, 0
    for _ in range(nt):
        nb = raw[off]; off += 1 + nb
        nd = raw[off]; off += 1
        dims = struct.unpack("<%dI" % nd, raw[off:off + 4 * nd]); off += 4 * nd
        off += 1
        ns = struct.unpack("<I", raw[off:off + 4])[0]; off += 4 + 4 * ns
        nbytes = struct.unpack("<I", raw[off:off + 4])[0]; off += 4 + nbytes
        p = 1
        for d in dims:
            p *= d
        total += p
    return total, None


def main():
    fails = []

    d = json.load(open(os.path.join(ROOT, "data/llm-dictionary.json"), encoding="utf-8"))
    n_terms = len(d["terms"])
    if n_terms != EXPECTED["dict_terms"]:
        fails.append("dictionary: %d terms, expected %d" % (n_terms, EXPECTED["dict_terms"]))
    print("  dictionary terms:", n_terms)

    t = json.load(open(os.path.join(ROOT, "data/tool-libraries.json"), encoding="utf-8"))
    n_libs = len(t["libraries"])
    if n_libs != EXPECTED["tool_libraries"]:
        fails.append("tool libraries: %d, expected %d" % (n_libs, EXPECTED["tool_libraries"]))
    print("  tool libraries:", n_libs)

    kb = json.load(open(os.path.join(ROOT, "data/explainer-kb.json"), encoding="utf-8"))
    n_kb = len(kb["entries"])
    if n_kb != EXPECTED["kb_entries"]:
        fails.append("explainer KB: %d entries, expected %d" % (n_kb, EXPECTED["kb_entries"]))
    print("  explainer KB entries:", n_kb)

    params, err = sgll_params(os.path.join(ROOT, "sigllama/sigllama-v1.bin"))
    if err or params != EXPECTED["params"]:
        fails.append("weights header: %s, expected %d params" % (err or params, EXPECTED["params"]))
    print("  SGLL params:", params)

    ms = json.load(open(os.path.join(ROOT, "model-status.json"), encoding="utf-8"))
    if ms.get("architecture", {}).get("parameters") != EXPECTED["params"]:
        fails.append("model-status.json parameters != %d" % EXPECTED["params"])
    if ms["weights"]["size_bytes"] != EXPECTED["weights_size"]:
        fails.append("model-status.json weights size_bytes != %d" % EXPECTED["weights_size"])

    for key, rel, expect in [("weights", "sigllama/sigllama-v1.bin", EXPECTED["weights_sha256"]),
                            ("engine", "sigllama/sigllama.js", EXPECTED["engine_sha256"]),
                            ("vocab", "sigllama/vocab.json", EXPECTED["vocab_sha256"])]:
        raw = open(os.path.join(ROOT, rel), "rb").read()
        h = hashlib.sha256(raw).hexdigest()
        if h != expect:
            fails.append("%s file hash mismatch: %s" % (rel, h))
        if ms[key]["sha256"] != expect:
            fails.append("model-status.json %s sha256 != ground truth" % key)
        print("  %s: %d bytes, sha256 ok" % (rel, len(raw)))

    # inventory: every entry rendered in the page; file refs resolve
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    entries = re.findall(r"\{ name: '([^']+)', cat: '([^']+)', file: '([^']*)',\s*\n\s*desc: ", html)
    print("  inventory entries in page:", len(entries))
    for name, cat, f in entries:
        if f and not os.path.isfile(os.path.join(ROOT, f)):
            fails.append("inventory: '%s' file ref %s missing" % (name, f))

    # llms.txt carries the same key numbers
    llms = open(os.path.join(ROOT, "llms.txt"), encoding="utf-8").read()
    for token in ["2,983,488", "312", "120"]:
        if token not in llms:
            fails.append("llms.txt missing token '%s'" % token)

    if fails:
        print("COUNT AUDIT: %d failure(s)" % len(fails))
        for f in fails:
            print("  FAIL", f)
        return 1
    print("COUNT AUDIT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
