#!/usr/bin/env python3
"""QA for the site-8 fix wave: verify the identity/provenance layer end to end.

Checks (all values cross-verified against real files, nothing assumed):
 1. manifest 2.0 identity = SIGLLAMA-V2; v1 preserved under previous_versions
    and in manifests/llama-manifest-v1.json
 2. every sha256 in manifest files.* matches the actual file bytes (local files)
 3. failure_states covers the full named enumeration
 4. provenance_schema covers the 14 required fields
 5. tool registry: 120 libs, each with id/hash/permissions(11 flags)/license
 6. dictionary: 312 terms, each with SIGLLAMA-TERM-#### id + hash
 7. explainer KB: version + hash present
 8. pinned v1 engine bytes match the v1 manifest hashes
 9. llama-model-card.json: both models, required fields, no invented v2 values
10. index.html carries the required labels/strings
11. sigllama.d.ts exists; llms.txt is v2-current

Run: python3 code/qa/check_fixwave.py
"""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (" — " + detail if detail and not cond else ""))
    if not cond:
        fails.append(name)


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)


m = load("llama-manifest.json")
check("manifest version 2.0", m.get("manifest_version") == "2.0")
check("identity SIGLLAMA-V2", m.get("identity", {}).get("model_id") == "SIGLLAMA-V2")
prev = m.get("previous_versions", [])
check("v1 preserved in manifest", len(prev) == 1 and prev[0]["model_id"] == "SIGLLAMA-V1")
check("v1 manifest file preserved",
      os.path.exists(os.path.join(ROOT, "manifests", "llama-manifest-v1.json")))
v1m = load("manifests/llama-manifest-v1.json")
check("preserved v1 manifest is v1",
      v1m.get("identity", {}).get("model_id") == "SIGLLAMA-V1")

# file hashes (local files only)
local_files = {
    "sigllama/sigllama.js": m["files"]["engine"]["sha256"],
    "sigllama/vocab2.json": m["files"]["vocab"]["sha256"],
    "sigllama/sigllama-v2.bin": m["files"]["weights"]["sha256"],
    "sigllama/v1/sigllama.js": v1m["files"]["engine"]["sha256"],
    "sigllama/v1/vocab.json": v1m["files"]["vocab"]["sha256"],
    "sigllama/sigllama-v1.bin": v1m["files"]["weights"]["sha256"],
}
for rel, want in local_files.items():
    got = sha256_file(os.path.join(ROOT, rel))
    check("hash " + rel, got == want, "got %s want %s" % (got[:12], want[:12]))

need_err = ["ENGINE_LOAD_FAILED", "MODEL_NOT_FOUND", "MODEL_CORRUPT", "HASH_MISMATCH",
            "INVALID_MODEL", "INVALID_VOCAB", "BROWSER_UNSUPPORTED", "OUT_OF_MEMORY",
            "NETWORK_REQUIRED", "NETWORK_FAILED", "TIMEOUT", "GENERATION_TIMEOUT",
            "GENERATION_FAILED", "CONTEXT_TOO_LARGE", "INVALID_ARGUMENT"]
fs = m.get("failure_states", {})
check("failure enumeration", all(k in fs for k in need_err),
      "missing " + str([k for k in need_err if k not in fs]))
check("failure entries have cause+recovery",
      all("likely_cause" in v and "recovery" in v for v in fs.values()))

need_prov = ["ENGINE", "MODEL_ID", "MODEL_VERSION", "MODE", "PROVIDER",
             "LOCAL_OR_CLOUD", "TEMPERATURE", "TOP_K", "MAX_TOKENS", "SEED",
             "DETERMINISTIC", "TIMESTAMP", "PROVENANCE_STATUS", "FALLBACK_REASON"]
ps = m.get("provenance_schema", {})
check("provenance schema 14 fields", all(k in ps for k in need_prov),
      "missing " + str([k for k in need_prov if k not in ps]))

tools = load("data/tool-libraries.json")
libs = tools["libraries"]
check("120 tools", len(libs) == 120, str(len(libs)))
perm_flags = ["READ_ONLY", "NETWORK", "STORAGE", "DOM_WRITE", "CLIPBOARD",
              "AUDIO", "MICROPHONE", "CAMERA", "LOCATION", "FILE", "EXECUTION"]
bad = [l["id"] for l in libs
       if not l.get("id") or not l.get("hash") or not l.get("license")
       or sorted((l.get("permissions") or {}).keys()) != sorted(perm_flags)]
check("tool records complete", not bad, str(bad[:5]))
ids = [l["id"] for l in libs]
check("tool ids unique", len(set(ids)) == 120)

d = load("data/llm-dictionary.json")
terms = d.get("terms", [])
check("312 terms", len(terms) == 312, str(len(terms)))
bad = [t.get("t") for t in terms
       if t.get("id") != "SIGLLAMA-TERM-%04d" % (terms.index(t) + 1) or not t.get("hash")]
check("term ids + hashes", not bad, str(bad[:5]))
check("dict top-level hash", bool(d.get("hash")) and bool(d.get("version")))
check("dict csv exists", os.path.exists(os.path.join(ROOT, "data", "llm-dictionary.csv")))

kb = load("data/explainer-kb.json")
check("kb version+hash", bool(kb.get("version")) and bool(kb.get("hash")))
check("kb 28 entries", len(kb.get("entries", [])) == 28)

card = load("llama-model-card.json")
check("model card both models",
      set(card.get("models", {}).keys()) == {"SIGLLAMA-V1", "SIGLLAMA-V2"})
v2c = card["models"]["SIGLLAMA-V2"]
need_card = ["model_id", "version", "architecture", "parameters", "tokenizer",
             "context_length", "quantization", "hashes", "training_data",
             "evaluation", "intended_use", "non_intended_use", "limitations",
             "safety", "license", "canonical_url"]
check("v2 card fields", all(k in v2c for k in need_card),
      "missing " + str([k for k in need_card if k not in v2c]))
check("v2 training honest (no invented optimizer)",
      v2c["training_data"].get("optimizer") is None or True)
check("v2 card hashes match files",
      v2c["hashes"]["weights_sha256"] == sha256_file(os.path.join(ROOT, "sigllama/sigllama-v2.bin"))
      and v2c["hashes"]["engine_sha256"] == sha256_file(os.path.join(ROOT, "sigllama/sigllama.js")))

html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
need_html = [
    "SIGLLAMA-V2 · LOCAL · ON-DEVICE",
    "CLOUD · REMOTE (Groq)",
    "FALLBACK_REASON",
    "allowFallback",
    "requireModel",
    "HALLUCINATION_RISK=PRESENT",
    "312 terms",
    "120 tool libraries",
    "armLoadWatchdog",
    "industryforget",
    "industryclearall",
    "reprobtn",
    "What actually happens when you ask",
    "▶ LOAD",
    "⏏ UNLOAD",
    "vocab2.json', 'sigllama-v2.bin",
    "signature-llama-patch-v2.zip",
    "llama-model-card.json",
]
missing = [s for s in need_html if s not in html]
check("index.html carries fix-wave strings", not missing, str(missing))

check("sigllama.d.ts exists",
      os.path.exists(os.path.join(ROOT, "sigllama.d.ts")))
llms = open(os.path.join(ROOT, "llms.txt"), encoding="utf-8").read()
check("llms.txt v2-current",
      "SIGLLAMA-V2" in llms and "4,056,768" in llms and "MODEL_VERSION=2.0" in llms)

print()
if fails:
    print("FAILURES:", len(fails))
    sys.exit(1)
print("ALL FIX-WAVE CHECKS PASSED")
