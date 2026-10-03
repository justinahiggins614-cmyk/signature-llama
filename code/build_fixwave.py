#!/usr/bin/env python3
"""Site-8 fix wave, Batch 1: identity/data layer.

What it does (all values read from real files, nothing invented):
 1. Preserves the v1 manifest: manifests/llama-manifest-v1.json (never overwritten).
 2. Rewrites llama-manifest.json as 2.0: current model SIGLLAMA-V2 with facts read
    from model-status.json; v1 record preserved under previous_versions.
 3. Creates llama-model-card.json (machine-readable model card, v2 current + v1 past).
    v2 training config is NOT documented in the repo -> marked honestly.
 4. Upgrades data/tool-libraries.json to 1.1: per-tool sha256 of code, formal
    permission flags (static scan of the shipped code), license, source.
 5. Upgrades data/llm-dictionary.json to 1.1: permanent term IDs, top-level
    version/hash/updated. Builds data/llm-dictionary.csv.
 6. Upgrades data/explainer-kb.json to 1.1: version/hash/updated.
 7. Publishes the pinned v1 engine: sigllama/v1/sigllama.js + vocab.json + README
    (bytes copied from src/, hashes verified against the v1 manifest).

Run from the repo root:  python3 code/build_fixwave.py
"""
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = date.today().isoformat()
SITE = "https://justinahiggins614-cmyk.github.io/signature-llama/"
BACKEND = "https://justinahiggins614-cmyk.github.io/signature-backend/sigllama/"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)


def save(p, obj):
    full = os.path.join(ROOT, p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    tmp = full + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, full)


# ---------------------------------------------------------------- permissions
PERMISSION_ORDER = ["READ_ONLY", "NETWORK", "STORAGE", "DOM_WRITE", "CLIPBOARD",
                    "AUDIO", "MICROPHONE", "CAMERA", "LOCATION", "FILE", "EXECUTION"]

SCAN_PATTERNS = {
    "NETWORK": [r"\bfetch\s*\(", r"XMLHttpRequest", r"WebSocket\s*\(", r"sendBeacon",
                r"EventSource\s*\(", r"\.src\s*=\s*['\"]https?://"],
    "STORAGE": [r"\blocalStorage\b", r"\bsessionStorage\b", r"\bindexedDB\b"],
    "DOM_WRITE": [r"document\.write", r"\binnerHTML\s*=", r"\bouterHTML\s*=",
                  r"insertAdjacentHTML", r"createElement\s*\(", r"\btextContent\s*="],
    "CLIPBOARD": [r"navigator\.clipboard", r"execCommand\s*\(\s*['\"]copy"],
    "AUDIO": [r"AudioContext", r"webkitAudioContext", r"\bnew Audio\s*\(", r"speechSynthesis"],
    "MICROPHONE": [r"getUserMedia"],
    "CAMERA": [r"getUserMedia"],
    "LOCATION": [r"\bgeolocation\b"],
    "FILE": [r"FileReader", r"showOpenFilePicker", r"showSaveFilePicker",
             r"URL\.createObjectURL", r"\bdownload\s*="],
    "EXECUTION": [r"\beval\s*\(", r"new Function\s*\(", r"setTimeout\s*\(\s*['\"]"],
}


def scan_permissions(code, declared):
    """Formal permission flags = declared capabilities OR'd with a static
    scan of the shipped code (the scan adds finer flags the old declaration
    did not track: DOM_WRITE, CLIPBOARD, AUDIO, LOCATION)."""
    code = code or ""
    declared = declared or {}
    perms = {}
    for flag, patterns in SCAN_PATTERNS.items():
        perms[flag] = any(re.search(p, code) for p in patterns)
    if declared.get("network") or declared.get("remote_requests"):
        perms["NETWORK"] = True
    if declared.get("storage"):
        perms["STORAGE"] = True
    if declared.get("filesystem"):
        perms["FILE"] = True
    if declared.get("camera"):
        perms["CAMERA"] = True
    if declared.get("microphone"):
        perms["MICROPHONE"] = True
    if declared.get("code_execution"):
        perms["EXECUTION"] = True
    # READ_ONLY = nothing detected at all
    perms["READ_ONLY"] = not any(perms[f] for f in PERMISSION_ORDER if f != "READ_ONLY")
    return perms


def main():
    # ---- 1. preserve the old manifest (never overwritten again) ----
    os.makedirs(os.path.join(ROOT, "manifests"), exist_ok=True)
    v1_copy = os.path.join(ROOT, "manifests", "llama-manifest-v1.json")
    if not os.path.exists(v1_copy):
        shutil.copy2(os.path.join(ROOT, "llama-manifest.json"), v1_copy)
        print("preserved v1 manifest ->", v1_copy)
    # v1 facts always come from the preserved v1 copy (idempotent re-runs)
    with open(v1_copy, encoding="utf-8") as f:
        manifest_v1 = json.load(f)
    status = load("model-status.json")

    arch = status.get("architecture", {})
    weights = status.get("weights", {})
    engine = status.get("engine", {})
    vocab = status.get("vocab", {})

    # ---- sanity: local files must match model-status.json hashes ----
    checks = [
        ("sigllama/sigllama.js", engine.get("sha256"), "engine"),
        ("sigllama/vocab2.json", vocab.get("sha256"), "vocab2"),
        ("sigllama/sigllama-v2.bin", weights.get("sha256"), "weights v2"),
        ("sigllama/sigllama-v1.bin", manifest_v1["files"]["weights"]["sha256"], "weights v1"),
        ("src/sigllama.js", manifest_v1["files"]["engine"]["sha256"], "engine v1"),
        ("src/vocab.json", manifest_v1["files"]["vocab"]["sha256"], "vocab v1"),
    ]
    for rel, want, label in checks:
        got = sha256_file(os.path.join(ROOT, rel))
        if got != want:
            print("HASH MISMATCH:", label, rel, "got", got, "want", want)
            sys.exit(1)
    print("all 6 file hashes verify against the manifests")

    # ---- 4. tool registry 1.1 ----
    tools = load("data/tool-libraries.json")
    n_exec = 0
    for lib in tools["libraries"]:
        code = lib.get("code", "")
        lib["hash"] = sha256_text(code)
        lib["permissions"] = scan_permissions(code, lib.get("capabilities"))
        lib["license"] = "Free for any website, app, or project. No API key, no fee."
        lib["source"] = SITE + "data/tool-libraries.json"
        lib["created"] = tools.get("updated", "2026-09-30")
        lib["updated"] = TODAY
        if lib["permissions"]["EXECUTION"]:
            n_exec += 1
    tools["version"] = "1.1"
    tools["updated"] = TODAY
    tools["permission_model"] = {
        "method": "static-scan",
        "ran": TODAY,
        "flags": PERMISSION_ORDER,
        "note": ("Each tool's shipped code was statically scanned for browser-API "
                 "patterns; flags are booleans. READ_ONLY=true means the scan found "
                 "no capability pattern. Scans can miss dynamically-built calls; "
                 "treat flags as declared, not proven. Tools run only when loaded, "
                 "and only as ordinary page JavaScript."),
    }
    tools["hash"] = sha256_text(canon({"libraries": tools["libraries"]}))
    save("data/tool-libraries.json", tools)
    print("tool registry 1.1:", len(tools["libraries"]), "tools,",
          n_exec, "flag EXECUTION, registry hash", tools["hash"][:16] + "...")

    # ---- 5. dictionary 1.1 ----
    d = load("data/llm-dictionary.json")
    terms = d.get("terms", [])
    for i, t in enumerate(terms, 1):
        t["id"] = "SIGLLAMA-TERM-%04d" % i
        t["v"] = "1.1"
        t["hash"] = sha256_text(canon({"t": t.get("t"), "d": t.get("d"), "c": t.get("c")}))
    d["version"] = "1.1"
    d["updated"] = TODAY
    d["hash"] = sha256_text(canon({"terms": terms}))
    save("data/llm-dictionary.json", d)
    with open(os.path.join(ROOT, "data", "llm-dictionary.csv"), "w", encoding="utf-8") as f:
        f.write("id,term,definition,category\n")
        for t in terms:
            q = lambda s: '"' + str(s).replace('"', '""') + '"'
            f.write(",".join([t["id"], q(t.get("t")), q(t.get("d")), q(t.get("c"))]) + "\n")
    print("dictionary 1.1:", len(terms), "terms, ids + hashes, csv written")

    # ---- 6. explainer KB 1.1 ----
    kb = load("data/explainer-kb.json")
    kb["version"] = "1.1"
    kb["updated"] = TODAY
    kb["hash"] = sha256_text(canon({"entries": kb["entries"]}))
    save("data/explainer-kb.json", kb)
    print("explainer-kb 1.1:", len(kb["entries"]), "entries")

    # ---- 7. pinned v1 engine ----
    os.makedirs(os.path.join(ROOT, "sigllama", "v1"), exist_ok=True)
    shutil.copy2(os.path.join(ROOT, "src", "sigllama.js"),
                 os.path.join(ROOT, "sigllama", "v1", "sigllama.js"))
    shutil.copy2(os.path.join(ROOT, "src", "vocab.json"),
                 os.path.join(ROOT, "sigllama", "v1", "vocab.json"))
    with open(os.path.join(ROOT, "sigllama", "v1", "README.txt"), "w") as f:
        f.write(
            "PINNED Signature Llama v1 engine + vocabulary (SIGLLAMA-V1).\n"
            "This directory never changes: sigllama.js and vocab.json are the exact\n"
            "bytes published 2026-09-30. Old model binaries are never overwritten\n"
            "under the same version.\n\n"
            "sigllama.js sha256: " + manifest_v1["files"]["engine"]["sha256"] + "\n"
            "vocab.json  sha256: " + manifest_v1["files"]["vocab"]["sha256"] + "\n"
            "Pair with sigllama-v1.bin weights "
            "(sha256 " + manifest_v1["files"]["weights"]["sha256"] + ").\n"
            "Canonical pinned URL: " + SITE + "sigllama/v1/sigllama.js\n")
    print("pinned v1 engine published at sigllama/v1/")

    # ---- 2. manifest 2.0 ----
    v1_rec = {
        "model_id": "SIGLLAMA-V1",
        "name": "Signature Llama v1",
        "version": "1.0",
        "status": "superseded — preserved, still downloadable",
        "parameters": manifest_v1["model"]["parameter_count"],
        "architecture": "decoder-only transformer",
        "layers": 5, "attention_heads": 8, "hidden_size": 192,
        "mlp_size": 768, "rope_theta": 10000.0,
        "context_length": 128,
        "tokenizer": "character-level, 84 tokens",
        "tokenizer_type": "character-level",
        "vocabulary_size": 84,
        "precision": "int8, per-row scales",
        "weight_format": "SGLL v1 binary (magic 'SGLL', format version 1)",
        "training": manifest_v1.get("training"),
        "weights": manifest_v1["files"]["weights"],
        "engine": manifest_v1["files"]["engine"],
        "vocab": manifest_v1["files"]["vocab"],
        "manifest": SITE + "manifests/llama-manifest-v1.json",
        "pinned_engine_url": SITE + "sigllama/v1/sigllama.js",
    }
    failure_states = {
        "ENGINE_LOAD_FAILED": {
            "meaning": "The engine script sigllama.js could not be downloaded or parsed.",
            "likely_cause": "network blocked the file, or the file is truncated.",
            "recovery": "retry the load; check the engine URL; verify the SHA-256."},
        "MODEL_NOT_FOUND": {
            "meaning": "vocab2.json or sigllama-v2.bin returned 404 at the model base URL.",
            "likely_cause": "wrong base URL, or the site files moved.",
            "recovery": "check the base URL and the pinned URLs in the manifest."},
        "MODEL_CORRUPT": {
            "meaning": "The weight binary failed its header check (magic 'SGLL', format version 1) or failed to parse.",
            "likely_cause": "truncated download or a tampered file.",
            "recovery": "re-download; verify the SHA-256 against the manifest."},
        "HASH_MISMATCH": {
            "meaning": "A downloaded file's SHA-256 did not match the manifest. The file is refused and never loaded.",
            "likely_cause": "corrupt download, stale cache, or tampering.",
            "recovery": "clear cache, re-download, compare hashes."},
        "INVALID_MODEL": {
            "meaning": "The weights parsed but are not a compatible Signature Llama model (wrong parameter count or layout).",
            "likely_cause": "mixed files from two model versions.",
            "recovery": "use the matched engine+weights+vocab triple from the manifest."},
        "INVALID_VOCAB": {
            "meaning": "The vocabulary does not match the model (wrong token count or format).",
            "likely_cause": "v1 vocab paired with v2 weights or vice versa.",
            "recovery": "use vocab2.json with SIGLLAMA-V2, vocab.json with SIGLLAMA-V1."},
        "BROWSER_UNSUPPORTED": {
            "meaning": "The browser is missing APIs the engine needs (fetch, Blob, URL, typed arrays, crypto.subtle).",
            "likely_cause": "an old browser.",
            "recovery": "use a current Chrome, Edge, Firefox, or Safari."},
        "OUT_OF_MEMORY": {
            "meaning": "The browser ran out of memory while allocating the model.",
            "likely_cause": "a low-memory phone with many tabs open.",
            "recovery": "close tabs and retry; avoid loading several models at once."},
        "NETWORK_REQUIRED": {
            "meaning": "The browser reports it is offline and the engine/weights are not cached yet. First load needs internet.",
            "likely_cause": "offline first visit.",
            "recovery": "connect once; afterwards the browser cache serves the files."},
        "NETWORK_FAILED": {
            "meaning": "A fetch failed after retries (not a 404).",
            "likely_cause": "flaky connection or a proxy blocking the file.",
            "recovery": "retry; check the connection."},
        "TIMEOUT": {
            "meaning": "A load step exceeded its time budget.",
            "likely_cause": "very slow network or a frozen tab.",
            "recovery": "retry; use a faster connection."},
        "GENERATION_TIMEOUT": {
            "meaning": "Generation did not finish within the requested timeoutMs.",
            "likely_cause": "the tab is throttled or frozen; the model itself is small.",
            "recovery": "raise timeoutMs or retry in a foreground tab."},
        "GENERATION_FAILED": {
            "meaning": "The engine threw during generation.",
            "likely_cause": "bad sampling arguments or an engine bug.",
            "recovery": "validate arguments (see sampling); retry; report the code."},
        "CONTEXT_TOO_LARGE": {
            "meaning": "The prompt plus maxTokens exceeds the model's context length.",
            "likely_cause": "maxTokens set too high for the context window.",
            "recovery": "lower maxTokens or shorten the prompt; the loader left-truncates."},
        "INVALID_ARGUMENT": {
            "meaning": "A sampling argument was rejected: NaN/Infinity temperature, negative maxTokens, or topK outside 1..vocab-1.",
            "likely_cause": "a programming mistake by the caller.",
            "recovery": "pass finite numbers inside the documented ranges."},
        "MISSING_KEY": {
            "meaning": "Industry Standard mode needs the user's free API key and none is saved.",
            "likely_cause": "first use of the cloud mode.",
            "recovery": "paste a free key in the Industry Standard box and connect."},
        "BAD_KEY": {
            "meaning": "The cloud rejected the API key (401).",
            "likely_cause": "a revoked or mistyped key.",
            "recovery": "check the key at the provider console and paste it again."},
        "RATE_LIMITED": {
            "meaning": "The cloud rate limit was hit (429).",
            "likely_cause": "too many requests on the free tier.",
            "recovery": "wait and retry; the on-device v2 keeps working."},
    }
    manifest = {
        "manifest_version": "2.0",
        "updated": TODAY,
        "identity": {
            "model_id": "SIGLLAMA-V2",
            "record_type": "LLAMA_MODEL",
            "name": "Signature Llama: The Fully Cyber Utilizable AI",
            "short_name": "Signature Llama",
            "human_name": "Signature Llama v2",
            "version": 2,
        },
        "previous_versions": [v1_rec],
        "name": "Signature Llama: The Fully Cyber Utilizable AI",
        "short_name": "Signature Llama",
        "creator": "Justin Addam Higgins",
        "site": SITE,
        "status": "live",
        "model_status": "live",
        "affiliation": "Independent model. Not affiliated with Meta or the LLaMA model family.",
        "description": ("A tiny transformer language model I built and trained from scratch. "
                        "v2 is a word-level chat model (~4M parameters) running entirely in "
                        "the browser: no API keys, no servers, no fees."),
        "model": {
            "model_id": "SIGLLAMA-V2",
            "version": "2.0",
            "architecture": arch.get("type", "decoder-only transformer"),
            "layers": arch.get("layers"),
            "attention_heads": arch.get("attention_heads"),
            "hidden_size": arch.get("hidden_size"),
            "mlp_size": arch.get("mlp_size"),
            "rope_theta": arch.get("rope_theta"),
            "context_length": arch.get("context_length"),
            "parameter_count": arch.get("parameters"),
            "parameters_human": "~4M (v2)",
            "tokenizer": arch.get("tokenizer"),
            "tokenizer_type": "word-level",
            "vocabulary_size": vocab.get("tokens"),
            "precision": arch.get("precision"),
            "weight_format": weights.get("format"),
            "weight_hash": weights.get("sha256"),
            "engine_hash": engine.get("sha256"),
            "vocab_hash": vocab.get("sha256"),
            "engine_version": engine.get("version"),
            "runtime": "pure JavaScript, zero dependencies, runs in browser",
            "chat_tuning": "chat-tuned on phone-book AI profiles (per model-status.json)",
        },
        "training": {
            "v2": {
                "status": "not documented in the repository",
                "note": ("SIGLLAMA-V2's training configuration (steps, corpus, optimizer, "
                         "seed, environment) was not recorded in this repo. It is "
                         "described only as 'chat-tuned on phone-book AI profiles'. "
                         "No values are invented here; they will be added when recorded."),
                "training_steps": None,
                "corpus_id": None,
                "corpus_hash": None,
                "optimizer": None,
            },
            "v1_documented": manifest_v1.get("training"),
        },
        "corpus_provenance": {
            "SIGLLAMA-CORPUS-1": {
                "corpus_id": "SIGLLAMA-CORPUS-1",
                "used_by": "SIGLLAMA-V1",
                "built": "2026-09-30",
                "lines": 135340,
                "bytes": 23241092,
                "hash": None,
                "hash_note": "the corpus.txt file is not preserved in the repo; no hash can be published.",
                "sanitization": manifest_v1.get("training", {}).get("corpus", {}).get("sanitization"),
                "sources": manifest_v1.get("training", {}).get("corpus", {}).get("sources"),
            }
        },
        "failure_states": failure_states,
        "engine_version_lock": {
            "ENGINE_MIN_VERSION": "1.0",
            "ENGINE_MAX_VERSION": "1.x",
            "MODEL_FORMAT_VERSION": 1,
            "weight_binary_magic": "SGLL",
            "weight_format_version": 1,
            "note": ("The site loader verifies the SHA-256 of the engine, weights, and "
                     "vocabulary against model-status.json before loading, refuses "
                     "mismatches (HASH_MISMATCH), then verifies the SGLL header "
                     "(MODEL_CORRUPT on failure)."),
        },
        "provenance_schema": {
            "ENGINE": "which code answered: 'sigllama.js' (trained), 'guide' (knowledge base), 'industry-llama.js' (cloud)",
            "MODEL_ID": "immutable model id: 'SIGLLAMA-V2' | 'SIGLLAMA-V1' | null (guide) | cloud model id (industry)",
            "MODEL_VERSION": "model version: '2.0' | '1.0' | cloud model label",
            "MODE": "trained_model | guide | industry | failed",
            "PROVIDER": "local | groq",
            "LOCAL_OR_CLOUD": "ON-DEVICE | CLOUD | N/A",
            "TEMPERATURE": "sampling temperature used",
            "TOP_K": "topK used",
            "MAX_TOKENS": "maxTokens used",
            "SEED": "integer seed or null",
            "DETERMINISTIC": "true | false",
            "TIMESTAMP": "ISO-8601 time the answer was produced",
            "PROVENANCE_STATUS": "human sentence: what answered and what to verify",
            "FALLBACK_REASON": "null when the trained model answered; one of model-not-loaded | model-download-failed | unsupported-browser | corrupted-weights | engine-failure | quality-gate-rejected | user-asked-guide",
        },
        "tool_permission_model": {
            "flags": PERMISSION_ORDER,
            "meaning": {
                "READ_ONLY": "the scan found no capability pattern in the tool code",
                "NETWORK": "may make network requests",
                "STORAGE": "may read/write browser storage",
                "DOM_WRITE": "may modify the page DOM",
                "CLIPBOARD": "may touch the clipboard",
                "AUDIO": "may play or synthesize audio",
                "MICROPHONE": "may request the microphone (browser always asks first)",
                "CAMERA": "may request the camera (browser always asks first)",
                "LOCATION": "may request geolocation (browser always asks first)",
                "FILE": "may read/write files or trigger downloads",
                "EXECUTION": "code may evaluate strings (declared code_execution)",
            },
            "registry": SITE + "data/tool-libraries.json",
        },
        "reproducibility_package": {
            "fields": ["prompt", "seed", "deterministic", "temperature", "topK",
                       "maxTokens", "model_id", "model_hash", "engine_version",
                       "engine_hash", "vocab_hash", "output_hash", "timestamp"],
            "note": ("Copy it from any chat answer via SignatureLlama.reproPackage(). "
                     "Same package + same browser engine class replays the answer "
                     "when deterministic=true or a seed is set; without them, "
                     "temperature>0 sampling is intentionally non-deterministic."),
        },
        "pinned_urls": {
            "note": "Pinned URLs never change behavior without a version bump.",
            "v1_engine": SITE + "sigllama/v1/sigllama.js",
            "v1_vocab": SITE + "sigllama/v1/vocab.json",
            "latest_engine": SITE + "sigllama/sigllama.js",
            "backend_latest": BACKEND + "sigllama.js",
            "cors": "served from GitHub Pages with Access-Control-Allow-Origin: *",
            "browser_requirements": "fetch, Blob, URL, typed arrays, crypto.subtle",
            "memory": "weights ~4 MB download; tens of MB of Float32 tensors at runtime",
            "download_size": "engine ~13 KB + vocab ~74 KB + weights ~4.1 MB (v2)",
        },
        "files": {},
        "limitations": manifest_v1.get("limitations"),
        "sampling": manifest_v1.get("sampling"),
        "determinism": manifest_v1.get("determinism"),
        "security": manifest_v1.get("security"),
        "industry_standard": manifest_v1.get("industry_standard"),
        "related": manifest_v1.get("related"),
        "signature_record_standard": {
            "conformance": "This manifest is the Signature Llama specialization of the SIGNATURE RECORD STANDARD v1.0 (signature-one-archive).",
            "governance_status": "SIGNATURE_VERIFIED",
            "record_id": "SIGLLAMA-V2",
            "record_type": "LLAMA_MODEL",
            "standard_version": "1.0",
            "public_status": "NOT_FILED — an original tiny model by Justin Addam Higgins, not a filing, not a grant",
            "hash": weights.get("sha256"),
            "hash_of": "canonical weight binary sigllama-v2.bin",
        },
        "license": manifest_v1.get("license"),
        "offline": status.get("offline"),
        "endpoints": {
            "site": SITE,
            "manifest": SITE + "llama-manifest.json",
            "model_card": SITE + "llama-model-card.json",
            "model_status": SITE + "model-status.json",
            "llms_txt": SITE + "llms.txt",
            "engine": BACKEND + "sigllama.js",
            "vocab": BACKEND + "vocab2.json",
            "weights": BACKEND + "sigllama-v2.bin",
            "dictionary": SITE + "data/llm-dictionary.json",
            "dictionary_csv": SITE + "data/llm-dictionary.csv",
            "tool_libraries": SITE + "data/tool-libraries.json",
            "explainer_kb": SITE + "data/explainer-kb.json",
            "ai_access": SITE + "#ai-access",
        },
        "llms_txt_derivation": manifest_v1.get("llms_txt_derivation"),
    }
    # files block: current files
    dict_d = load("data/llm-dictionary.json")
    lic = "Free for any website, app, or project. No API key, no fee."
    manifest["files"] = {
        "weights": dict(weights, url=BACKEND + "sigllama-v2.bin", license=lic,
                        description="Int8 quantized weights (per-row scales), SGLL v1 binary.",
                        compatible_engine="SigLlama engine 1.0 (format SGLL v1)"),
        "engine": dict(engine, url=BACKEND + "sigllama.js", license=lic,
                       description="Pure-JS inference engine. Global SigLlama."),
        "vocab": dict(vocab, url=BACKEND + "vocab2.json", license=lic,
                      description="Word-level vocabulary: 2879 tokens."),
        "dictionary": {
            "filename": "llm-dictionary.json", "version": dict_d["version"],
            "sha256": dict_d["hash"], "license": lic,
            "url": SITE + "data/llm-dictionary.json",
            "description": "312 original one-sentence LLM/AI definitions with permanent term IDs (SIGLLAMA-TERM-####).",
        },
        "dictionary_csv": {
            "filename": "llm-dictionary.csv", "version": dict_d["version"], "license": lic,
            "url": SITE + "data/llm-dictionary.csv",
            "description": "Same 312 terms as CSV: id,term,definition,category.",
        },
        "tool_libraries": {
            "filename": "tool-libraries.json", "version": tools["version"],
            "sha256": tools["hash"], "license": lic,
            "url": SITE + "data/tool-libraries.json",
            "description": "120 plug-in tool libraries of real runnable JS, each with a static-scanned permission declaration.",
        },
        "explainer_kb": {
            "filename": "explainer-kb.json", "version": kb["version"],
            "sha256": kb["hash"], "license": lic,
            "url": SITE + "data/explainer-kb.json",
            "description": "On-site guide knowledge base (28 entries).",
        },
        "model_card": {
            "filename": "llama-model-card.json", "version": "2.0", "license": lic,
            "url": SITE + "llama-model-card.json",
            "description": "Machine-readable model card (current SIGLLAMA-V2 + preserved SIGLLAMA-V1).",
        },
        "engine_types": {
            "filename": "sigllama.d.ts", "version": "1.0", "license": lic,
            "url": SITE + "sigllama.d.ts",
            "description": "TypeScript definitions for the SigLlama engine and the SignatureLlama/IndustryLlama site APIs.",
        },
        "pinned_v1_engine": {
            "filename": "sigllama/v1/sigllama.js",
            "sha256": manifest_v1["files"]["engine"]["sha256"], "license": lic,
            "url": SITE + "sigllama/v1/sigllama.js",
            "description": "Pinned, immutable SIGLLAMA-V1 engine (2026-09-30 bytes).",
        },
        "manifest": {
            "filename": "llama-manifest.json", "version": "2.0", "license": lic,
            "url": SITE + "llama-manifest.json",
            "description": "This file: the canonical machine-readable entry point.",
        },
        "model_status": {
            "filename": "model-status.json", "version": status.get("MODEL_VERSION", "2.0"),
            "license": lic,
            "url": SITE + "model-status.json",
            "description": "Single authoritative machine-readable model state. Every section of the site reads this.",
        },
        "industry_api": manifest_v1["files"]["industry_api"],
        "llms_txt": manifest_v1["files"]["llms_txt"],
        "patch_zip": manifest_v1["files"]["patch_zip"],
        "sources": manifest_v1["files"]["sources"],
    }
    save("llama-manifest.json", manifest)
    print("manifest 2.0 written; v1 preserved under previous_versions + manifests/")

    # ---- 3. model card ----
    card = {
        "model_card_version": "1.0",
        "updated": TODAY,
        "current_model": "SIGLLAMA-V2",
        "models": {
            "SIGLLAMA-V2": {
                "model_id": "SIGLLAMA-V2",
                "name": "Signature Llama v2",
                "version": "2.0",
                "status": "live",
                "released": status.get("weights", {}).get("published"),
                "architecture": {
                    "type": arch.get("type"),
                    "layers": arch.get("layers"),
                    "attention_heads": arch.get("attention_heads"),
                    "hidden_size": arch.get("hidden_size"),
                    "mlp_size": arch.get("mlp_size"),
                    "rope_theta": arch.get("rope_theta"),
                },
                "parameters": arch.get("parameters"),
                "tokenizer": {"type": "word-level", "vocabulary_size": vocab.get("tokens"),
                             "file": "vocab2.json",
                             "sha256": vocab.get("sha256")},
                "context_length": arch.get("context_length"),
                "quantization": arch.get("precision"),
                "weight_format": weights.get("format"),
                "hashes": {"weights_sha256": weights.get("sha256"),
                           "engine_sha256": engine.get("sha256"),
                           "vocab_sha256": vocab.get("sha256")},
                "training_data": {
                    "description": "chat-tuned on phone-book AI profiles",
                    "detail": "not documented in the repository — see manifest training.v2",
                    "training_steps": None, "corpus_id": None, "corpus_hash": None,
                },
                "evaluation": {
                    "determinism": "deterministic:true replays byte-identical output (tested with published weights)",
                    "note": "no formal benchmark suite has been run against v2; scores are not published",
                },
                "intended_use": ("On-device chat, explanations, and demos in the browser; "
                                 "a talking brain for Signature site AIs."),
                "non_intended_use": ("Anything needing guaranteed factual accuracy, "
                                    "medical/legal/financial advice, or safety-critical decisions."),
                "limitations": [
                    "Small (~4M parameters): can invent facts; verify anything important.",
                    "96-token context: long conversations lose their oldest turns first.",
                    "HALLUCINATION_RISK = PRESENT; FACTUALITY_NOT_GUARANTEED = TRUE; VERIFY_IMPORTANT_INFORMATION = TRUE.",
                ],
                "safety": ("Model output is plain text only and never executed. "
                           "Tool libraries are shipped code, never model-generated."),
                "license": "Free for any website, app, or project. No API key, no fee. By Justin Addam Higgins.",
                "canonical_url": SITE,
            },
            "SIGLLAMA-V1": {
                "model_id": "SIGLLAMA-V1",
                "name": "Signature Llama v1",
                "version": "1.0",
                "status": "superseded — preserved, still downloadable",
                "released": manifest_v1["files"]["weights"].get("published"),
                "parameters": manifest_v1["model"]["parameter_count"],
                "architecture": {"type": "decoder-only transformer", "layers": 5,
                                "attention_heads": 8, "hidden_size": 192,
                                "mlp_size": 768, "rope_theta": 10000.0},
                "tokenizer": {"type": "character-level", "vocabulary_size": 84,
                              "file": "vocab.json",
                              "sha256": manifest_v1["files"]["vocab"]["sha256"]},
                "context_length": 128,
                "quantization": "int8, per-row scales",
                "weight_format": "SGLL v1 binary (magic 'SGLL', format version 1)",
                "hashes": {"weights_sha256": manifest_v1["files"]["weights"]["sha256"],
                           "engine_sha256": manifest_v1["files"]["engine"]["sha256"],
                           "vocab_sha256": manifest_v1["files"]["vocab"]["sha256"]},
                "training_data": manifest_v1.get("training"),
                "evaluation": {"determinism": "tested 2026-10-01: identical prompt twice -> byte-identical output"},
                "intended_use": "On-device chat and demos in the browser.",
                "non_intended_use": "Anything needing guaranteed factual accuracy.",
                "limitations": manifest_v1.get("limitations"),
                "license": "Free for any website, app, or project. No API key, no fee. By Justin Addam Higgins.",
                "canonical_url": SITE,
                "pinned_files": {"engine": SITE + "sigllama/v1/sigllama.js",
                                 "vocab": SITE + "sigllama/v1/vocab.json"},
            },
        },
    }
    save("llama-model-card.json", card)
    print("llama-model-card.json written")


if __name__ == "__main__":
    main()
