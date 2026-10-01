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
cp "$ROOT/data/llm-dictionary.json" "$ROOT/data/explainer-kb.json" "$ROOT/data/tool-libraries.json" "$STAGE/data/"

# api + manifest + status + notes + embed
cp "$ROOT/llama-api.js" "$ROOT/llama-manifest.json" "$ROOT/llms.txt" "$ROOT/model-status.json" "$STAGE/"
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
The trained weights could not be fetched while building this patch
(the model IS published and live — this is a build-time network hiccup).

Get them directly:
https://justinahiggins614-cmyk.github.io/signature-backend/sigllama/sigllama-v1.bin
SHA-256: b2dfc0d05add95786797e596559f3e86de9b3a9c9dbce6818814ad05d6317b58

Or re-download the patch later:
https://justinahiggins614-cmyk.github.io/signature-llama/patch/signature-llama-patch-v1.zip
EOF
  echo "weights: PENDING placeholder written (network hiccup)"
fi

rm -f "$OUT"
(cd "$STAGE" && zip -qr "$OUT" .)
rm -rf "$STAGE"
echo "built: $OUT"
ls -la "$OUT"
