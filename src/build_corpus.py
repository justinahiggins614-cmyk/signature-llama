#!/usr/bin/env python3
"""Build SigLlama v1 training corpus from Manon's own data:
- The Signature Dictionary definitions (all.jsonl)
- Spec catalog volumes (abstracts, autoread blocks, AI explainer text)
Target ~20MB of clean plain text, one record per line, deduped, shuffled.
"""
import gzip, json, os, random, re, glob

OUT = os.path.expanduser("~/workspace/sigllama/corpus.txt")
TARGET_BYTES = 22 * 1024 * 1024

URL_RE = re.compile(r"https?://\S+")
WS_RE = re.compile(r"\s+")

def clean(s, maxlen=420):
    if not s: return ""
    s = URL_RE.sub("", s)
    s = WS_RE.sub(" ", s).strip()
    if len(s) < 20 or len(s) > maxlen: return ""
    # drop lines dominated by non-text
    letters = sum(1 for c in s if c.isalpha() or c.isspace())
    if letters < 0.6 * len(s): return ""
    return s

def main():
    random.seed(614)
    seen = set()
    lines = []

    # 1) Dictionary definitions
    dict_path = os.path.expanduser("~/workspace/jah-dictionary/data/definitions/all.jsonl")
    n_dict = 0
    with open(dict_path) as f:
        for raw in f:
            raw = raw.strip()
            if not raw: continue
            try: rec = json.loads(raw)
            except Exception: continue
            w = rec.get("w", ""); pos = rec.get("pos", "")
            for d in rec.get("d", []) or []:
                t = clean(f"{w} ({pos}): {d}")
                if t and t not in seen:
                    seen.add(t); lines.append(t); n_dict += 1
    print(f"dict lines: {n_dict}, bytes: {sum(len(l) for l in lines)}")

    # 2) Spec volumes - sample evenly to reach target
    vols = sorted(glob.glob(os.path.expanduser(
        "~/workspace/signature-one-archive/data/volumes/specs-c*.jsonl.gz")))
    print(f"volumes: {len(vols)}")
    remaining = TARGET_BYTES - sum(len(l) for l in lines)
    per_vol = max(1, remaining // (len(vols) * 3))  # 3 text fields each
    n_spec = 0
    for vf in vols:
        try:
            fh = gzip.open(vf, "rt", encoding="utf-8", errors="replace")
        except Exception:
            continue
        texts = []
        for raw in fh:
            raw = raw.strip()
            if not raw: continue
            try: rec = json.loads(raw)
            except Exception: continue
            for key in ("abstract", "autoread_block", "ai_explainer"):
                v = rec.get(key)
                if isinstance(v, str):
                    texts.append(v)
                elif isinstance(v, list):
                    texts.extend(str(x) for x in v if isinstance(x, str))
        fh.close()
        if not texts: continue
        random.shuffle(texts)
        take = max(2, min(len(texts), per_vol * 6))
        for t in texts[:take]:
            c = clean(t)
            if c and c not in seen:
                seen.add(c); lines.append(c); n_spec += 1
        if sum(len(l) for l in lines) >= TARGET_BYTES:
            break
    print(f"spec lines: {n_spec}")

    random.shuffle(lines)
    with open(OUT, "w", encoding="utf-8") as f:
        for l in lines:
            f.write(l + "\n")
    size = os.path.getsize(OUT)
    print(f"wrote {OUT}: {len(lines)} lines, {size/1024/1024:.1f} MB")

if __name__ == "__main__":
    main()
