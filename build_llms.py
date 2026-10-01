#!/usr/bin/env python3
"""Generate llms.txt from llama-manifest.json + model-status.json.
The manifest is the single source of truth; do not hand-edit llms.txt.
Run: python3 build_llms.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
m = json.load(open(os.path.join(HERE, 'llama-manifest.json')))
s = json.load(open(os.path.join(HERE, 'model-status.json')))
arch = m['model']
failures = '\n'.join('  - %s: %s' % (k, v['meaning']) for k, v in m['failure_states'].items())

txt = """# Signature Llama: The Fully Cyber Utilizable AI
# Generated from llama-manifest.json + model-status.json by build_llms.py — do not hand-edit.

Signature Llama v1 (SIGLLAMA-V1) is a tiny transformer language model built and
trained from scratch by Justin Addam Higgins on the IWB Dictionary and Signature
spec text. Independent model — not affiliated with Meta or the LLaMA family.

STATUS: {status} (see model-status.json: MODEL_STATUS={ms}, MODEL_VERSION={mv},
WEIGHTS_AVAILABLE={wa}, GUIDE_AVAILABLE={ga}, API_AVAILABLE={aa})

MODEL FACTS
- Parameters: {params:,} (~3M), {layers} layers, {heads} attention heads,
  hidden size {hidden}, context {ctx} tokens, vocab {vocab} (character-level)
- Weights: int8 per-row scales, SGLL v1 binary, {wbytes:,} bytes
- Weights SHA-256: {whash}
- Engine: sigllama.js (pure JavaScript, zero dependencies), SHA-256 {ehash}
- Training: 12,890 steps on a 135,340-line / 23.2 MB creator-authored corpus
  (IWB Dictionary definitions + Signature spec text, seed 614), finished
  2026-09-30; weights published 2026-09-30 22:39 EDT.
- License: free for any website, app, or project. No API key, no fee.
  Currently free for all internet tasks.

CAPABILITY BOUNDARY
- MODEL = local text generation only: no network, no files, no device access.
- TOOLS = optional plug-in tool libraries (120); only the ones you load run,
  only as ordinary page JavaScript, each with declared capabilities.
- DEFAULT = no network calls.

ENGINE MODES — every answer is labeled
- trained_model: the real SIGLLAMA-V1 weights running in the browser.
- guide: the on-site knowledge-base guide (28 entries), used when you ask the
  guide, or as fallback if the trained model cannot load. The site always says
  which engine answered.

NAMED FAILURE STATES (no silent failures)
{failures}

USE IT
1. Read the manifest first (machine-readable, start here):
   {site}llama-manifest.json
2. Model state (single authority):
   {site}model-status.json
3. Ask on demand (no model download needed):
   <script src="{site}llama-api.js"></script>
   <script>
     SignatureLlama.ask("What is a token?").then(function(answer){{
       console.log(answer);
     }});
   </script>
   SignatureLlama.askWithProvenance(question) also returns the engine, mode,
   model version, and provenance. SignatureLlama.mode() reports the mode.
4. Run the trained model yourself:
   <script src="{engine_url}"></script>
   <script type="module">
     // type="module" is REQUIRED for the top-level await below.
     await SigLlama.load("{base}");
     const text = await SigLlama.generate("Hello,", {{ maxTokens: 80, temperature: 0.8, topK: 40 }});
   </script>
   Deterministic: pass deterministic:true (forces temperature 0) or seed:<n>.
5. The same engine + weights are the talking brain inside every AI in the
   Signature AI Telephone Book (same base URL, same SHA-256).

HONEST LIMITS
- v1 is small, lively, and a little quirky — like a bright intern. It can
  invent facts; verify anything important.
- 128-token context: prompts are left-truncated to fit; long chats lose the
  oldest turns first.
- temperature <= 0 means greedy argmax (fully deterministic); otherwise
  sampling is intentionally non-deterministic unless deterministic:true/seed.
- First load needs internet; offline afterwards depends on the browser cache.

Independent model by Justin Addam Higgins. Not affiliated with Meta.
""".format(
    status=m['model_status'].upper(), ms=s['MODEL_STATUS'], mv=s['MODEL_VERSION'],
    wa=s['WEIGHTS_AVAILABLE'], ga=s['GUIDE_AVAILABLE'], aa=s['API_AVAILABLE'],
    params=arch['parameter_count'], layers=arch['layers'], heads=arch['attention_heads'],
    hidden=arch['hidden_size'], ctx=arch['context_length'], vocab=arch['vocabulary_size'],
    wbytes=m['files']['weights']['size_bytes'], whash=arch['weight_hash'],
    ehash=m['files']['engine']['sha256'], failures=failures,
    site='https://justinahiggins614-cmyk.github.io/signature-llama/',
    engine_url='https://justinahiggins614-cmyk.github.io/signature-backend/sigllama/sigllama.js',
    base='https://justinahiggins614-cmyk.github.io/signature-backend/sigllama/')

out = os.path.join(HERE, 'llms.txt')
open(out, 'w').write(txt)
print('wrote', out, len(txt), 'bytes')
