#!/usr/bin/env python3
"""C-02 Parser — turn the iQNewsClip email into NewsItem records.

Pipeline step 2 (docs/Techspec.md §4). Reads the plaintext body of the
iQNewsClip email (from a Gmail-MCP tool-results JSON, a saved thread JSON, or a
raw text file), splits the word-wrapped 7-column table into NewsItem records,
de-duplicates across overlapping emails, filters by time window (Asia/Bangkok),
and writes iqnewsclip_parsed.json split into {sansiri, competitor}.

Exit codes (PRD FR-02..04): 0 ok · 1 no input · 2 parse error · 3 empty window.

Usage:
    fetch_iqnewsclip.py --file thread.json [thread2.json ...] \
        [--start "2026-06-23 00:00"] [--end "2026-06-24 08:00"] \
        [--out iqnewsclip_parsed.json]
    fetch_iqnewsclip.py --auto --tool-results-dir DIR        # newest *get_thread* file
"""
import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (ALL_COMPANY_STRINGS, MEDIA_TYPES, canon_company,
                    is_sansiri_group, normalize_text, parse_pr_value,
                    parse_reach)

DT_RE = re.compile(r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})")
URL_RE = re.compile(r"<([^>]+)>")
TAIL_RE = re.compile(
    r"\s*(?P<title>.+?)\s+(?P<type>online|social|print)\s+"
    r"(?P<pr>[\d,]+\.\d{2})(?:\s+(?P<reach>[\d,]+))?",
    re.IGNORECASE,
)


def load_plaintext(path: str) -> str:
    """Accept a tool-results/thread JSON ({messages:[{plaintextBody}]}) or raw text."""
    with open(path, encoding="utf-8") as fh:
        data = fh.read()
    try:
        obj = json.loads(data)
    except json.JSONDecodeError:
        return data  # already raw text
    bodies = []
    msgs = obj.get("messages", []) if isinstance(obj, dict) else []
    for m in msgs:
        body = m.get("plaintextBody") or m.get("plaintext_body") or ""
        if body:
            bodies.append(body)
    return "\n\n".join(bodies) if bodies else data


def company_before(flat: str, pos: int):
    """Return the canonical company whose name ends right before index `pos`."""
    head = flat[:pos].rstrip()
    for cand in ALL_COMPANY_STRINGS:
        if head.endswith(cand):
            return canon_company(cand)
    return None


def parse_records(flat: str):
    flat = re.sub(r"\s+", " ", flat)
    marks = list(DT_RE.finditer(flat))
    records = []
    for i, m in enumerate(marks):
        company = company_before(flat, m.start())
        if not company:
            continue  # a stray date inside a headline, not a real row
        end = marks[i + 1].start() if i + 1 < len(marks) else len(flat)
        seg = flat[m.end():end]
        url_m = URL_RE.search(seg)
        if not url_m:
            continue
        headline = seg[:url_m.start()].strip()
        url = url_m.group(1).strip()
        tail = seg[url_m.end():]
        tm = TAIL_RE.match(tail)
        if tm:
            media_title = tm.group("title").strip()
            media_type = tm.group("type").lower()
            pr_value = parse_pr_value(tm.group("pr"))
            reach = parse_reach(tm.group("reach"))
        else:
            media_title, media_type, pr_value, reach = "", "", 0.0, 0
        if not headline:
            continue
        records.append({
            "company": company,
            "date": f"{m.group(1)}T{m.group(2)}+07:00",
            "headline": headline,
            "media_title": media_title,
            "media_type": media_type,
            "pr_value": pr_value,
            "reach": reach,
            "url": url,
        })
    return records


def dedupe(records):
    seen, out = {}, []
    for r in records:
        key = (normalize_text(r["headline"]), r["url"])
        if key in seen:
            continue
        seen[key] = True
        out.append(r)
    return out


def in_window(rec, start, end):
    try:
        dt = datetime.strptime(rec["date"][:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return True
    if start and dt < start:
        return False
    if end and dt > end:
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", nargs="*", default=[])
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--tool-results-dir", default="")
    ap.add_argument("--start", default="")
    ap.add_argument("--end", default="")
    ap.add_argument("--out", default="iqnewsclip_parsed.json")
    args = ap.parse_args()

    files = list(args.file)
    if args.auto and args.tool_results_dir:
        cand = sorted(glob.glob(os.path.join(args.tool_results_dir, "*get_thread*.txt")),
                      key=os.path.getmtime, reverse=True)
        files = cand[:2]
    if not files:
        print("ERROR: no input files (use --file or --auto)", file=sys.stderr)
        return 1

    def pdt(s):
        return datetime.strptime(s, "%Y-%m-%d %H:%M") if s else None
    start, end = pdt(args.start), pdt(args.end)

    all_text = "\n\n".join(load_plaintext(f) for f in files if os.path.exists(f))
    if not all_text.strip():
        print("ERROR: empty input", file=sys.stderr)
        return 1

    records = parse_records(all_text)
    if not records:
        print("ERROR: parsed 0 records", file=sys.stderr)
        return 2

    records = dedupe(records)
    records = [r for r in records if in_window(r, start, end)]
    if not records:
        print("ERROR: 0 records in time window", file=sys.stderr)
        return 3

    sansiri = [r for r in records if is_sansiri_group(r["company"])]
    competitor = [r for r in records if not is_sansiri_group(r["company"])]
    out = {
        "generated_from": files,
        "window": {"start": args.start, "end": args.end},
        "counts": {"total": len(records), "sansiri": len(sansiri),
                   "competitor": len(competitor)},
        "sansiri": sansiri,
        "competitor": competitor,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"OK: {len(records)} records "
          f"(sansiri={len(sansiri)}, competitor={len(competitor)}) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
