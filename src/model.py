#!/usr/bin/env python3
"""Signature Llama v1 - decoder-only Transformer, written from scratch.
Llama-style: RMSNorm, RoPE, SwiGLU, no biases, tied or untied head.
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class RMSNorm(nn.Module):
    def __init__(self, d, eps=1e-5):
        super().__init__()
        self.eps = eps
        self.w = nn.Parameter(torch.ones(d))

    def forward(self, x):
        return self.w * x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)


def build_rope_cache(seq_len, head_dim, theta=10000.0, device="cpu", dtype=torch.float32):
    # returns cos, sin shaped (seq_len, head_dim)
    inv = 1.0 / (theta ** (torch.arange(0, head_dim, 2, device=device, dtype=dtype) / head_dim))
    t = torch.arange(seq_len, device=device, dtype=dtype)
    freqs = torch.outer(t, inv)
    emb = torch.cat([freqs, freqs], dim=-1)
    return emb.cos(), emb.sin()


def apply_rope(x, cos, sin):
    # x: (B, T, H, D)
    d = x.shape[-1]
    x1, x2 = x[..., : d // 2], x[..., d // 2:]
    rot = torch.cat([-x2, x1], dim=-1)
    cos = cos[:, None, :]
    sin = sin[:, None, :]
    return x * cos + rot * sin


class Block(nn.Module):
    def __init__(self, d, n_heads, mlp_mult=4):
        super().__init__()
        assert d % n_heads == 0
        self.n_heads = n_heads
        self.hd = d // n_heads
        self.n1 = RMSNorm(d)
        self.n2 = RMSNorm(d)
        self.q = nn.Linear(d, d, bias=False)
        self.k = nn.Linear(d, d, bias=False)
        self.v = nn.Linear(d, d, bias=False)
        self.proj = nn.Linear(d, d, bias=False)
        self.gate = nn.Linear(d, mlp_mult * d, bias=False)
        self.up = nn.Linear(d, mlp_mult * d, bias=False)
        self.down = nn.Linear(mlp_mult * d, d, bias=False)

    def forward(self, x, cos, sin, mask=None):
        B, T, D = x.shape
        h = self.n1(x)
        q = self.q(h).view(B, T, self.n_heads, self.hd)
        k = self.k(h).view(B, T, self.n_heads, self.hd)
        v = self.v(h).view(B, T, self.n_heads, self.hd)
        q, k = apply_rope(q, cos[:T], sin[:T]), apply_rope(k, cos[:T], sin[:T])
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)
        att = (q @ k.transpose(-2, -1)) / math.sqrt(self.hd)
        if mask is not None:
            att = att + mask
        att = F.softmax(att, dim=-1)
        y = (att @ v).transpose(1, 2).contiguous().view(B, T, D)
        x = x + self.proj(y)
        h = self.n2(x)
        x = x + self.down(F.silu(self.gate(h)) * self.up(h))
        return x


class SigLlama(nn.Module):
    def __init__(self, vocab, d=160, layers=4, heads=6, seq=96, theta=10000.0, mlp_mult=4):
        super().__init__()
        self.cfg = dict(vocab=vocab, d=d, layers=layers, heads=heads,
                        seq=seq, theta=theta, mlp_mult=mlp_mult)
        self.tok = nn.Embedding(vocab, d)
        self.blocks = nn.ModuleList([Block(d, heads, mlp_mult) for _ in range(layers)])
        self.norm = RMSNorm(d)
        self.head = nn.Linear(d, vocab, bias=False)
        self.register_buffer("causal_mask", torch.triu(
            torch.full((seq, seq), float("-inf")), diagonal=1), persistent=False)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        cos, sin = build_rope_cache(self.cfg["seq"], self.cfg["d"] // self.cfg["heads"],
                                    self.cfg["theta"], idx.device, torch.float32)
        x = self.tok(idx)
        mask = self.causal_mask[:T, :T]
        for blk in self.blocks:
            x = blk(x, cos, sin, mask)
        logits = self.head(self.norm(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, self.cfg["vocab"]),
                                   targets.view(-1), ignore_index=-100)
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new, temperature=1.0, top_k=0):
        # idx: (1, T) LongTensor; greedy if temperature<=0
        self.eval()
        for _ in range(max_new):
            x = idx[:, -self.cfg["seq"]:]
            logits, _ = self.forward(x)
            lg = logits[0, -1]
            if temperature <= 0:
                nxt = int(torch.argmax(lg))
            else:
                lg = lg / temperature
                if top_k > 0:
                    v, _ = torch.topk(lg, top_k)
                    lg[lg < v[-1]] = float("-inf")
                p = F.softmax(lg, dim=-1)
                nxt = int(torch.multinomial(p, 1))
            idx = torch.cat([idx, torch.tensor([[nxt]])], dim=1)
        return idx


def count_params(m):
    return sum(p.numel() for p in m.parameters())
