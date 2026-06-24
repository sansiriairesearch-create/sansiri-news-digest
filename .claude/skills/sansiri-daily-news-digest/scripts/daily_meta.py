#!/usr/bin/env python3
"""Canonical date / subject helper — one source of truth for the daily run.

Produces the Thai (พ.ศ.) and English (AD) date strings, the exact email subject,
and the Gmail search term used by the idempotency pre-check (PRD FR-16). Using
this everywhere prevents date-format drift and makes the "one draft per day"
guard reliable. Time is computed in Asia/Bangkok.

Usage:
    daily_meta.py                 # today (Asia/Bangkok)
    daily_meta.py --iso 2026-06-24
Outputs JSON: {iso, date_th, date_en, subject, search_subject}
"""
import argparse
import json
import sys
from datetime import datetime, timezone, timedelta

BKK = timezone(timedelta(hours=7))
TH_MONTHS = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม",
             "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม",
             "พฤศจิกายน", "ธันวาคม"]
EN_MONTHS = ["", "January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]

SUBJECT_TMPL = ("ข่าวเกี่ยวกับกลุ่มบริษัทแสนสิริ ข่าวคู่แข่งและอสังหาทั่วไป "
                " วันที่  {d}  {th_month}  {be}   มีรายละเอียดที่น่าสนใจดังนี้")


def meta(dt):
    date_th = f"{dt.day} {TH_MONTHS[dt.month]} {dt.year + 543}"
    date_en = f"{EN_MONTHS[dt.month]} {dt.day}, {dt.year}"
    subject = SUBJECT_TMPL.format(d=dt.day, th_month=TH_MONTHS[dt.month],
                                  be=dt.year + 543)
    # Day-unique fragment for Gmail draft/thread search (idempotency, FR-16).
    search_subject = f"วันที่ {dt.day} {TH_MONTHS[dt.month]} {dt.year + 543}"
    return {
        "iso": dt.strftime("%Y-%m-%d"),
        "date_th": date_th,
        "date_en": date_en,
        "subject": subject,
        "search_subject": search_subject,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", default="")
    args = ap.parse_args()
    if args.iso:
        dt = datetime.strptime(args.iso, "%Y-%m-%d")
    else:
        dt = datetime.now(BKK)
    print(json.dumps(meta(dt), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
