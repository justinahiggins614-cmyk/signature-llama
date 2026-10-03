#!/usr/bin/env bash
# Build the complete Signature Llama v2 reproducible release package.
# Produces patch/signature-llama-patch-v2.zip + patch/signature-llama-patch-v2.zip.sha256
# Run from the repo root:  bash patch/build_patch_v2.sh
#
# The ZIP contains: the pinned v2 engine/weights/vocab, the preserved v1
# files, sources, data (dictionary, knowledge base, tool registry), the APIs,
# the manifest, the model card, the llms.txt, a README, and a MANIFEST.json
# with SHA-256 hashes of every file. The .sha256 file holds the ZIP's own hash.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$ROOT/patch/stage-v2"
OUT="$ROOT/patch/signature-llama-patch-v2.zip"

rm -rf "$STAGE"
mkdir -p "$STAGE/engine" "$STAGE/weights" "$STAGE/v1" "$STAGE/src" "$STAGE/data" \
         "$STAGE/manifests" "$STAGE/patch"

# --- current release: SIGLLAMA-V2 (local files win; they are byte-identical to published) ---
cp "$ROOT/sigllama/sigllama.js"  "$STAGE/engine/sigllama.js"
cp "$ROOT/sigllama/vocab2.json"  "$STAGE/engine/vocab2.json"
cp "$ROOT/sigllama/sigllama-v2.bin" "$STAGE/weights/sigllama-v2.bin"

# --- preserved v1 (never overwritten under the same version) ---
cp "$ROOT/sigllama/v1/sigllama.js" "$STAGE/v1/sigllama.js"
cp "$ROOT/sigllama/v1/vocab.json"  "$STAGE/v1/vocab.json"
cp "$ROOT/sigllama/v1/README.txt"  "$STAGE/v1/README.txt"
cp "$ROOT/sigllama/sigllama-v1.bin" "$STAGE/v1/sigllama-v1.bin"

# --- sources, data, APIs ---
cp "$ROOT"/src/*.py "$STAGE/src/"
cp "$ROOT/src/sigllama.js" "$STAGE/src/sigllama-v1-engine.js"
cp "$ROOT/data/llm-dictionary.json" "$ROOT/data/llm-dictionary.csv" \
   "$ROOT/data/explainer-kb.json" "$ROOT/data/tool-libraries.json" "$STAGE/data/"
cp "$ROOT/llama-api.js" "$ROOT/industry-llama.js" "$ROOT/sigllama.d.ts" "$STAGE/"

# --- identity documents ---
cp "$ROOT/llama-manifest.json" "$ROOT/llama-model-card.json" \
   "$ROOT/model-status.json" "$ROOT/llms.txt" "$STAGE/"
cp "$ROOT/manifests/llama-manifest-v1.json" "$STAGE/manifests/"
cp "$ROOT/patch/PATCH_NOTES.txt" "$ROOT/patch/embed-snippet.html" "$STAGE/patch/"

# --- README ---
cat > "$STAGE/README.txt" <<'EOF'
Signature Llama — complete reproducible release package (SIGLLAMA-V2 current, SIGLLAMA-V1 preserved)
Independent model by Justin Addam Higgins. Not affiliated with Meta.

WHAT IS WHERE
  engine/            pinned v2 engine (sigllama.js) + vocab2.json
  weights/           sigllama-v2.bin — the current trained weights
  v1/                preserved v1 engine + vocab + weights (never changes)
  src/               original training/inference sources (v1-era, preserved)
  data/              llm-dictionary.json (+ .csv), explainer-kb.json, tool-libraries.json
  llama-api.js       on-demand ask API (SignatureLlama.ask / askWithProvenance)
  industry-llama.js  cloud client for "Llama · Industry Standard" (NOT the on-device model)
  sigllama.d.ts      TypeScript definitions for the engine + site APIs
  llama-manifest.json    canonical machine-readable entry point (manifest 2.0)
  llama-model-card.json  machine-readable model card (SIGLLAMA-V2 + SIGLLAMA-V1)
  manifests/llama-manifest-v1.json  the preserved v1 manifest
  model-status.json  single authoritative live model state
  llms.txt           plain-words summary for AI readers
  MANIFEST.json      every file in this ZIP with its SHA-256 (verify against it)

VERIFY
  sha256sum -c <(grep -v '^#' /dev/null)  # or compare each file's hash to MANIFEST.json
  The v2 weights hash must be e351a9e1133a1774782d9f6f0e77f6ab756ca769af59fbbe763f6321e32d7049
  and the v2 engine hash a8bc903a244c7f2ea8575100433548bfe238a468fb0012a956be6e986a47e50b.

QUICK START
  See patch/embed-snippet.html, or the Developers section on the site.

LICENSE
  Free for any website, app, or project. No API key, no fee.
EOF

# --- MANIFEST.json: every file + its SHA-256 ---
python3 - "$STAGE" <<'PYEOF'
import hashlib, json, os, sys
stage = sys.argv[1]
files = []
for dirpath, _dirs, names in os.walk(stage):
    for n in sorted(names):
        full = os.path.join(dirpath, n)
        rel = os.path.relpath(full, stage)
        h = hashlib.sha256()
        with open(full, 'rb') as f:
            for c in iter(lambda: f.read(1 << 20), b''):
                h.update(c)
        files.append({'path': rel, 'sha256': h.hexdigest(),
                      'size_bytes': os.path.getsize(full)})
manifest = {
    'package': 'signature-llama-patch-v2.zip',
    'model_id': 'SIGLLAMA-V2',
    'model_version': '2.0',
    'previous_model': 'SIGLLAMA-V1',
    'created': __import__('datetime').date.today().isoformat(),
    'license': 'Free for any website, app, or project. No API key, no fee.',
    'compatibility': {
        'engine_version': '1.0',
        'engine_min_version': '1.0',
        'engine_max_version': '1.x',
        'model_format_version': 1,
        'browser': 'fetch, Blob, URL, typed arrays, crypto.subtle',
        'note': 'v2 weights require vocab2.json (2879 tokens); v1 weights require vocab.json (84 tokens). Never mix.',
    },
    'files': files,
}
with open(os.path.join(stage, 'MANIFEST.json'), 'w') as f:
    json.dump(manifest, f, indent=1)
    f.write('\n')
print('MANIFEST.json:', len(files), 'files')
PYEOF

rm -f "$OUT"
(cd "$STAGE" && zip -qr "$OUT" .)
rm -rf "$STAGE"
( cd "$ROOT/patch" && sha256sum signature-llama-patch-v2.zip | awk '{print $1}' > signature-llama-patch-v2.zip.sha256 )
echo "built: $OUT"
ls -la "$OUT" "$OUT.sha256"
