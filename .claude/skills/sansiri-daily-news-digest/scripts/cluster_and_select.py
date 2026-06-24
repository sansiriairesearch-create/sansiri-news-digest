#!/usr/bin/env python3
"""C-03 Cluster & Select — group by theme, rank, pick 5 Sansiri + 5 competitor.

Pipeline step 3 (docs/Techspec.md §4). Reads iqnewsclip_parsed.json, clusters
near-duplicate headlines, ranks clusters by total PR Value + Top-Media bonus,
selects the top 5 Sansiri + top 5 competitor clusters (max 2 per competitor for
breadth, PRD BR-02), and pre-selects representative URLs ordered print -> online
-> social (PR Value desc, PRD BR-05). Writes digest_suggestion.json with empty
title/summary fields for the AI step (C-04) to fill.

Exit code: 0 ok.

Usage: cluster_and_select.py [--in iqnewsclip_parsed.json] [--out digest_suggestion.json]
"""
import argparse
import json
import os
import sys
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import TOP_MEDIA, normalize_text

SIM_THRESHOLD = 0.62
PREFIX_MATCH = 20      # shared leading chars -> same story (common for reposts)
JACCARD_THRESHOLD = 0.5
MAX_PER_COMPETITOR = 2
URLS_PER_TYPE = 3


def is_top_media(title: str) -> bool:
    t = (title or "").lower()
    return any(tm in t for tm in TOP_MEDIA)


def _shingles(s, k=3):
    return {s[i:i + k] for i in range(max(0, len(s) - k + 1))}


def same_story(a_norm, b_norm):
    """Headlines refer to the same story (robust to Thai/Eng word-wrap reposts)."""
    if not a_norm or not b_norm:
        return False
    if a_norm[:PREFIX_MATCH] and a_norm[:PREFIX_MATCH] == b_norm[:PREFIX_MATCH]:
        return True
    if SequenceMatcher(None, a_norm, b_norm).ratio() >= SIM_THRESHOLD:
        return True
    sa, sb = _shingles(a_norm), _shingles(b_norm)
    if sa and sb:
        j = len(sa & sb) / len(sa | sb)
        if j >= JACCARD_THRESHOLD:
            return True
    return False


def cluster_records(records, within_company=False):
    """Greedy single-link clustering on normalized headlines."""
    clusters = []  # each: {"norm": str, "company": str, "items": [...]}
    for r in records:
        norm = normalize_text(r["headline"])
        placed = False
        for c in clusters:
            if within_company and c["company"] != r["company"]:
                continue
            if same_story(norm, c["norm"]):
                c["items"].append(r)
                placed = True
                break
        if not placed:
            clusters.append({"norm": norm, "company": r["company"], "items": [r]})
    return clusters


def score(cluster):
    items = cluster["items"]
    pr = sum(i["pr_value"] for i in items)
    bonus = 50000 if any(is_top_media(i["media_title"]) for i in items) else 0
    breadth = 5000 * len({i["media_title"] for i in items})
    return pr + bonus + breadth


def pick_urls(items):
    buckets = {"prints": [], "online": [], "social": []}
    keymap = {"print": "prints", "online": "online", "social": "social"}
    for i in sorted(items, key=lambda x: x["pr_value"], reverse=True):
        b = keymap.get(i["media_type"])
        if not b:
            b = "online"
        buckets[b].append({
            "media_title": i["media_title"],
            "headline_url": i["url"],
            "pr_value": i["pr_value"],
            "media_type": i["media_type"],
        })
    return {k: v[:URLS_PER_TYPE] for k, v in buckets.items()}


def make_cluster_obj(cluster, prefix, idx):
    items = sorted(cluster["items"], key=lambda x: x["pr_value"], reverse=True)
    top = items[0]
    return {
        "cluster_id": f"{prefix}{idx}",
        "company": cluster["company"],
        "suggestion_title": top["headline"],
        "title": "",
        "summary": "",
        "total_pr_value": round(sum(i["pr_value"] for i in items), 2),
        "appearances": len(items),
        "urls": pick_urls(items),
    }


def select(records, prefix, n=5, cap_per_company=None):
    clusters = cluster_records(records, within_company=bool(cap_per_company))
    clusters.sort(key=score, reverse=True)
    chosen, per_company = [], {}
    for c in clusters:
        if cap_per_company:
            cnt = per_company.get(c["company"], 0)
            if cnt >= cap_per_company:
                continue
            per_company[c["company"]] = cnt + 1
        chosen.append(c)
        if len(chosen) >= n:
            break
    return [make_cluster_obj(c, prefix, i + 1) for i, c in enumerate(chosen)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="iqnewsclip_parsed.json")
    ap.add_argument("--out", default="digest_suggestion.json")
    ap.add_argument("--n", type=int, default=5)
    args = ap.parse_args()

    with open(args.inp, encoding="utf-8") as fh:
        data = json.load(fh)

    sansiri = select(data.get("sansiri", []), "s", n=args.n)
    competitor = select(data.get("competitor", []), "c", n=args.n,
                        cap_per_company=MAX_PER_COMPETITOR)

    out = {"sansiri": sansiri, "competitor": competitor}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"OK: selected {len(sansiri)} Sansiri + {len(competitor)} competitor "
          f"clusters -> {args.out}")
    for c in sansiri + competitor:
        print(f"  {c['cluster_id']:4} {c['company']:18} "
              f"PR={c['total_pr_value']:>12,.0f} x{c['appearances']:<3} "
              f"{c['suggestion_title'][:46]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
