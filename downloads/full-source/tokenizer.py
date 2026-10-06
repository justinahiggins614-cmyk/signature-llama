#!/usr/bin/env python3
"""Character-level tokenizer for Signature Llama v1. Built from the corpus."""
import json, os
from collections import Counter

WORK = os.path.expanduser("~/workspace/sigllama")
VOCAB_PATH = os.path.join(WORK, "vocab.json")

SPECIALS = ["<BOS>", "<EOS>", "<PAD>"]
UNK_CHAR = "?"

def build(corpus_path=os.path.join(WORK, "corpus.txt")):
    c = Counter()
    with open(corpus_path, encoding="utf-8") as f:
        for line in f:
            c.update(line.rstrip("\n"))
    # keep chars with count >= 3, drop control chars except space
    chars = sorted([ch for ch, n in c.items()
                    if n >= 3 and (ch == " " or 33 <= ord(ch) <= 126)],
                   key=lambda ch: -c[ch])
    itos = SPECIALS + chars
    if UNK_CHAR not in itos:
        itos.append(UNK_CHAR)
    stoi = {s: i for i, s in enumerate(itos)}
    vocab = {"itos": itos, "stoi": stoi, "unk_id": stoi[UNK_CHAR],
             "bos_id": 0, "eos_id": 1, "pad_id": 2}
    with open(VOCAB_PATH, "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False)
    print(f"vocab size: {len(itos)} -> {VOCAB_PATH}")
    return vocab

def load(path=VOCAB_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def encode(text, vocab):
    stoi, unk = vocab["stoi"], vocab["unk_id"]
    return [stoi.get(ch, unk) for ch in text]

def decode(ids, vocab):
    itos = vocab["itos"]
    return "".join(itos[i] if 0 <= i < len(itos) else "?" for i in ids)

if __name__ == "__main__":
    build()
