# Sansiri Daily News Digest (Claude Code)

Headless Claude Code system that turns the morning **iQNewsClip email** into a
curated **5 Sansiri + 5 competitor** Thai news digest and leaves it as a **Gmail
draft** for the PR team to review and send. Generation is fully automatic; sending
stays a one-tap human action.

## Layout
```
docs/                         design docs (interlinked)
  PRD.md · Techspec.md · uxui.md · features.json
.claude/skills/sansiri-daily-news-digest/
  SKILL.md                    workflow + rules (what Claude follows)
  scripts/                    deterministic pipeline (Python 3, stdlib only)
    common.py                 entities, aliases, helpers
    fetch_iqnewsclip.py       C-02 parse the 7-column email -> NewsItem[]
    cluster_and_select.py     C-03 cluster, rank, pick 5+5, choose URLs
    build_html_digest.py      C-05 render branded HTML (inline CSS, GraphikTH)
    pre_draft_check.py        C-06 12 deterministic checks (must exit 0)
    build_failure_report.py   C-09 failure-notice email
    smoke_test.py             health check on fixtures
    fixtures/                 sample_email.txt, sample_config.json
  references/                 company_keywords.md, top_media_list.md
```

## Run the pipeline manually
```bash
cd work   # scratch dir
S=../.claude/skills/sansiri-daily-news-digest/scripts
# 1. fetch iQNewsClip email via Gmail MCP (get_thread) -> a tool-results .txt
python3 $S/fetch_iqnewsclip.py --file <tool-results.txt> --out iqnewsclip_parsed.json
python3 $S/cluster_and_select.py --in iqnewsclip_parsed.json --out digest_suggestion.json
#   -> Claude fills title+summary + Quality Gate -> digest_config.json
python3 $S/build_html_digest.py --input digest_config.json \
        --date "24 มิถุนายน 2569" --date-en "June 24, 2026" --output digest_20260624.html
python3 $S/pre_draft_check.py digest_20260624.html   # must exit 0
#   -> Gmail MCP create_draft (never send)
```

## Health check
```bash
python3 .claude/skills/sansiri-daily-news-digest/scripts/smoke_test.py
```

## Status
See [docs/features.json](docs/features.json). The deterministic pipeline + skill
are built and verified end-to-end on the real 24 Jun 2026 email (341 records →
5+5 → all 12 checks pass → test draft created).

**Before production (blocker):** verify the Gmail MCP authenticates in a headless
**scheduled cloud agent** run (docs/Techspec.md R-01 / T-701), then register the
daily schedule (T-702). Idempotent same-day draft replacement (T-601) is still TODO.
