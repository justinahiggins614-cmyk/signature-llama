#!/usr/bin/env bash
# Build the whole Signature Llama patch in one command.
# Produces patch/signature-llama-patch-v1.zip
# Run from the repo root:  bash patch/build_patch.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$ROOT/patch/stage"
OUT="$ROOT/patch/signature-llama-patch-v1.zip"
BACKEND="https://justinahiggins614-cmyk.github.io/signature-backend/sigllama"

rm -rf "$STAGE"
mkdir -p "$STAGE/engine" "$STAGE/weights" "$STAGE/src" "$STAGE/data"

# engine + vocab + sources (always present)
cp "$ROOT/src/sigllama.js" "$STAGE/engine/"
cp "$ROOT/src/vocab.json" "$STAGE/"
cp "$ROOT"/src/*.py "$STAGE/src/"

# data
cp "$ROOT/data/llm-dictionary.json" "$ROOT/data/explainer-kb.json" "$STAGE/data/"

# api + manifest + notes + embed
cp "$ROOT/llama-api.js" "$ROOT/llama-manifest.json" "$ROOT/llms.txt" "$STAGE/"
cp "$ROOT/patch/PATCH_NOTES.txt" "$ROOT/patch/embed-snippet.html" "$STAGE/"

# weights: local file wins, else try the published backend, else placeholder
if [ -f "$ROOT/src/sigllama-v1.bin" ]; then
  cp "$ROOT/src/sigllama-v1.bin" "$STAGE/weights/"
  echo "weights: local src/sigllama-v1.bin"
elif curl -sfI --max-time 20 "$BACKEND/sigllama-v1.bin" >/dev/null 2>&1; then
  curl -sfL --max-time 120 -o "$STAGE/weights/sigllama-v1.bin" "$BACKEND/sigllama-v1.bin"
  echo "weights: downloaded from published backend"
else
  cat > "$STAGE/weights/WEIGHTS_PENDING.txt" <<'EOF'
The trained weights are not published yet — the Llama is still training.

Check the live status pill at:
https://justinahiggins614-cmyk.github.io/signature-llama/

When it flips to LIVE, re-download the patch:
https://justinahiggins614-cmyk.github.io/signature-llama/patch/signature-llama-patch-v1.zip
and the real int8 sigllama-v1.bin will be inside this folder.

In the meantime, everything else in this patch works:
the engine, the sources, the dictionary, the knowledge base,
and SignatureLlama.ask() (knowledge-base answers).
EOF
  echo "weights: PENDING placeholder written"
fi

rm -f "$OUT"
(cd "$STAGE" && zip -qr "$OUT" .)
rm -rf "$STAGE"
echo "built: $OUT"
ls -la "$OUT"
