import re, statistics
from typing import List, Dict, Any

from .layout import Line
from .config import Config
from .text_utils import (
    normalize_all_digits,
    normalize_rtl,
    script_ratios,
    dominant_script,
)

# ───────────────────────────────────────── heading patterns ──────────────────
_numbering_re      = re.compile(r'^\d+(?:\.\d+)*\s')
_jp_chapter_re     = re.compile(r'^第[0-9]+章')
_romaji_jp_re      = re.compile(r'^Dai[0-9]+sho', re.IGNORECASE)
_ar_chapter_re     = re.compile(r'^(?:الفصل|الباب|المبحث)\s*[0-9٠-٩]+')
_hi_chapter_re     = re.compile(r'^अध्याय\s*[0-9]+')
_appendix_re       = re.compile(r'^Appendix\s+[A-Z]\b', re.IGNORECASE)
_roman_re          = re.compile(r'^[IVXLC]+\.?\s')

_word_split_re     = re.compile(r'\s+')
_caption_prefix_re = re.compile(r'^(figure|fig\.|table|tab\.)\b', re.IGNORECASE)
_dot_leader_re     = re.compile(r'\.{3,}')

# ───────────────────────────────────────── helpers ────────────────────────────
def _median_body_font(lines: List[Line]) -> float:
    sizes = [ln.avg_size for ln in lines if ln.avg_size > 0]
    if not sizes:
        return 1.0
    sizes.sort()
    trimmed = sizes[: int(len(sizes) * 0.95)] or sizes
    try:
        return statistics.median(trimmed) or 1.0
    except statistics.StatisticsError:
        return trimmed[0]

# ───────────────────────────────────────── main feature fn ────────────────────
def compute_features(lines: List[Line], page_count: int) -> List[Dict[str, Any]]:
    body_med = _median_body_font(lines)

    # track repetition (running headers)
    text_pages: Dict[str, set[int]] = {}
    for ln in lines:
        text_pages.setdefault(normalize_rtl(ln.text.strip()), set()).add(ln.page)

    feats: list[dict[str, Any]] = []

    for idx, ln in enumerate(lines):
        raw = ln.text.strip()
        raw = normalize_rtl(raw)               # logical-order Arabic
        norm_digits = normalize_all_digits(raw)

        words = [w for w in _word_split_re.split(raw) if w]
        word_count = len(words)
        char_count = len(raw)

        rel_font = (ln.avg_size / body_med) if body_med else 1.0
        is_bold  = ln.bold_frac >= 0.6

        # numbering / chapter patterns
        starts_numbering = bool(_numbering_re.match(norm_digits))
        if _jp_chapter_re.match(norm_digits)   : starts_numbering = True
        if _romaji_jp_re.match(norm_digits)    : starts_numbering = True
        if _ar_chapter_re.match(norm_digits)   : starts_numbering = True
        if _hi_chapter_re.match(norm_digits)   : starts_numbering = True
        if _appendix_re.match(raw)             : starts_numbering = True
        if _roman_re.match(raw)                : starts_numbering = True

        ends_with_period = raw.endswith(('.', '?', '!', '。', '؟'))
        letters     = [c for c in raw if c.isalpha()]
        all_caps    = bool(letters) and all(ch.isupper() for ch in letters)
        title_case  = bool(words) and all((w[0].isupper() or not w[0].isalpha()) for w in words if w)

        # gap above (spacing heuristic)
        gap_above = None
        for j in range(idx - 1, -1, -1):
            if lines[j].page == ln.page:
                gap_above = ln.y0 - lines[j].y1
                break

        repeat_count   = len(text_pages.get(raw, set()))
        is_caption_like = bool(_caption_prefix_re.match(raw.lower()))
        has_dot_leader  = bool(_dot_leader_re.search(raw))

        ratios     = script_ratios(raw)
        dom_script = dominant_script(ratios)       
    # ── rescue: treat unknown lines that contain normal Arabic letters as Arabic ──

    if dom_script == "unknown" and re.search(r'[\u0600-\u06FF]', raw):

        dom_script = "arabic"
    # ── rescue: if ratios missed normal Arabic letters ──

    if dom_script == "unknown" and re.search(r'[\u0600-\u06FF]', raw):

        dom_script = "arabic"
        if dom_script == "unknown" and re.search(r'[\uFB50-\uFEFC]', raw):
               dom_script = "arabic"
        if dom_script == "arabic" and re.search(r'[0-9٠-٩]', norm_digits):
            starts_numbering = True

        feat = {
            "page"          : ln.page + 1,
            "text"          : raw,
            "avg_size"      : ln.avg_size,
            "rel_font_size" : round(rel_font, 3),
            "is_bold"       : is_bold,
            "word_count"    : word_count,
            "char_count"    : char_count,
            "starts_numbering": starts_numbering,
            "all_caps"      : all_caps,
            "title_case"    : title_case,
            "ends_with_period": ends_with_period,
            "gap_above"     : gap_above,
            "repeat_count"  : repeat_count,
            "is_caption_like": is_caption_like,
            "has_dot_leader": has_dot_leader,
            "lower_text"    : raw.lower(),
            "script_dom"    : dom_script,
            "script_ratios" : ratios,
        }
        feats.append(feat)


    for f in feats:
        script_dom = f["script_dom"]
        non_latin  = script_dom in ("cjk", "arabic", "devanagari")

        font_ok = (
            f["rel_font_size"] >= Config.REL_FONT_HEADING_MIN
            or (f["rel_font_size"] >= Config.REL_FONT_HEADING_LOWERED and f["is_bold"])
        )
        if f["script_dom"] == "arabic" and f["starts_numbering"]:
            font_ok = True        # accept body-sized Arabic headings
        casing_ok = f["is_bold"] or f["title_case"] or f["all_caps"]
        if non_latin:
            casing_ok = True  # casing unreliable ⇒ ignore

        candidate = (
            (
                font_ok
                or (f["is_bold"] and f["word_count"] <= Config.MAX_SHORT_HEADING_WORDS and not f["ends_with_period"])
                or f["starts_numbering"]
            )
            and 1 <= f["word_count"] <= Config.MAX_HEADING_WORDS
            and f["char_count"] >= 2
            and casing_ok
        )

        # extra rescue for non-Latin numbered headings
        if not candidate and non_latin and f["starts_numbering"]:
            candidate = True

        # black-list filters
        if candidate:
            if (
                f["repeat_count"] >= Config.RUNNING_HEADER_MIN_PAGES
                and (f["repeat_count"] / page_count) >= Config.RUNNING_HEADER_FRACTION
            ):
                candidate = False
            elif f["is_caption_like"] or f["has_dot_leader"]:
                candidate = False
            elif f["rel_font_size"] < 1.02 and not f["is_bold"] and not f["starts_numbering"] and not non_latin:
                candidate = False
            elif f["lower_text"].startswith("page "):
                candidate = False
            elif (
                script_dom == "latin"
                and f["text"].count(".") >= 2
                and f["rel_font_size"] < 1.15
                and not f["starts_numbering"]
            ):
                candidate = False

        f["candidate_heading"] = candidate

    _ar_basic_re = re.compile(r'^(المقدمة|الخاتمة)$')
    for f in feats:
        if _ar_basic_re.match(f["text"]):
            f["starts_numbering"] = True

    for f in feats:
        if not f["candidate_heading"]:
            continue

        multi_sent = (
            f["text"].count(".")
            + f["text"].count("؟")
            + f["text"].count("۔")
            + f["text"].count("।")
        )

        # kill multi-sentence lines (even bold) if smallish font
        if multi_sent >= 2 and f["rel_font_size"] < 1.30:
            f["candidate_heading"] = False
            continue
        # --- keep Arabic numbered headings even if the above matched ---
        if f["script_dom"] == "arabic" and f["starts_numbering"]:
            continue
        # very long Latin body line
        if f["word_count"] >= 12 and f["rel_font_size"] < 1.20:
            f["candidate_heading"] = False
            continue

        # long Arabic / Devanagari body sentence
        if (
            f["script_dom"] in ("arabic", "devanagari")
            and f["word_count"] >= 12
            and f["rel_font_size"] < 1.20
            and not f["starts_numbering"]
        ):
            f["candidate_heading"] = False
    # final rescue: keep numbered non-Latin lines that survived filters
    for f in feats:
        if f["starts_numbering"] and f["script_dom"] in ("cjk","arabic","devanagari"):
            f["candidate_heading"] = True


    return feats