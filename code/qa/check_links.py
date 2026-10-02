#!/usr/bin/env python3
"""Link audit for the signature-llama site.

Checks every link on the page:
  - #anchors -> must exist as an id= in index.html
  - relative file paths (data/*.json, sigllama/*, patch/*, industry-llama.js, llama-api.js)
    -> must exist in the repo
  - absolute URLs -> HTTP HEAD must return 200/30x (timeout 20s)

Exits 0 when everything resolves, 1 with a list of broken links otherwise.
Usage: python3 check_links.py [--live]   (--live enables absolute-URL checks)
"""
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX = os.path.join(ROOT, "index.html")

NAV_EXPECTED = [
    ("https://justinahiggins614-cmyk.github.io/jah-ai-models/", "Telephone Book"),
    ("https://justinahiggins614-cmyk.github.io/jah-calculator/", "Calculator"),
    ("https://justinahiggins614-cmyk.github.io/jah-dictionary/", "Dictionary"),
    ("https://justinahiggins614-cmyk.github.io/jah-wiki/", "JAH Wiki"),
    ("https://justinahiggins614-cmyk.github.io/jah-n-wiki-leaks/", "JAH-N Wiki"),
    ("https://justinahiggins614-cmyk.github.io/cyber-patent-catalog/", "Patent Catalog"),
    ("https://justinahiggins614-cmyk.github.io/signature-one-archive/specs.html", "Spec Catalog"),
    ("https://justinahiggins614-cmyk.github.io/signature-llama/", "Signature Llama"),
    ("https://justinahiggins614-cmyk.github.io/jah-computer-systems/", "PC Depository"),
]


def head_ok(url):
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "signature-llama-qa/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return 200 <= r.status < 400, r.status
    except Exception as e:  # noqa: BLE001 - we report whatever failed
        return False, "ERR %s" % e


def main():
    do_live = "--live" in sys.argv
    html = open(INDEX, encoding="utf-8").read()
    fails = []

    # 1. THE JAH NETWORK bar: exact canonical order + destinations
    m = re.search(r'<div class="jahnet">(.*?)</div>', html, re.S)
    if not m:
        fails.append("nav: THE JAH NETWORK bar not found")
    else:
        bar = m.group(1)
        got = re.findall(r'href="([^"]+)"', bar)
        got += ["(current)"] if '<span class="cur">' in bar else []
        expected = [u for u, _ in NAV_EXPECTED]
        # position 8 (index 7) is the "YOU ARE HERE" span, not a link
        expected_links = [u for u in expected if u != "https://justinahiggins614-cmyk.github.io/signature-llama/"]
        if got[:-1] != expected_links:
            fails.append("nav: order/destinations wrong.\n  got: %s\n  want: %s"
                         % (got[:-1], expected_links))
        if "YOU ARE HERE: SIGNATURE LLAMA" not in bar:
            fails.append("nav: YOU ARE HERE: SIGNATURE LLAMA marker missing")
        else:
            # marker must sit between position 7 (spec catalog) and position 9 (pc depository)
            parts = re.split(r'(<span class="cur">.*?</span>)', bar)
            before = parts[0]
            if not before.rstrip().endswith('signature-one-archive/specs.html">Signature Spec Catalog Pending Patents</a>'):
                fails.append("nav: YOU ARE HERE marker not at canonical position 8")

    # 2. #anchors resolve to an id= in the page
    ids = set(re.findall(r'id="([^"]+)"', html))
    for a in set(re.findall(r'href="#([A-Za-z0-9_-]+)"', html)):
        if a not in ids:
            fails.append("anchor: #%s has no matching id=" % a)

    # 3. relative data/script files exist
    for f in ["data/tool-libraries.json", "data/llm-dictionary.json", "data/explainer-kb.json",
              "model-status.json", "llama-manifest.json", "llms.txt",
              "sigllama/sigllama-v1.bin", "sigllama/sigllama.js", "sigllama/vocab.json",
              "industry-llama.js", "llama-api.js",
              "patch/signature-llama-patch-v1.zip"]:
        if not os.path.isfile(os.path.join(ROOT, f)):
            fails.append("file: %s missing from repo" % f)

    # 4. page JS fetches point at real relative files
    for f in set(re.findall(r"fetch\('([^']+)'\)", html)):
        if f.startswith(("http", "data:")):
            continue
        if not os.path.isfile(os.path.join(ROOT, f)):
            fails.append("fetch: %s missing from repo" % f)

    # 5. absolute URLs reachable (only with --live)
    if do_live:
        absurls = sorted(set(re.findall(r'href="(https://[^"]+)"', html))
                         | set(re.findall(r"src=\"(https://[^\"]+)\"", html))
                         | {"https://console.groq.com/keys",
                            "https://justinahiggins614-cmyk.github.io/signature-backend/sigllama/sigllama-v1.bin",
                            "https://justinahiggins614-cmyk.github.io/signature-backend/sigllama/sigllama.js",
                            "https://justinahiggins614-cmyk.github.io/signature-backend/sigllama/vocab.json"})
        for u in absurls:
            ok, code = head_ok(u)
            if not ok:
                fails.append("url: %s -> %s" % (u, code))
            else:
                print("  ok  %s" % u)

    if fails:
        print("LINK AUDIT: %d failure(s)" % len(fails))
        for f in fails:
            print("  FAIL", f)
        return 1
    print("LINK AUDIT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
