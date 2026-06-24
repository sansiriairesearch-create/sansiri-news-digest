# PRD — Sansiri Daily News Digest (Claude Code)

> **Product Requirements Document**
> ระบบสรุปข่าว PR อสังหาริมทรัพย์ประจำวันของแสนสิริ ที่รันอัตโนมัติบน Claude Code

| | |
|---|---|
| **Owner** | PR Team, Sansiri (Nantiya "Muk") |
| **Product account** | `sansiriairesearch@gmail.com` (display: *GenAI-Center Sansiri*) |
| **Status** | Draft |
| **Version** | 0.1.0 |
| **Last updated** | 2026-06-24 |
| **Predecessor** | Claude Cowork skill `sansiri-daily-news-digest` (`/Users/muknantiya/Downloads/PRNewsDigest`) |

### Related documents
- **Technical design:** [Techspec.md](./Techspec.md)
- **Email UX / visual spec:** [uxui.md](./uxui.md)
- **Task tracker:** [features.json](./features.json)
- **Decisions & regression log:** [DECISIONS.md](./DECISIONS.md)

---

## 1. Context & Background

ทุกเช้า inbox ของ `sansiriairesearch@gmail.com` จะได้รับอีเมล **iQNewsClip** (จาก `iqnewsclip@iqnewsclip.com`,
หัวข้อ `Sansiri News (DD MON YY / HH:MM)`) ที่รวบรวมข่าวดิบในรูป **ตาราง 7 คอลัมน์**:

`Company · Date · HeadLine · Media Title · Media Type · PR Value · Potential Reach`

ปัจจุบันพนักงานทีม PR ต้องนำข่าวดิบเหล่านี้มา **คัดเลือกและสรุปด้วยมือ** ให้เหลือ "ข่าวเด่นประจำวัน" จำนวน 10 เรื่อง
(แสนสิริ 5 + คู่แข่ง 5) พร้อมเขียนพาดหัวและสรุปเนื้อหา แล้วจัดเป็นอีเมล HTML แบรนด์แสนสิริ งานนี้เดิมทำผ่าน
**Claude Cowork** (skill `sansiri-daily-news-digest`) ซึ่งยังต้องมีคนเปิดเครื่อง/สั่งงาน

**เป้าหมายของโปรเจกต์นี้** คือย้ายงานสรุปข่าวมาทำบน **Claude Code** ให้ **สร้างฉบับร่างได้อัตโนมัติ 100% แบบ headless
โดยไม่ต้องเปิดคอมพิวเตอร์** — ระบบจะรันเองตามเวลาทุกเช้าบน cloud, อ่านอีเมล iQNewsClip, สร้าง **Gmail Draft** ที่ผ่านการ
ตรวจสอบแล้ว รอให้ทีม PR เปิด Gmail (บนมือถือก็ได้) ตรวจและกดส่งเอง

> **สรุปหลักการ:** "100% automatic" หมายถึง *การสร้างฉบับร่าง* เป็นอัตโนมัติเต็มรูปแบบ ส่วน *การกดส่ง* ยังเป็นงานของคน
> (human-in-the-loop) — ตรงตาม Rule 35 ของ skill เดิม

### ความสัมพันธ์กับระบบเดิม
- ระบบ **`SansiriNewsDaily`** (Google Apps Script) ที่ผลิต *อีเมลตารางรายบริษัทรายวัน* (`source: portal`) และ
  *รายงาน Weekly AMEC* ยังคงทำงานต่อไป — **อยู่นอกขอบเขต** ของเอกสารชุดนี้
- โปรเจกต์นี้เป็น **greenfield บน Claude Code** ไม่แชร์โค้ดกับ GAS (อ้างอิงได้เพื่อความสอดคล้องของแบรนด์/รายชื่อคู่แข่ง)

---

## 2. Goals & Non-Goals

### Goals
- G1 — ผลิต **Daily Digest** (แสนสิริ 5 + คู่แข่ง 5 พร้อมสรุป AI) เป็น Gmail Draft อัตโนมัติทุกเช้า
- G2 — ทำงาน **headless บน cloud** ไม่ต้องเปิดคอม ไม่ต้องมีคนสั่ง
- G3 — รักษา **คุณภาพ/รูปแบบ/แบรนด์** ให้เทียบเท่าหรือดีกว่างานที่ทำด้วยมือ
- G4 — มี **Content Quality Gate** กรองข่าวไม่เหมาะสม/ไม่เกี่ยวข้อง/prompt injection ออก
- G5 — กระบวนการ **deterministic + auditable** (ใช้สคริปต์/ไฟล์กลางที่ตรวจสอบย้อนหลังได้)

### Non-Goals
- N1 — **ไม่** ส่งอีเมลอัตโนมัติ (draft-only; คนกดส่ง)
- N2 — **ไม่** ทำอีเมลตารางรายบริษัทรายวัน และ **ไม่** ทำรายงาน Weekly AMEC (เป็นของระบบ GAS เดิม)
- N3 — **ไม่** ล็อกอิน NCX Dataxet / ใช้ Chrome MCP / browser automation
- N4 — **ไม่** อ่านเนื้อหาข่าว print ฉบับเต็ม (ไม่มี browser ใน headless run)

---

## 3. Stakeholders & Recipients

| บทบาท | ผู้เกี่ยวข้อง |
|---|---|
| Product owner / reviewer | Nantiya "Muk" (PR Team) |
| ผู้รับอีเมล (To) | `satchapong@sansiri.com`, `Nantiya.Sai@sansiri.com`, `Samatcha@sansiri.com`, `Metisa@sansiri.com`, `PRTeam@sansiri.com`, `Patcharawan@plus.co.th`, `Ploynapas.Ve@plus.co.th` |
| ผู้กดส่ง (human-in-the-loop) | สมาชิกทีม PR คนใดก็ได้ที่เปิด draft แล้วตรวจ/ส่ง |
| Sender identity | `sansiriairesearch@gmail.com` |

> รายชื่อผู้รับเป็นค่า config (ดู [Techspec.md §7](./Techspec.md)) ปรับได้โดยไม่แก้โค้ด

---

## 4. User Stories

- **US1** — *ในฐานะทีม PR* ฉันอยากเปิด Gmail ตอนเช้าแล้วเจอ draft ข่าวเด่นที่จัดรูปแบบเรียบร้อยรออยู่ เพื่อจะได้ตรวจและกดส่งได้เลย โดยไม่ต้องเปิดคอมมานั่งสรุปเอง
- **US2** — *ในฐานะผู้บริหาร* ฉันอยากได้สรุปข่าวที่ "อ่านแล้วเข้าใจประเด็น" ไม่ใช่แค่ลิงก์ดิบ
- **US3** — *ในฐานะทีม PR* ฉันอยากมั่นใจว่าข่าวที่ไม่เกี่ยวข้อง/เสี่ยงต่อแบรนด์/ข้อมูลผิด จะถูกคัดออกก่อนถึงผู้รับ
- **US4** — *ในฐานะผู้ดูแลระบบ* ฉันอยากได้อีเมลแจ้งเตือนเมื่อ pipeline ล้มเหลว แทนที่จะเงียบหายไปเฉย ๆ
- **US5** — *ในฐานะทีม PR* ฉันอยากแก้ไขถ้อยคำใน draft ได้ก่อนส่ง (ระบบไม่ส่งเองเด็ดขาด)

---

## 5. Functional Requirements

ทุกข้อถูกอ้างอิงด้วย `FR-NN` และผูกกับ component ใน [Techspec.md](./Techspec.md) และงานใน [features.json](./features.json)

| ID | Requirement | หมายเหตุ |
|---|---|---|
| **FR-01** | ค้นหาและดึงอีเมล iQNewsClip ล่าสุด (วันนี้ + เมื่อวาน) ผ่าน Gmail MCP | รองรับ response ใหญ่ที่ถูก auto-save เป็นไฟล์ tool-results |
| **FR-02** | แยกตาราง 7 คอลัมน์เป็นเรคคอร์ดข่าว (`NewsItem`) | รองรับทั้ง HTML table และ plaintext body |
| **FR-03** | ตัดข่าวซ้ำข้ามอีเมลที่คาบเกี่ยวกัน (dedupe) | นับข่าวเดียวกันที่ถูกบันทึกหลายครั้งเป็นชิ้นเดียว |
| **FR-04** | กรองตามช่วงเวลา: D-1 12:00 → เวลาที่รัน (Asia/Bangkok) | |
| **FR-05** | จัดกลุ่มข่าวตามธีม (cluster) แยกกลุ่มแสนสิริ / คู่แข่ง | |
| **FR-06** | จัดอันดับ cluster ด้วย PR Value รวม + โบนัส Top Media | |
| **FR-07** | เลือกข่าวเด่น **แสนสิริ 5 + คู่แข่ง 5** | จำนวนเป้าหมาย 10; อาจน้อยกว่าได้ถ้า QG ตัดออก |
| **FR-08** | ภายในแต่ละ cluster เลือก URL ตัวแทน เรียง print → online → social (PR Value มาก→น้อย) | |
| **FR-09** | **Content Quality Gate** ตรวจทุกข่าวก่อนรวมเข้า digest | ดู [BR-03](#7-editorial--business-rules) |
| **FR-10** | ให้ Claude เขียน **พาดหัว (1–2 บรรทัด) + สรุป 2–4 ย่อหน้า** ภาษาไทยทางการต่อข่าว | บันทึกลง `digest_config.json` |
| **FR-11** | สร้างอีเมล **HTML แบรนด์แสนสิริ** จาก `digest_config.json` | inline CSS, GraphikTH; ดู [uxui.md](./uxui.md) |
| **FR-12** | ตรวจ HTML ด้วยชุดตรวจ **14 ข้อ (deterministic)** ต้องผ่าน (exit 0) ก่อนสร้าง draft | ดู [Techspec.md §8](./Techspec.md) |
| **FR-13** | สร้าง **Gmail Draft** (ไม่ส่ง) พร้อมผู้รับ + subject + HTML body | ผ่าน `gmail_create_draft` |
| **FR-14** | รันอัตโนมัติทุกวันตามตารางเวลา (scheduled cloud agent) แบบ headless | cron ~08:00 Asia/Bangkok |
| **FR-15** | ถ้า pipeline ล้มเหลว → สร้าง **อีเมลแจ้งความล้มเหลว** (failure report) | กันงานเงียบหาย |
| **FR-16** | กระบวนการ **idempotent**: ไม่สร้าง draft ซ้ำซ้อนในวันเดียวกัน | **ตรวจก่อนสร้าง** — ใช้ `daily_meta.py` หา `search_subject` แล้ว `list_drafts`/`search_threads` หา draft/อีเมลของวันนั้น ถ้ามีแล้วให้หยุด (MCP ลบ/แก้ draft ไม่ได้ จึงกัน "ไม่สร้างซ้ำ" แทนการแทนที่) |

---

## 6. Pipeline (ภาพรวม 7 ขั้น)

```
1. Collect    → Gmail MCP ดึงอีเมล iQNewsClip (วันนี้ + เมื่อวาน)         [FR-01]
2. Parse      → fetch_iqnewsclip.py แตกตาราง 7 คอลัมน์ + dedupe + กรองเวลา  [FR-02..04]
3. Cluster    → cluster_and_select.py จัดกลุ่ม/จัดอันดับ/เลือก 5+5 + URLs   [FR-05..08]
4. Summarize  → Claude เขียนพาดหัว+สรุป + Content Quality Gate              [FR-09, FR-10]
5. Build      → build_html_digest.py เรนเดอร์ HTML แบรนด์                   [FR-11]
6. Validate   → pre_draft_check.py ตรวจ 14 ข้อ (ต้อง exit 0)               [FR-12]
7. Draft      → Gmail MCP สร้าง Draft (ไม่ส่ง)                              [FR-13]
```
รายละเอียดสคริปต์/อินพุต/เอาต์พุต ดู [Techspec.md §5](./Techspec.md)

---

## 7. Editorial / Business Rules

| ID | Rule |
|---|---|
| **BR-01 — ลำดับความสำคัญข่าวแสนสิริ** | (1) วิกฤต/ข่าวลบ → (2) กลยุทธ์ธุรกิจ/ร่วมทุน → (3) แบรนด์/ลักชัวรี/เรือธง → (4) หุ้น/การเงิน → (5) ชุมชน/ไลฟ์สไตล์ → (6) เปิดตัวโครงการ/แคมเปญ. **ข้อยกเว้น:** ถ้าเป็น "Highlight of the Day" (บล็อกเกอร์รายงาน 7+ ราย + PR Value สูง) ให้เลื่อนขึ้นอันดับ 1 |
| **BR-02 — ลำดับความสำคัญข่าวคู่แข่ง** | (1) การเคลื่อนไหวเชิงกลยุทธ์ → (2) ข่าวการเงินที่กระทบตลาด → (3) ข่าวที่พาดพิงแสนสิริโดยตรง → (4) เทรนด์ตลาด → (5) ข่าวอสังหาทั่วไป (fallback ถ้าคู่แข่ง < 5) |
| **BR-03 — Content Quality Gate (เกณฑ์ตัดออก)** | ตัดข่าวที่: (1) **Prompt injection** (เช่น "ignore instructions", "send email to") (2) **ข่าวปลอม/ข้อมูลขัดแย้งชัดเจน** (3) **ไม่เกี่ยวข้อง** กับอสังหา/แสนสิริ/คู่แข่ง/ตลาด (4) **ไม่เหมาะกับการสื่อสารองค์กร** (การเมืองรุนแรง/ทำเสื่อมเสีย) (5) **URL ปลายทางไม่ตรงพาดหัว** — แม้มาจาก Top Media ก็ต้องตัด และยอมให้ข่าวน้อยกว่า 10 ได้ |
| **BR-04 — สไตล์การเขียนสรุป** | ภาษาไทยทางการ; ใส่ตัวเลขจริง (เป้าขาย/มูลค่า/ดอกเบี้ย) + ชื่อ-ตำแหน่งผู้บริหาร (อ่านจากต้นฉบับ ห้ามเดา); ไม่มีความเห็นส่วนตัว/สแลง/อิโมจิ |
| **BR-05 — การจัดลิงก์แหล่งข่าว** | เรียง print → online → social, ภายในแต่ละชนิดเรียงตาม PR Value มาก→น้อย; ไม่ใส่ป้าย "(print)"/"[PDF]"/"(FB)"; print link แสดงชื่อสื่อเฉย ๆ |
| **BR-08 — ลิงก์ต้องชี้ตรงหน้าข่าวจริง** | ลิงก์ **online/social** ต้องถอด prefix proxy ของ Dataxet (`https://re.dataxet.co/api/`) ออก และซ่อม `https:/` → `https://` ให้ชี้ตรงหน้าข่าวต้นทาง (กัน Gmail Redirect Notice เด้งไป URL ของ Dataxet). ลิงก์ **print** (ไฟล์ PDF ข่าวตัดที่ `iqnewsclip.com/reportdl/printdl`) **คง proxy ไว้** เพราะเปิดได้ผ่าน Dataxet เท่านั้น |
| **BR-09 — แนบไฟล์ HTML ของ digest** | นอกจากเนื้ออีเมล HTML แล้ว ให้ **แนบไฟล์ `Sansiri-News-<YYYY-MM-DD>.html`** (สำเนาเดียวกัน) ไปกับ draft ด้วย เพราะเมื่อเปิดไฟล์แนบในเบราว์เซอร์ ลิงก์จะเป็น URL ต้นฉบับสะอาด **ไม่ถูก Gmail ห่อด้วย `google.com/url`** → คลิกเข้าหน้าข่าวตรงทันที. **ข้อจำกัด:** MCP `create_draft` แนบไฟล์ไม่ได้ (R-06) → ใช้ BR-10 แทน |
| **BR-10 — ลิงก์ "ดูอีเมลนี้เป็นหน้าเว็บ" ท้ายอีเมล** | แปะ **ลิงก์ท้ายสุดของอีเมล** ("เปิดเวอร์ชันเว็บ (คลิกลิงก์ข่าวได้โดยตรง สำหรับตรวจสอบ)") ผ่าน `build_html_digest.py --web-link <URL>` เปิดแล้วเป็น **หน้าเว็บจริง คลิกข่าวได้ตรง** ไม่ผ่าน Gmail wrapper. **วิธีโฮสต์ที่เลือก:** เผยแพร่ไฟล์ standalone เข้า **public GitHub repo** (`web/Sansiri-News-<iso>.html`) แล้วลิงก์ผ่าน **htmlpreview** (`https://htmlpreview.github.io/?https://raw.githubusercontent.com/<owner>/<repo>/main/web/<file>`) — เปิดได้ทุกคน เรนเดอร์เป็นหน้าเว็บ. **ไม่ใช้ Google Drive** เพราะ Drive ไม่เรนเดอร์ HTML เป็นหน้าเว็บ (ให้โหลดไฟล์) + ตั้ง public อัตโนมัติไม่ได้. **อัตโนมัติ (R-09):** cloud run ต้อง `git commit && push` ไฟล์ web เข้า repo ได้ (ถ้า push ไม่ได้ ให้สร้าง draft โดยไม่มีลิงก์ท้าย) |
| **BR-06 — ขอบเขตการพาดพิง** | นับรวมข่าวที่ "เอ่ยถึงแสนสิริ" แม้บทความหลักจะเป็นเรื่องอื่น |
| **BR-07 — ขอบเขตติดตาม** | กลุ่มแสนสิริ = Sansiri + Plus Property (+ LPP); คู่แข่ง = Supalai, AP (Thailand), Ananda, Noble, Origin, Pruksa, LPN, Land & Houses, Magnolia/MQDC, Property Perfect, Q House, Raimon Land, Sena, SC Asset, Singha Estate |

> รายการคีย์เวิร์ด/ผู้บริหาร/Top Media ฉบับเต็ม เก็บเป็นไฟล์ reference ในสกิล — ดู [Techspec.md §7](./Techspec.md)

---

## 8. Non-Functional Requirements

| ID | Requirement |
|---|---|
| **NFR-01** | **Headless execution** — รันบน cloud โดยไม่มี GUI/เบราว์เซอร์/คนสั่ง |
| **NFR-02** | **Timezone** — อ้างอิง Asia/Bangkok ทุกการคำนวณวันเวลา |
| **NFR-03** | **Idempotency** — รันซ้ำในวันเดียวกันไม่สร้าง draft ซ้อน |
| **NFR-04** | **ความปลอดภัย** — ไม่ฝัง secret/credential ในโค้ดหรือไฟล์สกิล ใช้ env/Script properties |
| **NFR-05** | **Gmail HTML compatibility** — inline CSS, table layout, ไม่มี `<style>`, ไม่ใช้ Noto Sans Thai, เคารพ body cap ~102 KB |
| **NFR-06** | **ต้นทุนต่ำ** — งบประมาณระดับไม่กี่บาท/ฉบับ (อ้างอิง weekly ~3 บาท/ฉบับของระบบเดิม) |
| **NFR-07** | **Determinism & auditability** — ขั้นตอนเป็นสคริปต์ + artifact ไฟล์กลาง (`*_parsed.json`, `digest_*.json`, `digest_*.html`) ตรวจย้อนหลังได้ |
| **NFR-08** | **Observability** — มี smoke test + failure report เพื่อรู้สถานะการรัน |

---

## 9. Data Sources & Constraints

- **แหล่งข้อมูลเดียว:** อีเมล iQNewsClip ผ่าน **Gmail MCP** (`search_threads`, `get_thread`)
- **ข้อจำกัดที่ยอมรับ:** ไม่มี browser → ไม่อ่านบทความ print ฉบับเต็ม; สรุปจากพาดหัว + บริบทเท่าที่อยู่ในอีเมล
- **ทางเลือกเสริม (ไม่ใช่ core):** อาจใช้ **WebFetch** ดึงเนื้อหาบทความ *online* ที่เป็น URL สาธารณะ (ไม่ต้องล็อกอิน) เพื่อให้สรุปมีรายละเอียดขึ้น — เปิดใช้ภายหลังได้โดยไม่ขัดกับหลัก headless

---

## 10. Success Metrics

- **SM-01** — มี draft พร้อมตรวจในกล่อง Drafts ภายใน ~07:00–08:00 ทุกวันทำการ (≥ 95% ของวัน)
- **SM-02** — ทีม PR แก้ไขถ้อยคำเฉลี่ย ≤ จำนวนที่ตกลงกันต่อฉบับ ก่อนกดส่ง
- **SM-03** — ไม่มี "การรันที่ล้มเหลวแบบเงียบ" (ทุกความล้มเหลวมี failure report)
- **SM-04** — ข่าวที่ผ่าน QG ไม่มีกรณี off-topic/brand-damaging หลุดถึงผู้รับ

---

## 11. Risks & Open Questions

| ID | ความเสี่ยง / คำถาม | แนวทาง |
|---|---|---|
| **R-01** | **Gmail MCP ใน headless cron run** — MCP ที่ผูกกับ claude.ai อาจไม่พร้อมใช้งานในการรันแบบ scheduled/headless | ต้องตรวจสอบ/ตั้งค่า OAuth ให้ Gmail MCP ใช้ได้ใน cloud runtime ก่อน go-live (ดู [Techspec.md §3, §11](./Techspec.md)) — **ความเสี่ยงหลัก** |
| **R-02** | **ความลึกของสรุป** เมื่ออ่านได้แค่พาดหัว/บริบทในอีเมล | พิจารณา WebFetch online URL เป็น enrichment (§9) |
| **R-03** | เวลาอีเมล iQNewsClip มาถึงไม่ตรงกัน / มาช้า | เผื่อ retry/grace window + ใช้ failure report |
| **R-04** | รูปแบบอีเมล iQNewsClip เปลี่ยน (HTML↔plaintext) | parser รองรับสองรูปแบบ + smoke test ดักจับ |

---

## 12. Traceability

- `FR-NN` / `NFR-NN` / `BR-NN` ในเอกสารนี้ถูกอ้างอิงจาก components `C-NN` ใน [Techspec.md](./Techspec.md),
  จากสเปกหน้าจอ `UX-NN` ใน [uxui.md](./uxui.md), และจาก tasks `T-NNN` (ฟิลด์ `prdRefs`) ใน [features.json](./features.json)
- สายโยง: **requirement (PRD) → component (Techspec) → screen (uxui) → task (features.json)**
