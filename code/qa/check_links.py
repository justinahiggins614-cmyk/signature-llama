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
    ("https://justinahiggins614-cmyk.github.io/jah-ai-models/", "The Signature AI Phone Book"),
    ("https://justinahiggins614-cmyk.github.io/jah-calculator/", "Calculator"),
    ("https://justinahiggins614-cmyk.github.io/jah-dictionary/", "Dictionary"),
    ("https://justinahiggins614-cmyk.github.io/jah-wiki/", "JAH Wiki"),
    ("https://justinahiggins614-cmyk.github.io/jah-n-wiki-leaks/", "JAH-N Wiki"),
    ("https://justinahiggins614-cmyk.github.io/cyber-patent-catalog/", "Patent Catalog"),
    ("https://justinahiggins614-cmyk.github.io/signature-one-archive/specs.html", "Spec Catalog"),
    ("https://justinahiggins614-cmyk.github.io/signature-llama/", "Signature Llama"),
    ("https://justinahiggins614-cmyk.github.io/jah-computer-systems/", "PC Depository"),
    ("https://justinahiggins614-cmyk.github.io/signature-cyber-mega-mall/", "Cyber Mega-Mall"),
    ("https://justinahiggins614-cmyk.github.io/signature-university/", "Signature University"),
    ("https://justinahiggins614-cmyk.github.io/signature-books/", "Book Depository"),
    ("https://justinahiggins614-cmyk.github.io/signature-comics/", "Comic Store"),
    ("https://justinahiggins614-cmyk.github.io/signature-newspapers/", "Global Newspaper Archive"),
    ("https://justinahiggins614-cmyk.github.io/signature-3d-print/", "3D Print Mega Mall"),
    ("https://justinahiggins614-cmyk.github.io/signature-backend/", "Signature Backend"),
    ("https://justinahiggins614-cmyk.github.io/signature-boundless-generators/", "Boundless Generator Archive"),
    ("https://justinahiggins614-cmyk.github.io/signature-ai-mixlab/", "AI Mix Lab"),
    ("https://justinahiggins614-cmyk.github.io/signature-ai-olypics/", "AI Olympics"),
    ("https://justinahiggins614-cmyk.github.io/signature-chip-maker/", "Chip Maker and Archive"),
    ("https://justinahiggins614-cmyk.github.io/signature-app-archive/", "App Archive"),
    ("https://justinahiggins614-cmyk.github.io/signature-ai-robot-matcher/", "AI Robot Matcher"),
    ("https://justinahiggins614-cmyk.github.io/signature-experiment-solver/", "Experiment Solver"),
    ("https://justinahiggins614-cmyk.github.io/signature-ai-image-video-maker/", "Signature AI Pixel"),
    ("https://justinahiggins614-cmyk.github.io/signature-ai-video-maker/", "Video Maker AI"),
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

    # 1. THE JAH NETWORK bar: exact canonical order + destinations + labels.
    # The bar carries all 25 canonical links; self is an <a class="cur"> link
    # followed by a <span class="cur">YOU ARE HERE...</span> marker at position 8.
    m = re.search(r'<div class="jahnet">(.*?)</div>', html, re.S)
    if not m:
        fails.append("nav: THE JAH NETWORK bar not found")
    else:
        bar = m.group(1)
        got = re.findall(r'<a [^>]*href="([^"]+)"[^>]*>([^<]+)</a>', bar)
        if got != NAV_EXPECTED:
            fails.append("nav: order/destinations/labels wrong.\n  got: %s\n  want: %s"
                         % (got, NAV_EXPECTED))
        # self link carries class="cur" at canonical position 8
        SELF = "https://justinahiggins614-cmyk.github.io/signature-llama/"
        if '<a class="cur" href="%s">Signature Llama</a>' % SELF not in bar:
            fails.append('nav: self link missing class="cur"')
        if "YOU ARE HERE: SIGNATURE LLAMA" not in bar:
            fails.append("nav: YOU ARE HERE: SIGNATURE LLAMA marker missing")
        else:
            # marker must sit between position 7 (spec catalog) and position 9 (pc depository)
            parts = re.split(r'(<span class="cur">.*?</span>)', bar)
            before = parts[0]
            if not (before.rstrip().endswith('">Signature Llama</a>')
                    and 'signature-one-archive/specs.html">Spec Catalog</a><a class="cur"' in before):
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
