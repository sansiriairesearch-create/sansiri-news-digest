# Decisions & Regression Log — Sansiri Daily News Digest

> "ข้อตกลง" ที่บันทึก **ปัญหาที่เคยเกิด → วิธีแก้ → การ์ดที่กันไม่ให้เกิดซ้ำ**
> ทุกครั้งที่เจอบั๊ก/ตัดสินใจสำคัญ ให้เพิ่มแถวที่นี่ พร้อมผูกกับ rule/check ที่บังคับใช้จริง

### Related documents
- [PRD.md](./PRD.md) · [Techspec.md](./Techspec.md) · [uxui.md](./uxui.md) · [features.json](./features.json)

---

## A. Regression log (อย่าให้เกิดซ้ำ)

| # | ปัญหาที่เกิด | สาเหตุ | วิธีแก้ | การ์ดกันซ้ำ (อัตโนมัติ) |
|---|---|---|---|---|
| **D-01** | ลิงก์ข่าวเด้งไป URL ของ Dataxet (`re.dataxet.co/api/https:/…`) ไม่เข้าหน้าข่าวจริง | ใส่ URL ดิบจากอีเมลที่ห่อ proxy 2 ชั้น | `unwrap_dataxet()` ถอด prefix + ซ่อม `https:/`→`https://` สำหรับ online/social (print PDF คงไว้) | **Check C10** (online/social ต้องไม่มี `re.dataxet.co/api/`) + **BR-08** |
| **D-02** | Banner สีหาย → ตัวอักษร "Sansiri News" ขาวมองไม่เห็น | client/compose view ตัด CSS `background-color` | เพิ่ม attribute `bgcolor` คู่กับ `background-color` ทั้งแถบทอง/น้ำเงิน | **Check C13** (ต้องมี `bgcolor="#D4A843"` และ `="#1B3A5C"`) + uxui UX-02 |
| **D-03** | หน้า Google **Redirect Notice** ขึ้นตอนคลิกลิงก์ | คลิกจาก **ฉบับร่าง** ที่ยังไม่มีลายเซ็น `usg=` (Gmail เติมตอนส่ง) + Gmail ห่อทุกลิงก์ด้วย `google.com/url` (ปิดจากผู้ส่งไม่ได้) | อธิบาย/ยอมรับ: ส่งจริงแล้วเด้งตรง; ลิงก์ใน source ของเราต้องสะอาด | **Check C14** (source ต้องไม่มี `google.com/url` ฝังมาเอง) + uxui UX-06b |
| **D-04** | สร้าง **draft ทดสอบซ้ำหลายฉบับ** รกกล่อง | รันสร้าง draft ซ้ำโดยไม่เช็กของเดิม | Idempotency pre-check ก่อนสร้าง | **FR-16 / SKILL Step 0** (`daily_meta.py` → `list_drafts`/`search_threads`; มีแล้วให้หยุด) |
| **D-05** | แนบไฟล์ HTML เข้า draft ไม่ได้ (`Internal error`) | Gmail MCP `create_draft` **ไม่รองรับ attachments** | ทดสอบยืนยันข้อจำกัด; เตรียมไฟล์ standalone ไว้แนบผ่าน production send path (Gmail API/GAS) | **Techspec R-06** + **BR-09** (ไม่พยายามแนบผ่าน MCP; ใช้ `build_standalone.py`) |
| **D-06** | base64 ก้อนใหญ่ทำตัวช่วยโดน policy filter/รันค้าง | ส่ง base64 ขนาดใหญ่ผ่าน model context | หลีกเลี่ยงการส่ง base64 ผ่าน MCP create_draft (เพราะแนบไม่ได้อยู่แล้ว — D-05) | เลิกใช้ attachment ผ่าน MCP (อ้างอิง D-05) |

## B. Locked design decisions (อ้างอิงคำตัดสินกับมุก)

| # | การตัดสินใจ | สถานะ |
|---|---|---|
| **DD-1** | ผลลัพธ์ = Daily Digest 5+5 พร้อมสรุป AI เท่านั้น (ตาราง/Weekly เป็นของ GAS) | ล็อก |
| **DD-2** | สร้าง **draft เท่านั้น ไม่ส่งเอง** (human กดส่ง) | ล็อก |
| **DD-3** | แหล่งข้อมูล = อีเมล iQNewsClip อย่างเดียว (headless ไม่มี NCX/Chrome) | ล็อก |
| **DD-4** | greenfield Claude Code แยกจาก GAS | ล็อก |
| **DD-5** | **Header banner = APPROVED & LOCKED** (uxui UX-01/02) ห้ามแก้ layout/สี/ข้อความหัวโดยไม่ขออนุมัติ | ล็อก |

## C. มาตรฐานการทำงาน (กันพลาดก่อนสร้าง draft ทุกครั้ง)

1. รัน `python3 scripts/smoke_test.py` ให้ผ่านก่อน (parse→cluster→build→validate บน fixtures)
2. ทุก digest ต้องผ่าน `pre_draft_check.py` **exit 0** (14 ข้อ) ก่อนเรียก `create_draft`
3. ทำ **idempotency pre-check** (Step 0) ทุกครั้ง — มี draft/อีเมลของวันนั้นแล้วให้หยุด
4. เพิ่มแถวใน Regression log (ส่วน A) ทุกครั้งที่เจอบั๊กใหม่ พร้อม "การ์ดกันซ้ำ" ที่ตรวจได้อัตโนมัติ
