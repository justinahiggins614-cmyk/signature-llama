#!/usr/bin/env python3
"""Python side of the parity test: greedy-generate from best.pt, print output."""
import sys, torch
sys.path.insert(0, "/home/hatch/workspace/sigllama")
from tokenizer import load as vload, encode, decode
from model import SigLlama

def main(prompt, max_new):
    vocab = vload(); V = len(vocab["itos"])
    m = SigLlama(V, d=192, layers=5, heads=8, seq=128)
    sd = torch.load("/home/hatch/workspace/sigllama/checkpoints/best.pt",
                    map_location="cpu", weights_only=True)
    m.load_state_dict(sd); m.eval()
    ids = [vocab["bos_id"]] + encode(prompt, vocab)
    idx = torch.tensor([ids], dtype=torch.long)
    with torch.no_grad():
        out = m.generate(idx, max_new, temperature=0)
    print(decode(out[0].tolist(), vocab))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "the",
         int(sys.argv[2]) if len(sys.argv) > 2 else 40)
