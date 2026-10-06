#!/usr/bin/env python3
"""Train Signature Llama v1 on the corpus. Streaming windows, AdamW, cosine schedule.
Checkpoints to workdir; keeps best by val loss; wall-clock cap.
"""
import json, math, os, random, time
import torch
import torch.nn.functional as F

WORK = os.path.expanduser("~/workspace/sigllama")
torch.set_num_threads(2)

CFG = dict(d=192, layers=5, heads=8, seq=128, theta=10000.0, mlp_mult=4,
           batch=20, lr=4e-4, warmup=500, target_tokens=33_000_000,
           time_cap_s=4.5 * 3600, ckpt_every=1000)

def main():
    from tokenizer import load as vload
    from model import SigLlama, count_params
    vocab = vload(); V = len(vocab["itos"])
    bos, eos = vocab["bos_id"], vocab["eos_id"]

    print("tokenizing corpus...", flush=True)
    data = bytearray()
    with open(os.path.join(WORK, "corpus.txt"), encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            for ch in line:
                data.append(vocab["stoi"].get(ch, vocab["unk_id"]))
            data.append(eos)
    data = bytes(data)
    n = len(data)
    print(f"corpus tokens: {n}", flush=True)
    n_val = 200_000
    train_data, val_data = data[: n - n_val], data[n - n_val:]

    m = SigLlama(V, d=CFG["d"], layers=CFG["layers"], heads=CFG["heads"],
                 seq=CFG["seq"], theta=CFG["theta"], mlp_mult=CFG["mlp_mult"])
    print("params:", count_params(m), flush=True)
    m.train()
    opt = torch.optim.AdamW(m.parameters(), lr=CFG["lr"], betas=(0.9, 0.95),
                            weight_decay=0.1)

    total_steps = CFG["target_tokens"] // (CFG["batch"] * CFG["seq"])
    print(f"target steps: {total_steps}", flush=True)

    def lr_at(step):
        if step < CFG["warmup"]:
            return CFG["lr"] * step / CFG["warmup"]
        p = (step - CFG["warmup"]) / max(1, total_steps - CFG["warmup"])
        return CFG["lr"] * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1.0, p))))

    def batch(split):
        d = train_data if split == "train" else val_data
        B, T = CFG["batch"], CFG["seq"]
        x = torch.empty(B, T, dtype=torch.long)
        y = torch.empty(B, T, dtype=torch.long)
        for b in range(B):
            i = random.randrange(0, len(d) - T - 1)
            w = d[i: i + T + 1]
            x[b] = torch.tensor(list(w[:-1]), dtype=torch.long)
            y[b] = torch.tensor(list(w[1:]), dtype=torch.long)
        return x, y

    @torch.no_grad()
    def val_loss():
        m.eval(); tot, cnt = 0.0, 0
        for _ in range(20):
            x, y = batch("val")
            _, loss = m(x, y)
            tot += loss.item(); cnt += 1
        m.train()
        return tot / cnt

    t0 = time.time()
    best = float("inf")
    step = 0
    ckpt_dir = os.path.join(WORK, "checkpoints")
    os.makedirs(ckpt_dir, exist_ok=True)

    # resume if a checkpoint exists
    latest = os.path.join(ckpt_dir, "latest.pt")
    if os.path.exists(latest):
        sd = torch.load(latest, map_location="cpu", weights_only=False)
        m.load_state_dict(sd["model"]); opt.load_state_dict(sd["opt"])
        step, best = sd["step"], sd["best"]
        print(f"resumed at step {step}, best {best:.3f}", flush=True)

    while step < total_steps:
        if time.time() - t0 > CFG["time_cap_s"]:
            print("time cap reached", flush=True); break
        for g in opt.param_groups:
            g["lr"] = lr_at(step)
        x, y = batch("train")
        opt.zero_grad()
        _, loss = m(x, y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opt.step()
        step += 1
        if step % 200 == 0:
            el = time.time() - t0
            print(f"step {step}/{total_steps} loss {loss.item():.3f} "
                  f"lr {lr_at(step):.1e} elapsed {el/60:.0f}m", flush=True)
        if step % CFG["ckpt_every"] == 0:
            vl = val_loss()
            tag = "BEST" if vl < best else ""
            if vl < best:
                best = vl
                torch.save(m.state_dict(), os.path.join(ckpt_dir, "best.pt"))
            torch.save({"model": m.state_dict(), "opt": opt.state_dict(),
                        "step": step, "best": best, "cfg": CFG}, latest)
            print(f"[ckpt {step}] val {vl:.3f} best {best:.3f} {tag}", flush=True)
            # sample
            with torch.no_grad():
                m.eval()
                idx = torch.tensor([[bos]])
                out = m.generate(idx, 120, temperature=0.8, top_k=40)
                from tokenizer import decode
                print("SAMPLE:", decode(out[0].tolist(), vocab)[:200].replace("\n", " "), flush=True)
                m.train()

    torch.save(m.state_dict(), os.path.join(ckpt_dir, "final.pt"))
    meta = {"cfg": CFG, "steps": step, "best_val": best, "params": count_params(m),
            "vocab": V, "elapsed_s": time.time() - t0}
    with open(os.path.join(WORK, "train_meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("DONE", json.dumps(meta), flush=True)

if __name__ == "__main__":
    main()
