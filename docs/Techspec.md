# Tech Spec — Sansiri Daily News Digest (Claude Code)

> **Technical Specification** — การออกแบบเชิงเทคนิคที่รองรับ [PRD.md](./PRD.md)

| | |
|---|---|
| **Status** | Draft |
| **Version** | 0.1.0 |
| **Last updated** | 2026-06-24 |
| **Platform** | Claude Code (scheduled cloud agent / routine), headless |
| **Language** | Python 3 (สคริปต์ deterministic) + Claude (สรุป/QG) |

### Related documents
- **Requirements:** [PRD.md](./PRD.md)
- **Email UX / visual spec:** [uxui.md](./uxui.md)
- **Task tracker:** [features.json](./features.json)
- **Decisions & regression log:** [DECISIONS.md](./DECISIONS.md)

### Component → Requirement map
| Component | ทำหน้าที่ | รองรับ FR/NFR |
|---|---|---|
| **C-01** Gmail Ingest | ดึงอีเมล iQNewsClip | FR-01, NFR-01 |
| **C-02** Parser | แตกตาราง 7 คอลัมน์ + dedupe + กรองเวลา | FR-02, FR-03, FR-04, NFR-02 |
| **C-03** Cluster/Select | จัดกลุ่ม/จัดอันดับ/เลือก 5+5 + URLs | FR-05, FR-06, FR-07, FR-08 |
| **C-04** AI Summarize + QG | เขียนพาดหัว+สรุป + Content Quality Gate | FR-09, FR-10, BR-01..06 |
| **C-05** HTML Builder | เรนเดอร์อีเมล HTML แบรนด์ | FR-11, NFR-05 |
| **C-06** Validator | ตรวจ 14 ข้อก่อนสร้าง draft | FR-12, NFR-07 |
| **C-07** Draft Creator | สร้าง Gmail Draft (ไม่ส่ง) | FR-13, FR-16, NFR-03 |
| **C-08** Scheduler / Cloud Agent | รันอัตโนมัติทุกเช้าแบบ headless | FR-14, NFR-01 |
| **C-09** Failure Reporter | แจ้งเตือนเมื่อ pipeline ล้ม | FR-15, NFR-08 |

---

## 1. Architecture Overview

```
                    ┌──────────────────────────────────────────────┐
                    │  C-08 Scheduler / Cloud Agent (cron ~08:00)   │
                    │  Claude Code routine, headless, Asia/Bangkok  │
                    └───────────────────────┬──────────────────────┘
                                            │ invokes skill
                                            ▼
        ┌───────────────────────────────────────────────────────────────┐
        │           skill: sansiri-daily-news-digest                     │
        │                                                                │
        │  C-01 ──► C-02 ──► C-03 ──► C-04 ──► C-05 ──► C-06 ──► C-07     │
        │ Gmail   Parser  Cluster  AI sum   HTML    Valid.   Draft       │
        │ Ingest          /Select  + QG     Build   14 chk   create      │
        │   │       │        │       │        │       │        │         │
        │   ▼       ▼        ▼       ▼        ▼       ▼        ▼         │
        │ tool-   parsed  suggest  config   digest  exit0?  Gmail        │
        │ results .json   .json    .json    .html            Draft       │
        │                                                                │
        │            (any step fails) ──────────► C-09 Failure Reporter  │
        └───────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
                          Gmail Drafts  ──►  ทีม PR ตรวจ + กดส่งเอง
```

ทุกขั้นเขียน artifact ลงไฟล์กลางใน workspace เพื่อ determinism + audit (NFR-07)

---

## 2. Runtime & Scheduling (C-08)

- **กลไก:** Claude Code **scheduled cloud agent / routine** (สร้างผ่าน `/schedule`) — รันบน cloud ของ Anthropic ตาม
  cron โดยไม่ต้องเปิดเครื่อง (FR-14, NFR-01)
- **ตารางเวลา:** `0 8 * * *` (ทุกวัน 08:00 **Asia/Bangkok**) — ปรับได้; เผื่อ grace window เผื่ออีเมล iQNewsClip มาช้า
- **โหมด:** headless, non-interactive; ไม่มี Chrome MCP / browser
- **MCP ที่จำเป็น (ต้อง authenticate ใน cloud runtime):** Gmail MCP
  - `mcp__..._Gmail__search_threads`
  - `mcp__..._Gmail__get_thread`
  - `mcp__..._Gmail__create_draft`
- ⚠️ **ข้อควรระวัง (R-01):** MCP ที่ผูกกับ claude.ai อาจไม่พร้อมในการรันแบบ headless/cron — ต้องยืนยันว่า Gmail MCP
  ใช้งานได้ในการรันแบบ scheduled ก่อน go-live (ดู §11)

---

## 3. Skill Layout

ติดตั้งเป็น Claude Code skill ภายใต้โปรเจกต์ `NewsSummary` (อ้างอิงโครงจาก bundle เดิม
`/Users/muknantiya/Downloads/PRNewsDigest` แต่ตัดส่วน browser/NCX ออก):

```
NewsSummary/
├── docs/                       ← PRD.md · Techspec.md · uxui.md · features.json
└── .claude/
    └── skills/
        └── sansiri-daily-news-digest/
            ├── SKILL.md                 ← frontmatter (name, description) + ขั้นตอน + กติกา
            ├── scripts/
            │   ├── fetch_iqnewsclip.py        (C-02)
            │   ├── cluster_and_select.py      (C-03)
            │   ├── build_html_digest.py       (C-05)
            │   ├── pre_draft_check.py         (C-06)
            │   ├── build_failure_report.py    (C-09)
            │   ├── smoke_test.py              (CI/health)
            │   ├── diagnose.py                (debug)
            │   └── fixtures/
            │       ├── sample_parsed.json
            │       └── sample_config.json
            └── references/
                ├── project_instructions.md   ← กติกา editorial (อิง BR-01..07)
                ├── company_keywords.md       ← คีย์เวิร์ด/ผู้บริหาร 7 หมวด
                └── top_media_list.md          ← Top Media ranked
```

> สคริปต์ Python นำสัญญา input/output/exit-code จากเวอร์ชัน Cowork ที่พิสูจน์แล้วมาใช้ซ้ำ (ดู §5)

---

## 4. Pipeline ↔ Scripts (รายขั้น)

| ขั้น | Component | สคริปต์/ตัวกระทำ | Input | Output | Exit codes |
|---|---|---|---|---|---|
| 1 | C-01 | Gmail MCP (`search_threads` + `get_thread`) | query หัวข้อ/ผู้ส่ง | ไฟล์ tool-results (auto-save ถ้า > ~25k tokens) | — |
| 2 | C-02 | `fetch_iqnewsclip.py` | tool-results files / thread IDs + ช่วงเวลา | `iqnewsclip_parsed.json` | 0 ok · 1 ไม่พบ input · 2 parse error · 3 ไม่มีข่าวในช่วงเวลา |
| 3 | C-03 | `cluster_and_select.py` | `iqnewsclip_parsed.json` | `digest_suggestion.json` (10 cluster, title/summary ว่าง) | 0 ok |
| 4 | C-04 | **Claude** (อ่าน suggestion, เขียน title+summary, ใช้ QG) | `digest_suggestion.json` | `digest_config.json` | — |
| 5 | C-05 | `build_html_digest.py` | `digest_config.json` + วันที่ TH/EN | `digest_<YYYYMMDD>.html` | 0 ok · ≠0 ถ้า config ไม่ครบ |
| 6 | C-06 | `pre_draft_check.py` | `digest_<YYYYMMDD>.html` | รายงานผลตรวจ | **0 = ผ่าน (บังคับ)** · 1 = ไม่ผ่าน |
| 7 | C-07 | Gmail MCP (`create_draft`) | HTML + recipients + subject | Gmail Draft | — |
| ✗ | C-09 | `build_failure_report.py` | ข้อความ error/stage | อีเมลแจ้งล้มเหลว (draft/แจ้งเตือน) | 0 ok |

**คำสั่งตัวอย่าง (อ้างอิงสัญญาเดิม):**
```bash
python3 fetch_iqnewsclip.py --auto --start "2026-06-23 12:00" --end "2026-06-24 08:00"
python3 cluster_and_select.py            # อ่าน iqnewsclip_parsed.json
python3 build_html_digest.py --input digest_config.json \
        --date "24 มิถุนายน 2569" --date-en "June 24, 2026" \
        --output digest_20260624.html
python3 pre_draft_check.py digest_20260624.html && echo OK
```

---

## 5. Data Model

### `NewsItem` (เรคคอร์ดข่าวมาตรฐาน)
```jsonc
{
  "company": "Sansiri",                 // ชื่อบริษัท (กลุ่มแสนสิริ / คู่แข่ง)
  "date": "2026-06-24T06:45:00+07:00",  // เวลาเผยแพร่ (Asia/Bangkok)
  "headline": "…",                       // พาดหัวจากคอลัมน์ HeadLine
  "media_title": "กรุงเทพธุรกิจ",         // ชื่อสื่อ/เพจ
  "media_type": "print",                 // print | online | social
  "pr_value": 150000,                     // มูลค่าข่าว (บาท)
  "reach": 500000,                        // Potential Reach
  "url": "https://re.dataxet.co/api/…"   // ลิงก์ต้นทาง (print = PDF ของ Dataxet)
}
```

### Artifacts กลาง
| ไฟล์ | สร้างโดย | เนื้อหา |
|---|---|---|
| `iqnewsclip_parsed.json` | C-02 | เรคคอร์ด `NewsItem[]` แยก `sansiri` / `competitor` (dedupe + กรองเวลาแล้ว) |
| `digest_suggestion.json` | C-03 | 10 cluster (5+5) แต่ละ cluster มี `urls.{prints,online,social}` + `suggestion_title`; `summary` ว่าง |
| `digest_config.json` | C-04 (Claude) | เหมือน suggestion แต่เติม `title` + `summary` ครบ + ผ่าน QG แล้ว |
| `digest_<YYYYMMDD>.html` | C-05 | อีเมล HTML สำเร็จรูปพร้อมตรวจ |

### `digest_suggestion.json` (รูปแบบย่อ)
```jsonc
{
  "sansiri": [
    { "cluster_id": "s1_via34", "suggestion_title": "…", "summary": "",
      "urls": { "prints": [{"media_title":"กรุงเทพธุรกิจ","headline_url":"…","pr_value":150000}],
                "online": [{"media_title":"propholic.com","headline_url":"…","pr_value":45000}],
                "social": [] } }
    // … s2..s5
  ],
  "competitor": [ /* c1..c5 */ ]
}
```

### การจัดการ response ใหญ่
Gmail MCP จะ auto-save response ที่ใหญ่เกิน ~25k tokens เป็นไฟล์ `tool-results/…txt` — C-02 อ่านจากไฟล์เหล่านี้
(`--auto` หา latest ให้ หรือระบุ `--file` / `--thread-id`) เพื่อไม่ให้ context ล้น

---

## 6. Configuration & Secrets

| หมวด | รายละเอียด | ที่เก็บ |
|---|---|---|
| Recipients | 7 ผู้รับ (ดู [PRD.md §3](./PRD.md)) | config ไฟล์/ตัวแปร |
| Entities | กลุ่มแสนสิริ + 15 คู่แข่ง (ดู [PRD.md BR-07](./PRD.md)) | `references/company_keywords.md` |
| Keywords / Top Media | คีย์เวิร์ด 7 หมวด + Top Media ranked | `references/*.md` |
| Time window | เมื่อวาน 07:00 → วันนี้ 06:00 (จาก daily_meta.py) | config |
| Brand tokens | navy/gold/link-blue, GraphikTH | ใช้ใน C-05 (ดู [uxui.md](./uxui.md)) |
| Secrets | **ห้ามฝังในโค้ด/สกิล** — ใช้ env / Script properties เท่านั้น (NFR-04) | runtime env |

> โหมด email-only ไม่ต้องใช้ credential ของ NCX/Chrome อีกต่อไป (ลดความเสี่ยงด้านความปลอดภัย)

---

## 7. Validation — 14 Checks (C-06)

`pre_draft_check.py` ต้อง **exit 0** ก่อนเรียก `create_draft` มิฉะนั้น Claude ต้องแก้ `digest_config.json` → rebuild → re-validate

| # | Check | เงื่อนไขที่ถือว่า "ไม่ผ่าน" | บังคับใช้กฎ UX |
|---|---|---|---|
| C1 | Broken URL | พบ `https://https:/` หรือ `http://https:/` | UX-03 |
| C2 | Prohibited labels | พบ "(print)", "[PDF]", "(FB)", "(IG)", "(TikTok)", "อ่านเพิ่มเติม" | UX-03 / BR-05 |
| C3 | AI banner present | ไม่มีแถบทอง `#D4A843` "Generated by AI" | UX-01 |
| C4 | Main banner present | ไม่มีแถบ navy `#1B3A5C` "Sansiri News" | UX-01 |
| C5 | Section headers | ขาดหัวข้อ "ข่าวกลุ่มบริษัทแสนสิริ" หรือ "ข่าวคู่แข่งและอสังหาทั่วไป" | UX-01 |
| C6 | Footer exact | footer ≠ "ฝ่ายสื่อสารองค์กร / บริษัท แสนสิริ จำกัด (มหาชน)" | UX-01 |
| C7 | Headline anchors unstyled | `<a>` พาดหัวมี `text-decoration:underline` (ต้องเป็น none) | UX-03 |
| C8 | Each cluster has links | มีข่าวที่ไม่มีลิงก์แหล่งข่าว | UX-03 |
| C9 | News count | ไม่ใช่ 5+5 ตามโครง S1–S5 + C1–C5 (ยอมน้อยกว่าได้ถ้า QG ตัด — ดูหมายเหตุ) | UX-05 |
| C10 | Direct article links | ลิงก์ online/social ยังติด proxy `re.dataxet.co/api/` (ต้องถอดออก); print PDF (`iqnewsclip.com/reportdl/printdl`) คง proxy ไว้ได้ — ดู BR-08 | UX-03 |
| C11 | No style block | พบ `<style>…</style>` | UX-06 / NFR-05 |
| C12 | No Noto Sans Thai | font-family มี "Noto Sans Thai" | UX-06 / NFR-05 |
| C13 | Banner bgcolor present | ขาด `bgcolor="#D4A843"` หรือ `bgcolor="#1B3A5C"` (กัน banner หาย/ตัวอักษรขาวมองไม่เห็น) | UX-02 / BR (regression) |
| C14 | No baked google.com/url | source มี `google.com/url` ฝังมาเอง (ต้องไม่มี — Gmail เติมเองตอนแสดง) | BR-08 (regression) |

> หมายเหตุ C9: ค่ามาตรฐานคือ 10 ข่าว แต่ตาม BR-03 ถ้า QG ตัดจนเหลือน้อยกว่า ให้ถือว่าผ่านได้ พร้อมบันทึกเหตุผล
> (กฎจำนวนปรับเป็น warning ได้ตามนโยบายทีม)

---

## 8. Error Handling & Idempotency

- **Failure report (C-09):** ทุกความล้มเหลว (ไม่พบอีเมล / parse error / validate ไม่ผ่านหลัง retry) → `build_failure_report.py`
  สร้างอีเมลแจ้งสถานะ เพื่อไม่ให้ "เงียบหาย" (FR-15, SM-03)
- **Idempotency (FR-16, NFR-03):** ใช้ `daily_meta.py` หา `search_subject` ของวันนั้น แล้วเรียก
  `list_drafts` + `search_threads in:sent` ก่อนสร้าง — **ถ้ามี draft/อีเมลของวันนั้นแล้วให้หยุด ไม่สร้างซ้ำ**
  (MCP `create_draft` ไม่มีคำสั่งลบ/แก้ draft จึงทำได้แค่ "กันสร้างซ้ำ" ไม่ใช่ "แทนที่"). รันซ้ำได้ปลอดภัย
- **Retry/grace:** ถ้าอีเมล iQNewsClip ยังมาไม่ถึงตอนรัน ให้รอ/ลองใหม่ในกรอบเวลาที่กำหนดก่อนแจ้งล้มเหลว (R-03)

---

## 9. MCP Integration

| การใช้งาน | เครื่องมือ | ขั้น |
|---|---|---|
| ค้นอีเมล iQNewsClip | `Gmail.search_threads` (`subject:"Sansiri News" from:iqnewsclip@iqnewsclip.com newer_than:2d`) | C-01 |
| ดึงเนื้ออีเมลเต็ม | `Gmail.get_thread` (FULL_CONTENT; response ใหญ่ → tool-results file) | C-01 |
| สร้างฉบับร่าง | `Gmail.create_draft` (recipients + subject + html body) | C-07 |
| (เสริม, ไม่ใช่ core) | `WebFetch` ดึงบทความ online สาธารณะเพื่อ enrich สรุป | C-04 |

**ถอดออกจากเวอร์ชัน Cowork:** Chrome MCP (navigate/read_page/javascript) และการล็อกอิน NCX Dataxet — ไม่ใช้ในโหมด headless/email-only

---

## 10. Deployment & Setup

1. **Scaffold** โปรเจกต์ `NewsSummary` + โครงสกิลตาม §3
2. **เขียนสคริปต์** C-02/C-03/C-05/C-06/C-09 + fixtures (พอร์ตจาก bundle เดิม, ตัด browser)
3. **เขียน `SKILL.md`** ฝังขั้นตอน 7 ขั้น + กติกา editorial (BR-01..07) + 14 checks
4. **เชื่อม Gmail MCP** ใน cloud runtime และ **ยืนยันว่าใช้ได้ในการรันแบบ scheduled** (R-01)
5. **ลงทะเบียน schedule** ผ่าน `/schedule` (cron 08:00 Asia/Bangkok)
6. **รัน `smoke_test.py`** บน fixtures ให้ผ่าน
7. **Dry-run** end-to-end หนึ่งวัน → ตรวจ draft ที่ได้กับ [uxui.md](./uxui.md) และอีเมลจริงที่เคยส่ง

---

## 11. Decisions & Risks

| ID | หัวข้อ | สรุป |
|---|---|---|
| D-1 | email-only | ใช้ iQNewsClip email เป็นแหล่งเดียว ตัด NCX/Chrome (รองรับ headless) |
| D-2 | draft-only | สร้าง draft ไม่ส่งเอง (Rule 35) คนกดส่ง |
| D-3 | greenfield | สร้างใหม่บน Claude Code แยกจาก GAS |
| **R-01** | **Gmail MCP ใน headless/cron** | ต้องยืนยัน auth ใช้งานได้จริงในการรันแบบ scheduled ก่อน go-live — **บล็อกเกอร์หลัก** |
| R-02 | ความลึกสรุป | ไม่มีบทความ print เต็ม → พิจารณา WebFetch online เป็น enrichment |
| R-05 | ความต่างจาก Cowork | ผลลัพธ์อาจต่างจากเวอร์ชันที่อ่านบทความเต็มได้เล็กน้อย (สรุปจากพาดหัว/บริบทในอีเมล) |
| **R-06** | **MCP `create_draft` แนบไฟล์ไม่ได้** | tool ระบุ "attachments not supported yet" และทดสอบแล้วได้ `Internal error`. การแนบไฟล์ standalone HTML (BR-09) ต้องทำผ่าน **Gmail API / GAS โดยตรง** ในขั้น production (ระบบ GAS เดิมแนบไฟล์ได้อยู่แล้ว) — `build_standalone.py` เตรียมไฟล์ไว้ให้พร้อมแนบ |
| **R-07** | **Scheduled cloud agent ต้องมี GitHub repo** | routine บน cloud จะ **clone โค้ดจาก GitHub** (เข้าถึงไฟล์ในเครื่องไม่ได้). ตอนนี้โปรเจกต์เป็น local-only (ไม่มี git remote, ไม่มี `gh`). ต้อง **push โค้ดขึ้น GitHub repo (แนะนำ private)** ก่อน แล้วชี้ routine มาที่ repo นั้น. ข่าวดี: Gmail connector มีให้แนบกับ routine ได้ (ลดความเสี่ยง R-01) — cron 08:30 Asia/Bangkok = **`30 1 * * *` UTC** |

---

## 12. Traceability Table (C ↔ FR ↔ T)

| Component | PRD requirements | features.json tasks |
|---|---|---|
| C-01 Gmail Ingest | FR-01, NFR-01 | T-101 |
| C-02 Parser | FR-02, FR-03, FR-04 | T-102 |
| C-03 Cluster/Select | FR-05, FR-06, FR-07, FR-08 | T-201, T-202 |
| C-04 AI Summarize + QG | FR-09, FR-10, BR-01..06 | T-301, T-302 |
| C-05 HTML Builder | FR-11, NFR-05 | T-401 |
| C-06 Validator | FR-12, NFR-07 | T-501 |
| C-07 Draft Creator | FR-13, FR-16, NFR-03 | T-601 |
| C-08 Scheduler/Cloud Agent | FR-14, NFR-01 | T-701, T-702 |
| C-09 Failure Reporter | FR-15, NFR-08 | T-801 |

> ตารางนี้สอดคล้องกับฟิลด์ `techspecRefs` / `prdRefs` ใน [features.json](./features.json)
