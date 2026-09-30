#!/usr/bin/env python3
"""Export trained Signature Llama v1 to a compact int8 binary for the browser.
Layout (little-endian):
  magic "SGLL", u32 version=1
  u32 vocab, u32 d_model, u32 n_layers, u32 n_heads, u32 seq_max,
  f32 rope_theta, u32 mlp_hidden
  u32 tensor_count
  per tensor: u8 name_len, name bytes, u8 ndim, u32 dims[ndim],
              u8 kind (0=int8,1=f32), u32 n_scales, f32 scales[n_scales],
              u32 data_len, data[data_len]
Linear weights: per-output-row symmetric int8 quantization.
"""
import json, os, struct
import torch

WORK = os.path.expanduser("~/workspace/sigllama")

def quantize_int8_per_row(w):
    # w: (out, in) float tensor -> (q int8, scales float32 per row)
    amax = w.abs().amax(dim=1).clamp_min(1e-8)
    scale = amax / 127.0
    q = torch.clamp((w / scale[:, None]).round(), -127, 127).to(torch.int8)
    return q, scale

def main(which="best"):
    from tokenizer import load as vload
    from model import SigLlama
    vocab = vload(); V = len(vocab["itos"])
    cfg = dict(d=192, layers=5, heads=8, seq=128, theta=10000.0, mlp_mult=4)
    try:
        with open(os.path.join(WORK, "train_meta.json")) as f:
            meta = json.load(f)
        for k in ("d", "layers", "heads", "seq", "theta", "mlp_mult"):
            if k in meta.get("cfg", {}):
                cfg[k] = meta["cfg"][k]
    except Exception:
        pass
    m = SigLlama(V, d=cfg["d"], layers=cfg["layers"], heads=cfg["heads"],
                 seq=cfg["seq"], theta=cfg["theta"], mlp_mult=cfg["mlp_mult"])
    if which != "random":
        ckpt = os.path.join(WORK, "checkpoints", f"{which}.pt")
        sd = torch.load(ckpt, map_location="cpu", weights_only=True)
        m.load_state_dict(sd)
    m.eval()

    tensors = []  # (name, array_bytes, dims, kind, scales)
    def add_int8(name, w):
        q, s = quantize_int8_per_row(w.detach().float())
        tensors.append((name, q.numpy().tobytes(), tuple(q.shape), 0, s.numpy()))
    def add_f32(name, w):
        a = w.detach().float().numpy()
        tensors.append((name, a.tobytes(), tuple(a.shape), 1, None))

    add_int8("tok_emb", m.tok.weight)
    for l, blk in enumerate(m.blocks):
        p = f"layers.{l}."
        add_int8(p + "attn_q", blk.q.weight)
        add_int8(p + "attn_k", blk.k.weight)
        add_int8(p + "attn_v", blk.v.weight)
        add_int8(p + "attn_proj", blk.proj.weight)
        add_int8(p + "mlp_gate", blk.gate.weight)
        add_int8(p + "mlp_up", blk.up.weight)
        add_int8(p + "mlp_down", blk.down.weight)
        add_f32(p + "rms1", blk.n1.w)
        add_f32(p + "rms2", blk.n2.w)
    add_f32("final_norm", m.norm.w)
    add_int8("head", m.head.weight)

    out_path = os.path.join(WORK, "sigllama-v1.bin")
    with open(out_path, "wb") as f:
        f.write(b"SGLL")
        f.write(struct.pack("<I", 1))
        f.write(struct.pack("<IIIII", V, cfg["d"], cfg["layers"], cfg["heads"], cfg["seq"]))
        f.write(struct.pack("<f", cfg["theta"]))
        f.write(struct.pack("<I", cfg["d"] * cfg["mlp_mult"]))
        f.write(struct.pack("<I", len(tensors)))
        for name, data, dims, kind, scales in tensors:
            nb = name.encode("ascii")
            f.write(struct.pack("<B", len(nb)))
            f.write(nb)
            f.write(struct.pack("<B", len(dims)))
            for d_ in dims:
                f.write(struct.pack("<I", d_))
            f.write(struct.pack("<B", kind))
            if scales is None:
                f.write(struct.pack("<I", 0))
            else:
                f.write(struct.pack("<I", len(scales)))
                f.write(scales.astype("<f4").tobytes())
            f.write(struct.pack("<I", len(data)))
            f.write(data)
    size = os.path.getsize(out_path)
    print(f"wrote {out_path}: {size/1024/1024:.2f} MB, {len(tensors)} tensors")
    # sanity: max reconstruction error of head
    q, s = quantize_int8_per_row(m.head.weight.float())
    err = ((q.float() * s[:, None] - m.head.weight.float()).abs().max()).item()
    print(f"head max abs quant err: {err:.5f}")

if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "best")
