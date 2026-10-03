#!/usr/bin/env python3
"""Generate llms.txt from llama-manifest.json + model-status.json.
The manifest is the single source of truth; do not hand-edit llms.txt.
Run: python3 build_llms.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
m = json.load(open(os.path.join(HERE, 'llama-manifest.json')))
s = json.load(open(os.path.join(HERE, 'model-status.json')))
nterms = len(json.load(open(os.path.join(HERE, 'data', 'llm-dictionary.json')))['terms'])
nlibs = len(json.load(open(os.path.join(HERE, 'data', 'tool-libraries.json')))['libraries'])
arch = m['model']
tok = arch.get('tokenizer', '')
failures = '\n'.join('  - %s: %s' % (k, v['meaning']) for k, v in m['failure_states'].items())
SITE = 'https://justinahiggins614-cmyk.github.io/signature-llama/'
tr = m.get('training', {}).get('v2', {})
cp = m.get('corpus_provenance', {}).get('SIGLLAMA-CORPUS-2', {})
prev = (m.get('previous_versions') or [{}])[0]

txt = """# Signature Llama: The Fully Cyber Utilizable AI
# Generated from llama-manifest.json + model-status.json by build_llms.py — do not hand-edit.

Signature Llama v2 (SIGLLAMA-V2) is a tiny transformer language model built and
trained from scratch by Justin Addam Higgins, chat-tuned on phone-book AI
profiles. Independent model — not affiliated with Meta or the LLaMA family.

STATUS: {status} (see model-status.json: MODEL_STATUS={ms}, MODEL_VERSION={mv},
WEIGHTS_AVAILABLE={wa}, GUIDE_AVAILABLE={ga}, API_AVAILABLE={aa})

MODEL FACTS (current: SIGLLAMA-V2)
- Parameters: {params:,} (~4M), {layers} layers, {heads} attention heads,
  hidden size {hidden}, context {ctx} words, vocab {vocab} ({toktype})
- Weights: int8 per-row scales, SGLL v1 binary, {wbytes:,} bytes
- Weights SHA-256: {whash}
- Engine: sigllama.js (pure JavaScript, zero dependencies), SHA-256 {ehash}
- Vocab: vocab2.json (2,879 word tokens), SHA-256 {vhash}
- Training: {steps:,} steps on {examples:,} persona-dialogue examples ({tokens}
  tokens) distilled from the phone book's 270 AI profiles; validation loss
  {valloss} ({epochs} epochs); weights published {wpublished}.
  Corpus: {corpus} (hash not published — corpus file not preserved in repo).
- Previous model: {prev_id} ({prev_params:,} params) — preserved, still
  downloadable; see manifests/llama-manifest-v1.json.
- License: free for any website, app, or project. No API key, no fee.
  Currently free for all internet tasks.

CAPABILITY BOUNDARY
- MODEL = local text generation only: no network, no files, no device access.
- TOOLS = optional plug-in tool libraries ({nlibs}); only the ones you load run,
  only as ordinary page JavaScript, each with a formal permission declaration.
- DEFAULT = no network calls.

ENGINE MODES — every answer is labeled
- trained_model: the real SIGLLAMA-V2 weights running in the browser, labeled
  "✦ Trained Llama v2 · SIGLLAMA-V2 · LOCAL · ON-DEVICE".
- guide: the on-site knowledge-base guide (28 entries), used when you ask the
  guide, or as fallback if the trained model cannot load. Always labeled
  "Guide:" — never called a Llama model.
- industry: the cloud option, labeled "⬢ Industry Standard · <model> · CLOUD ·
  REMOTE (Groq)". NOT the on-device Signature Llama.
- Every answer carries machine-readable provenance: ENGINE, MODEL_ID,
  MODEL_VERSION, MODE, PROVIDER, LOCAL_OR_CLOUD, TEMPERATURE, TOP_K,
  MAX_TOKENS, SEED, DETERMINISTIC, TIMESTAMP, PROVENANCE_STATUS,
  FALLBACK_REASON. See SignatureLlama.askWithProvenance().

DATA ON THIS SITE (counts read from the data files at generation time)
- LLM/AI dictionary: {nterms} original terms with permanent IDs
  (SIGLLAMA-TERM-0001..) — data/llm-dictionary.json (+ .csv)
- Tool libraries: {nlibs} runnable plug-ins, each with a formal permission
  declaration and a SHA-256 of its code (data/tool-libraries.json)

INDUSTRY STANDARD — the cloud option (NOT the on-device model)
- The site chat has a model picker: "✦ Signature Llama v2 · on-device"
  (LOCAL · ON-DEVICE, no key) vs "⬢ Llama · Industry Standard" (CLOUD ·
  REMOTE, via Groq).
- Industry Standard = the full-scale Llama the industry runs (default Llama 3.3
  70B; Llama 4 Maverick / Llama 4 Scout selectable), served live from the cloud
  by Groq at https://api.groq.com/openai/v1/chat/completions.
- NEEDS A FREE API KEY (bring-your-own, from https://console.groq.com/keys).
  The key lives only in the user's browser localStorage and is sent ONLY to
  api.groq.com. Never in analytics, error logs, URLs, chat history, or saved
  transcripts. A "Remove key" / "Clear all cloud credentials" button clears it.
- Every Industry Standard reply is labeled "⬢ Industry Standard · <model> ·
  CLOUD · REMOTE (Groq)" — impossible to confuse with the local model. The
  cloud system prompt forbids claiming to be the small on-device v2. Llama
  weights are by Meta; the site is independent, not affiliated with Meta.
- Client: industry-llama.js. SignatureLlama.askIndustry(question) answers via
  the cloud; SignatureLlama.industryReady() reports whether a key is saved.

NAMED FAILURE STATES (no silent failures)
{failures}

USE IT
1. Read the manifest first (machine-readable, start here):
   {site}llama-manifest.json
2. Model state (single authority):
   {site}model-status.json
3. Model card (machine-readable):
   {site}llama-model-card.json
4. Ask on demand (no model download needed):
   <script src="{site}llama-api.js"></script>
   <script>
     SignatureLlama.ask("What is a token?").then(function(answer){{
       console.log(answer);
     }});
   </script>
   SignatureLlama.askWithProvenance(question, opts) returns the answer plus
   the full provenance record. Options: allowFallback, requireModel,
   deterministic, seed, temperature, topK, maxTokens, timeoutMs.
   SignatureLlama.mode() reports the mode.
   SignatureLlama.verifyIntegration() proves the same engine+weights
   automatically (for the Telephone Book's hash check).
5. Run the trained model yourself (pinned to SIGLLAMA-V2 explicitly):
   <script src="{engine_url}"></script>
   <script type="module">
     // type="module" is REQUIRED for the top-level await below.
     await SigLlama.load("{base}", "vocab2.json", "sigllama-v2.bin");
     const text = await SigLlama.generate("Hello,", {{ maxTokens: 80, temperature: 0.8, topK: 40 }});
   </script>
   Deterministic: pass deterministic:true (forces temperature 0) or seed:<n>.
   Sampling arguments are validated with named INVALID_ARGUMENT errors.
6. The same engine + weights are the talking brain inside every AI in the
   Signature AI Telephone Book — verified automatically by hash, not by claim.

HONEST LIMITS
- v2 is small and lively — like a bright intern. It can invent facts; verify
  anything important. HALLUCINATION_RISK=PRESENT,
  FACTUALITY_NOT_GUARANTEED=TRUE, VERIFY_IMPORTANT_INFORMATION=TRUE.
- 96-word context: prompts are left-truncated to fit; long chats lose the
  oldest turns first. CHAT HISTORY (12 turns kept) is not MODEL CONTEXT.
- temperature <= 0 means greedy argmax (fully deterministic); otherwise
  sampling is intentionally non-deterministic unless deterministic:true/seed.
- First load needs internet; offline afterwards depends on the browser cache
  and has not been lab-tested.

Independent model by Justin Addam Higgins. Not affiliated with Meta.
""".format(
    status=m['model_status'].upper(), ms=s['MODEL_STATUS'], mv=s['MODEL_VERSION'],
    wa=s['WEIGHTS_AVAILABLE'], ga=s['GUIDE_AVAILABLE'], aa=s['API_AVAILABLE'],
    params=arch['parameter_count'], layers=arch['layers'], heads=arch['attention_heads'],
    hidden=arch['hidden_size'], ctx=arch['context_length'], vocab=arch['vocabulary_size'],
    toktype=('word-level' if arch.get('tokenizer_type') == 'word-level' else tok),
    wbytes=m['files']['weights']['size_bytes'], whash=arch['weight_hash'],
    ehash=m['files']['engine']['sha256'], vhash=arch['vocab_hash'], failures=failures,
    nterms=nterms, nlibs=nlibs,
    steps=tr.get('training_steps') or 0, examples=cp.get('examples') or 0,
    tokens=cp.get('tokens') or '?', valloss=tr.get('best_val_loss'),
    epochs=tr.get('epochs'), wpublished=s.get('weights', {}).get('published'),
    corpus=tr.get('corpus_id'),
    prev_id=prev.get('model_id'), prev_params=prev.get('parameters') or 0,
    site=SITE,
    engine_url='https://justinahiggins614-cmyk.github.io/signature-backend/sigllama/sigllama.js',
    base='https://justinahiggins614-cmyk.github.io/signature-backend/sigllama/')

out = os.path.join(HERE, 'llms.txt')
open(out, 'w').write(txt)
print('wrote', out, len(txt), 'bytes')
