#!/usr/bin/env python3
"""Health check — run the deterministic pipeline on bundled fixtures.

Exercises C-02 (parse) -> C-03 (cluster/select) -> C-05 (build) -> C-06
(validate) without touching Gmail. Run before every production deploy
(docs/Techspec.md §10, features.json T-901).

Exit code: 0 all stages pass · 1 a stage failed.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")


def run(label, argv):
    print(f"\n=== {label} ===")
    env = dict(os.environ, PYTHONUTF8="1")
    p = subprocess.run([sys.executable] + argv, capture_output=True, text=True, env=env)
    print(p.stdout.strip())
    if p.returncode != 0:
        print(p.stderr.strip(), file=sys.stderr)
        print(f"FAIL: {label} exit={p.returncode}")
    return p.returncode


def main():
    tmp = tempfile.mkdtemp(prefix="sansiri_smoke_")
    parsed = os.path.join(tmp, "parsed.json")
    suggestion = os.path.join(tmp, "suggestion.json")
    html = os.path.join(tmp, "digest.html")

    steps = [
        ("C-02 parse", [os.path.join(HERE, "fetch_iqnewsclip.py"),
                        "--file", os.path.join(FIX, "sample_email.txt"),
                        "--out", parsed]),
        ("C-03 cluster/select", [os.path.join(HERE, "cluster_and_select.py"),
                                 "--in", parsed, "--out", suggestion, "--n", "2"]),
        ("C-05 build", [os.path.join(HERE, "build_html_digest.py"),
                        "--input", os.path.join(FIX, "sample_config.json"),
                        "--date", "24 มิถุนายน 2569", "--date-en", "June 24, 2026",
                        "--output", html]),
        ("C-06 validate", [os.path.join(HERE, "pre_draft_check.py"), html]),
    ]
    for label, argv in steps:
        if run(label, argv) != 0:
            return 1

    # sanity: parser actually produced records
    with open(parsed, encoding="utf-8") as fh:
        d = json.load(fh)
    assert d["counts"]["total"] >= 4, "expected >=4 parsed records"
    assert d["counts"]["sansiri"] >= 2 and d["counts"]["competitor"] >= 2

    print("\n✅ SMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
