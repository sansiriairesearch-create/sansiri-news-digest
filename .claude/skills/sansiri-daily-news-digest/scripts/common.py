"""Shared constants + helpers for the Sansiri Daily News Digest pipeline.

See ../../../docs/Techspec.md (C-02..C-06) and docs/PRD.md (BR-07) for the
canonical entity list and rules. Email-only / headless: no NCX/Chrome.
"""
import re
import unicodedata

# --- Entity model (PRD BR-07) -------------------------------------------------
SANSIRI_GROUP = ["Sansiri", "Plus Property", "LPP"]

COMPETITORS = [
    "Supalai", "AP (Thailand)", "Ananda", "Noble", "Origin", "Pruksa", "LPN",
    "Land & Houses", "Magnolia", "Property Perfect", "Q House", "Raimon Land",
    "Sena Development", "SC Asset", "Singha Estate",
]

# Aliases seen verbatim in the iQNewsClip email -> canonical name above.
COMPANY_ALIASES = {
    "Land & House": "Land & Houses",
    "SCAsset": "SC Asset",
    "SC ASset": "SC Asset",
    "Sena": "Sena Development",
    "MQDC": "Magnolia",
    "Magnolia Quality Development": "Magnolia",
    "Plus": "Plus Property",
}

# All recognizable company strings (canonical + aliases), longest first so that
# multi-word names win over substrings when matched as a suffix.
ALL_COMPANY_STRINGS = sorted(
    set(SANSIRI_GROUP + COMPETITORS + list(COMPANY_ALIASES.keys())),
    key=len, reverse=True,
)

MEDIA_TYPES = ("online", "social", "print")

# Top media outlets get a small ranking bonus during selection (C-03).
TOP_MEDIA = {
    "bangkokpost.com", "bangkok post", "กรุงเทพธุรกิจ", "bangkokbiznews.com",
    "prachachat.net", "ประชาชาติธุรกิจ", "thairath.co.th", "ไทยรัฐ",
    "mgronline.com", "ผู้จัดการ", "propholic.com", "propholic",
    "thinkofliving.com", "think of living", "ddproperty.com", "homeday",
    "หุ้นอินไซด์", "ข่าวหุ้น", "ฐานเศรษฐกิจ", "thunhoon.com",
}


def canon_company(name: str):
    """Normalize a raw company string to its canonical form, or None."""
    if not name:
        return None
    name = name.strip()
    if name in COMPANY_ALIASES:
        return COMPANY_ALIASES[name]
    if name in SANSIRI_GROUP or name in COMPETITORS:
        return name
    return None


def is_sansiri_group(company: str) -> bool:
    return canon_company(company) in SANSIRI_GROUP


def normalize_text(s: str) -> str:
    """For fuzzy dedupe/clustering: lowercase, strip punctuation & spaces."""
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"https?://\S+", "", s)
    s = re.sub(r"[#\"'`.,!?\-–—()\[\]:;/\\]", "", s)
    s = re.sub(r"\s+", "", s)
    return s.lower()


_DATAXET_PREFIX_RE = re.compile(r"^https?://re\.dataxet\.co/api/", re.IGNORECASE)
_PRINT_PDF_MARKER = "iqnewsclip.com/reportdl/printdl"


def is_print_pdf(url: str) -> bool:
    """A Dataxet print-clipping PDF (only reachable via the Dataxet proxy)."""
    return _PRINT_PDF_MARKER in (url or "")


def unwrap_dataxet(url: str) -> str:
    """Strip the `https://re.dataxet.co/api/` proxy prefix so the link points
    directly at the real article, and repair the `https:/` single-slash that the
    wrapper leaves behind. Print-clipping PDFs are returned unchanged (they are
    only accessible through the proxy). See docs/PRD.md BR-05 / uxui.md UX-03.
    """
    if not url or not _DATAXET_PREFIX_RE.match(url):
        return url
    if is_print_pdf(url):
        return url  # keep the proxy for scanned-newspaper PDFs
    rest = _DATAXET_PREFIX_RE.sub("", url)
    rest = re.sub(r"^(https?):/(?!/)", r"\1://", rest)  # https:/x -> https://x
    return rest


def parse_pr_value(s: str) -> float:
    try:
        return float(str(s).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def parse_reach(s) -> int:
    try:
        return int(str(s).replace(",", ""))
    except (ValueError, TypeError):
        return 0
