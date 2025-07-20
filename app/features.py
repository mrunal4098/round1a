import re
import statistics
from typing import List, Dict, Any
from .layout import Line

_numbering_re = re.compile(r'^\d+(?:\.\d+)*\s')
_word_split_re = re.compile(r'\s+')
_caption_prefix_re = re.compile(r'^(figure|fig\.|table|tab\.)\b', re.IGNORECASE)

def _median_body_font(lines: List[Line]) -> float:
    sizes = [ln.avg_size for ln in lines if ln.avg_size > 0]
    if not sizes:
        return 1.0
    sizes.sort()
    # remove top 5% outliers
    cutoff_index = int(len(sizes) * 0.95)
    trimmed = sizes[:cutoff_index] if cutoff_index > 0 else sizes
    if not trimmed:
        trimmed = sizes
    try:
        return statistics.median(trimmed)
    except statistics.StatisticsError:
        return trimmed[0]

def compute_features(lines: List[Line], page_count: int) -> List[Dict[str, Any]]:
    body_med = _median_body_font(lines)
    # repetition map for header/footer detection
    text_pages = {}
    for ln in lines:
        key = ln.text.strip()
        text_pages.setdefault(key, set()).add(ln.page)

    features = []
    for idx, ln in enumerate(lines):
        text = ln.text.strip()
        words = [w for w in _word_split_re.split(text) if w]
        word_count = len(words)
        char_count = len(text)
        is_bold = ln.bold_frac >= 0.6
        rel_font = (ln.avg_size / body_med) if body_med > 0 else 1.0
        starts_numbering = bool(_numbering_re.match(text))
        ends_with_period = bool(text.endswith(('.', '?', '!')))
        letters = [c for c in text if c.isalpha()]
        all_caps = False
        title_case = False
        if letters:
            if all(ch.isupper() for ch in letters):
                all_caps = True
            # naive title case: every word (length>0) starts uppercase (or is numeric)
            if words and all((w[0].isupper() or not w[0].isalpha()) for w in words):
                title_case = True

        # gap_above: need previous line on same page
        gap_above = None
        # previous line with same page
        for j in range(idx - 1, -1, -1):
            if lines[j].page == ln.page:
                gap_above = ln.y0 - lines[j].y1
                break

        repeat_count = len(text_pages[text])

        feat = {
            "page": ln.page + 1,
            "text": text,
            "avg_size": ln.avg_size,
            "rel_font_size": round(rel_font, 3),
            "is_bold": is_bold,
            "word_count": word_count,
            "char_count": char_count,
            "starts_numbering": starts_numbering,
            "all_caps": all_caps,
            "title_case": title_case,
            "ends_with_period": ends_with_period,
            "gap_above": gap_above,
            "repeat_count": repeat_count
        }
        features.append(feat)
    # mark candidates
    for f in features:
        candidate = (
            (
                f["rel_font_size"] >= 1.08
                or (f["is_bold"] and f["word_count"] <= 12 and not f["ends_with_period"])
                or f["starts_numbering"]
            )
            and f["word_count"] >= 1
            and f["char_count"] >= 2
        )
        # exclusion filters
        txt_lower = f["text"].lower()
        if candidate:
            if f["repeat_count"] >= 2 and (f["repeat_count"] / page_count) >= 0.5:
            # Exclude only if appears on >=50% of pages AND at least twice (true running header/footer)
                candidate = False
            elif f["word_count"] > 20:
                candidate = False
            elif _caption_prefix_re.match(txt_lower):
                candidate = False
            elif (not f["is_bold"] and f["rel_font_size"] < 1.02 and txt_lower == txt_lower.lower()):
                candidate = False
        f["candidate_heading"] = candidate
    return features
