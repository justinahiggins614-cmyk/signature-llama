#!/usr/bin/env python3
"""File compiled-Llama phone-book entries into the AI phone book.

The Signature Llama Compiler (compiler.html) records every compile behind the
scenes: it queues the two phone-book entries (the Signature version + the
improved "best" version) in the browser's localStorage and embeds them in the
downloaded manifest. A browser cannot push to GitHub, so this helper performs
the final step: appending real user compiles to jah-ai-models/ai-catalog.json.

Usage:
  python3 code/file_compiles.py entries.json [--dry-run]

  entries.json: a JSON array of phone-book entry objects, as produced by the
    compiler (copy them with the "Copy entry" buttons on compiler.html, or
    pull them from a downloaded manifest's phonebook_filed block).

Flow: git pull --ff-only in ~/workspace/jah-ai-models -> validate every entry
against the catalog schema (exact top-level keys + RUNTIME/DEMO/VOICE/ARTIFACTS
sub-keys, no ID or SIGNATURE_NUMBER collisions) -> append -> commit ONLY
ai-catalog.json -> push.

--dry-run: validate only, change nothing.
"""
import json
import os
import subprocess
import sys

CATALOG_CLONE = os.path.expanduser("~/workspace/jah-ai-models")
CATALOG_FILE = os.path.join(CATALOG_CLONE, "ai-catalog.json")
SUBKEYS = ("RUNTIME", "DEMO", "VOICE", "ARTIFACTS")


def run(*args, cwd=CATALOG_CLONE):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("FAILED: %s\n%s" % (" ".join(args), r.stderr.strip()))
    return r.stdout.strip()


def load_catalog():
    with open(CATALOG_FILE, encoding="utf-8") as f:
        cat = json.load(f)
    return cat, (cat["records"] if isinstance(cat, dict) and "records" in cat else cat)


def validate(entries, records):
    if not isinstance(entries, list) or not entries:
        raise SystemExit("entries.json must be a non-empty JSON array")
    keyset = set()
    sub = {sk: set() for sk in SUBKEYS}
    for r in records:
        keyset.update(r.keys())
        for sk in SUBKEYS:
            if isinstance(r.get(sk), dict):
                sub[sk].update(r[sk].keys())
    seen_ids = {r.get("ID") for r in records}
    seen_phones = {r.get("SIGNATURE_NUMBER") for r in records}
    for e in entries:
        missing = [k for k in keyset if k not in e]
        extra = [k for k in e.keys() if k not in keyset]
        if missing or extra:
            raise SystemExit("Key mismatch in %s: missing=%s extra=%s"
                             % (e.get("ID"), missing, extra))
        for sk in SUBKEYS:
            ek = set((e.get(sk) or {}).keys())
            mk = [k for k in sub[sk] if k not in ek]
            xk = [k for k in ek if k not in sub[sk]]
            if mk or xk:
                raise SystemExit("Sub-key mismatch in %s.%s: missing=%s extra=%s"
                                 % (e.get("ID"), sk, mk, xk))
        if e.get("ID") in seen_ids:
            raise SystemExit("ID collision: %s already in catalog" % e.get("ID"))
        if e.get("SIGNATURE_NUMBER") in seen_phones:
            raise SystemExit("Phone collision: %s already in catalog"
                             % e.get("SIGNATURE_NUMBER"))
        if not str(e.get("ID", "")).startswith("JAH-AI-CMP-"):
            raise SystemExit("Refusing non-compile entry: %s (this helper files "
                             "only JAH-AI-CMP-* compiler entries)" % e.get("ID"))
        seen_ids.add(e.get("ID"))
        seen_phones.add(e.get("SIGNATURE_NUMBER"))
    print("Validated %d entries: schema exact, no ID/phone collisions." % len(entries))


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 1
    dry = "--dry-run" in sys.argv[1:]
    with open(sys.argv[1], encoding="utf-8") as f:
        entries = json.load(f)

    print("Pulling jah-ai-models (ff-only)...")
    print(run("git", "pull", "--ff-only"))
    cat, records = load_catalog()
    print("Catalog records: %d" % len(records))
    validate(entries, records)
    if dry:
        print("DRY RUN: catalog untouched.")
        return 0

    records.extend(entries)
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(cat, f, ensure_ascii=False, indent=1)
        f.write("\n")
    run("git", "add", "ai-catalog.json")
    names = ", ".join(e.get("ID", "?") for e in entries)
    run("git", "commit", "-m",
        "File compiled-Llama phone-book entries: %s" % names)
    print(run("git", "push"))
    sha = run("git", "rev-parse", "--short", "HEAD")
    print("Committed + pushed %d entries (%s) at %s" % (len(entries), names, sha))
    return 0


if __name__ == "__main__":
    sys.exit(main())
