# Top Media list

Outlets that earn a ranking bonus during cluster selection (`scripts/common.py`
`TOP_MEDIA`). A cluster appearing in any of these is weighted up (quality over
raw repetition — aligns with the AMEC principle of weighting credible media).

## Newspapers / business press
- Bangkok Post (bangkokpost.com)
- กรุงเทพธุรกิจ (bangkokbiznews.com)
- ประชาชาติธุรกิจ (prachachat.net)
- ฐานเศรษฐกิจ
- ผู้จัดการ / MGR Online (mgronline.com)

## General news (high reach)
- ไทยรัฐ (thairath.co.th)

## Property / real-estate verticals
- Propholic (propholic.com)
- Think of Living (thinkofliving.com)
- DDproperty (ddproperty.com)
- Homeday

## Finance / stock
- ข่าวหุ้น
- หุ้นอินไซด์
- ทันหุ้น (thunhoon.com)

> Extend `TOP_MEDIA` in `scripts/common.py` to add outlets. Matching is
> case-insensitive substring against the parsed `media_title`.
