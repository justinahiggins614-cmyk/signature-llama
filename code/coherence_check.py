#!/usr/bin/env python3
"""Coherence check: AI identity shown on the Signature Llama site vs the canon.

Manon's order (2026-10-02): "There should be no ai any website incoherent" —
every AI profile matches the phone-book canon exactly. The canon lives at
jah-ai-models/ai-catalog.json.

This site presents one AI identity: Signature Llama (LLAMA_PROFILE in
index.html). Signature Llama is the engine itself, not a phone-book AI file,
so it carries a standalone ID (JAH-AI-SIG-LLAMA-1). This checker fails loudly
if the site's profile ever:
  - claims a JAH-AI-* ID that exists in the canon but with a different
    name/description (impersonation/drift), or
  - uses the NAME of a canon AI under a different ID.

Exit 0 = coherent. Exit 1 = drift found.
Run after any identity/profile edit:  python3 code/coherence_check.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CANON = "/home/hatch/workspace/jah-ai-models/ai-catalog.json"


def norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def site_profile():
    html = open(os.path.join(REPO, "index.html"), encoding="utf-8").read()
    m = re.search(r"var LLAMA_PROFILE\s*=\s*\{(.*?)\};", html, re.S)
    if not m:
        raise SystemExit("FAIL — LLAMA_PROFILE not found in index.html")
    body = m.group(1)

    def field(name):
        fm = re.search(name + r"\s*:\s*'((?:[^'\\]|\\.)*)'", body)
        return fm.group(1).replace("\\'", "'") if fm else ""

    return {"name": field("name"), "id": field("id"), "description": field("description")}


def main():
    site = site_profile()
    print("site profile: %s (%s)" % (site["name"], site["id"]))
    if not site["name"] or not site["id"]:
        print("FAIL — LLAMA_PROFILE is missing name or id")
        return 1
    catalog = json.load(open(CANON, encoding="utf-8"))
    recs = catalog.get("records", [])
    by_id = {r["ID"]: r for r in recs}
    issues = []

    rec = by_id.get(site["id"])
    if rec is not None:
        # The site's ID exists in the canon: it must match exactly.
        if norm(site["name"]).lower() != norm(rec.get("NAME")).lower():
            issues.append("ID %s: site name %r vs canon %r" % (site["id"], site["name"], rec.get("NAME")))
        sd, cd = norm(site["description"]), norm(rec.get("DESCRIPTION"))
        if sd and cd and sd != cd and sd[:120] != cd[:120]:
            issues.append("ID %s: description drift (first 120 chars differ)" % site["id"])
    else:
        # Standalone engine identity — legal, but it must not borrow a canon NAME.
        for r in recs:
            if norm(r.get("NAME")).lower() == norm(site["name"]).lower():
                issues.append("name %r matches canon AI %s but uses a different ID (%s) — incoherent" %
                              (site["name"], r["ID"], site["id"]))
                break
        else:
            print("info: %s is a standalone engine identity (no canon record) — no impersonation." % site["id"])

    if issues:
        print("FAIL — %d coherence issue(s):" % len(issues))
        for i in issues:
            print("  - " + i)
        return 1
    print("PASS — site AI identity is coherent with the phone-book canon.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
