#!/usr/bin/env python3
"""ONE-COMMAND HOOK: keep the Signature Llama archive page in step with the data.

Count-stamp chain for signature-llama (never one-run-behind):
  1. Rebuild the compact lazy-load index  (data/browse-index.json) -- done here
  2. Re-stamp browse.html count header + section counters -- done here
  3. Rebuild sitemap.xml (core + browse.html + every ?term= / ?toollib=) -- done here

Run from the repo root AFTER any data flush or edit that touches:
  - data/llm-dictionary.json (terms added/renamed/removed)
  - data/tool-libraries.json (libraries added/renamed/removed)
  - code/build_fixwave.py (dictionary/library rebuilds)

Run:  python3 code/stamp_browse.py

Counts are always read live from the data files, so the stamped numbers
can never lag one run behind the data.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def run_step(argv, label):
    r = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stderr.write("STEP FAILED: %s\n%s\n" % (label, r.stderr))
        sys.exit(r.returncode)


def main():
    # 1. compact index (reads the real data files)
    run_step([sys.executable, os.path.join("code", "build_browse_index.py")],
             "build_browse_index.py")

    idx = json.load(open(os.path.join(REPO, "data", "browse-index.json")))
    nterms, ntools = idx["term_count"], idx["tool_count"]

    # 2. re-stamp browse.html (fail loud if a marker is missing)
    page_path = os.path.join(REPO, "browse.html")
    page = open(page_path, encoding="utf-8").read()

    count_html = '%d AI terms \u00b7 %d tool libraries' % (nterms, ntools)
    for pattern, repl, label in [
        (r'<b id="browseCount">.*?</b>',
         '<b id="browseCount">%s</b>' % count_html, "browseCount"),
        (r'<span id="termn">\d+</span>',
         '<span id="termn">%d</span>' % nterms, "termn"),
        (r'<span id="tooln">\d+</span>',
         '<span id="tooln">%d</span>' % ntools, "tooln"),
    ]:
        new_page, n = re.subn(pattern, repl, page, count=1)
        if n != 1:
            sys.stderr.write("STEP FAILED: stamp marker missing: %s\n" % label)
            sys.exit(1)
        page = new_page
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(page)
    print("stamped browse.html: %s" % count_html)

    # 3. sitemap (picks up the counts + any new ?term= / ?toollib= URLs)
    run_step([sys.executable, os.path.join("code", "build_sitemap.py")],
             "build_sitemap.py")
    print("stamp_browse.py: done -- counts live at browse.html #browseCount")


if __name__ == "__main__":
    main()
