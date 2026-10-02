#!/usr/bin/env python3
"""Duplicate-ID checker for the signature-llama site.

Finds exact duplicate identifiers:
  - tool library `id` values in data/tool-libraries.json
  - dictionary term names (case-insensitive) in data/llm-dictionary.json
  - id="..." attributes in index.html
  - INVENTORY entry names in index.html

Exits 0 on pass, 1 with findings otherwise.
Usage: python3 check_dupe_ids.py
"""
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def dupes(seq):
    return [k for k, n in Counter(seq).items() if n > 1]


def main():
    fails = []

    t = json.load(open(os.path.join(ROOT, "data/tool-libraries.json"), encoding="utf-8"))
    d = dupes([l["id"] for l in t["libraries"]])
    if d:
        fails.append("tool library duplicate ids: %s" % d)
    print("  tool library ids: %d unique" % len(set(l["id"] for l in t["libraries"])))

    dd = json.load(open(os.path.join(ROOT, "data/llm-dictionary.json"), encoding="utf-8"))
    d = dupes([e["t"].strip().lower() for e in dd["terms"]])
    if d:
        fails.append("dictionary duplicate terms: %s" % d)
    print("  dictionary terms: %d unique" % len(set(e["t"].strip().lower() for e in dd["terms"])))

    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    d = dupes(re.findall(r'id="([^"]+)"', html))
    if d:
        fails.append("index.html duplicate element ids: %s" % d)
    print("  page element ids: %d unique" % len(set(re.findall(r'id="([^"]+)"', html))))

    d = dupes(re.findall(r"\{ name: '([^']+)', cat:", html))
    if d:
        fails.append("inventory duplicate names: %s" % d)
    print("  inventory names: %d unique" % len(set(re.findall(r"\{ name: '([^']+)', cat:", html))))

    if fails:
        print("DUPE-ID AUDIT: %d failure(s)" % len(fails))
        for f in fails:
            print("  FAIL", f)
        return 1
    print("DUPE-ID AUDIT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
