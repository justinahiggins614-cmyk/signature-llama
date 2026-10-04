#!/usr/bin/env python3
"""Build the compact lazy-load index for browse.html.

Reads the REAL data files and writes data/browse-index.json carrying only
what the archive page needs: names, categories, and deep-link targets.
Never carries definitions or tool code, so the archive page lazy-loads a
few KB instead of the full megabyte-scale data files.

Run from the repo root:  python3 code/build_browse_index.py
Stamp order (never one-run-behind): rebuild this file AFTER any data
flush (dictionary / tool-library edits), then re-stamp browse.html and
rebuild the sitemap -- see code/stamp_browse.py for the one-command hook.
"""
import json
import os
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

dd = json.load(open(os.path.join(REPO, "data", "llm-dictionary.json")))
terms = dd["terms"]
td = json.load(open(os.path.join(REPO, "data", "tool-libraries.json")))
libs = td["libraries"]

out = {
    "updated": date.today().isoformat(),
    "term_count": len(terms),
    "tool_count": len(libs),
    # deep links mirror the live site convention: ?term=<term title>,
    # ?toollib=<library id> (index.html matches on the exact term title)
    "terms": [{"t": t.get("t", ""), "c": t.get("c", "")} for t in terms],
    "tools": [{"id": l.get("id", ""), "name": l.get("name", ""),
               "cat": l.get("category", "")} for l in libs],
}

dest = os.path.join(REPO, "data", "browse-index.json")
tmp = dest + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(out, f, separators=(",", ":"), ensure_ascii=False)
os.replace(tmp, dest)
print("wrote data/browse-index.json: %d terms, %d tools"
      % (len(terms), len(libs)))
