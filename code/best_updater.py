#!/usr/bin/env python3
"""Best-of-the-Best background reviewer for the Signature Llama showcase.

Usage:
  python3 code/best_updater.py --brief
      Prints a JSON review brief for the AI worker: the current best pick,
      plus everything new since it was built (new tool libraries, new patch
      bundles, manifest version bumps). The worker (an AI) reviews the brief
      and decides whether a better flagship exists.

  python3 code/best_updater.py --apply-new-best new_best.json --change "..."
      Installs a new best pick (written by the reviewing AI) and appends a
      changelog entry. Used only when the review concludes something better
      arrived.

The daily cron runs --brief; the worker updates the JSON files only when the
best actually changes, then commits and pushes. Silent otherwise.
"""
import json, os, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def load(p):
    with open(os.path.join(ROOT, p)) as f:
        return json.load(f)

def cmd_brief():
    best = load("data/best/best.json")
    libs = load("data/tool-libraries.json")
    manifest = load("llama-manifest.json")
    built = best.get("built", "")
    new_libs = []
    for l in libs.get("libraries", []):
        # a library counts as "new since best" if the index updated after the pick
        # and the library id is not already in the flagship's component list
        comp_ids = {c.get("id") for c in best.get("components", {}).get("tool_libraries", [])}
        if l.get("id") not in comp_ids:
            new_libs.append({"id": l["id"], "name": l["name"],
                             "category": l.get("category"), "version": l.get("version"),
                             "optimal": bool(l.get("optimal")), "desc": l.get("desc", "")[:160]})
    patches = sorted([f for f in os.listdir(os.path.join(ROOT, "patch"))
                      if f.endswith(".zip")])
    brief = {
        "generated": datetime.date.today().isoformat(),
        "current_best": {"id": best["id"], "title": best["title"],
                         "version": best.get("version"), "built": built,
                         "why": best.get("why", [])},
        "catalog_now": {
            "tool_libraries_total": len(libs.get("libraries", [])),
            "tool_libraries_index_updated": libs.get("updated"),
            "manifest_version": manifest.get("manifest_version"),
            "patch_bundles": patches,
        },
        "new_libraries_since_best": new_libs,
        "instruction": ("Review the new libraries/bundles above. If one or more of them "
                        "genuinely makes the flagship better (more capable, more universal, "
                        "better structured), write a new best.json via --apply-new-best. "
                        "If nothing better arrived, change nothing and stay silent."),
    }
    print(json.dumps(brief, indent=1))

def cmd_apply():
    # argv: --apply-new-best NEW_BEST_JSON --change "text"
    try:
        ni = sys.argv.index("--apply-new-best") + 1
        ci = sys.argv.index("--change") + 1
        new_best_path, change = sys.argv[ni], sys.argv[ci]
    except (ValueError, IndexError):
        sys.exit("usage: best_updater.py --apply-new-best NEW_BEST_JSON --change \"text\"")
    with open(new_best_path) as f:
        new_best = json.load(f)
    old = load("data/best/best.json")
    for k in ("id", "title", "tagline", "why", "components", "stats"):
        if k not in new_best:
            sys.exit("new best.json missing required key: " + k)
    new_best["built"] = datetime.date.today().isoformat()
    new_best["version"] = int(old.get("version", 0)) + 1
    with open(os.path.join(ROOT, "data/best/best.json"), "w") as f:
        json.dump(new_best, f, indent=1)
    clog = load("data/best/changelog.json")
    clog.append({"date": new_best["built"], "version": new_best["version"],
                 "change": change, "by": "JAH Best-Builder (background review)"})
    with open(os.path.join(ROOT, "data/best/changelog.json"), "w") as f:
        json.dump(clog, f, indent=1)
    print("BEST UPDATED: v%s (%s)" % (new_best["version"], new_best["title"]))

if __name__ == "__main__":
    if "--brief" in sys.argv:
        cmd_brief()
    elif "--apply-new-best" in sys.argv:
        cmd_apply()
    else:
        sys.exit("usage: best_updater.py --brief | --apply-new-best NEW_BEST_JSON --change \"text\"")
