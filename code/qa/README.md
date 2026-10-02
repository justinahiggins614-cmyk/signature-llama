# QA checkers — signature-llama

Re-runnable audits. Run any of them from this directory:

    python3 check_links.py [--live]   # nav order/destinations, anchors, repo files, [--live] HTTP HEADs
    python3 check_counts.py           # 312 terms / 120 libs / 28 KB entries / 2,983,488 params / hashes
    python3 check_dupe_ids.py         # duplicate tool ids, terms, element ids, inventory names
    python3 check_missing_ids.py      # required fields on libraries, terms, inventory, manifest

Each exits 0 on PASS, 1 with findings. `check_links.py --live` hits the network
(about 20 small HEAD requests); without the flag it only checks repo-local links.
