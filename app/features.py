import re
import statistics
from typing import List, Dict, Any
from .layout import Line
from .config import Config

_numbering_re = re.compile(r'^\d+(?:\.\d+)*\s')
_word_split_re = re.compile(r'\s+')
_caption_prefix_re = re.compile(r'^(figure|fig\.|table|tab\.)\b', re.IGNORECASE)
_dot_leader_re = re.compile(r'\.{3,}')

def _median_body_font(lines: List[Line]) -> float:
    sizes = [ln.avg_size for ln in lines if ln.avg_size > 0]
    if not sizes:
        return 1.0
    sizes.sort()
    cutoff_index = int(len(sizes) * 0.95)
    trimmed = sizes[:cutoff_index] if cutoff_index > 0 else sizes
    try:
        return statistics.median(trimmed) or 1.0
    except statistics.StatisticsError:
        return trimmed[0] if trimmed else 1.0

def compute_features(lines: List[Line], page_count: int) -> List[Dict[str, Any]]:
    body_med = _median_body_font(lines)
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
        ends_with_period = text.endswith(('.', '?', '!'))
        letters = [c for c in text if c.isalpha()]
        all_caps = bool(letters) and all(ch.isupper() for ch in letters)
        title_case = bool(words) and all((w[0].isupper() or not w[0].isalpha()) for w in words if w)
        gap_above = None
        for j in range(idx - 1, -1, -1):
            if lines[j].page == ln.page:
                gap_above = ln.y0 - lines[j].y1
                break
        repeat_count = len(text_pages[text])
        is_caption_like = bool(_caption_prefix_re.match(text.lower()))
        has_dot_leader = bool(_dot_leader_re.search(text))  # TOC style
        lower_text = text.lower()

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
            "repeat_count": repeat_count,
            "is_caption_like": is_caption_like,
            "has_dot_leader": has_dot_leader,
            "lower_text": lower_text
        }
        features.append(feat)

    # Candidate logic with config thresholds
    for f in features:
        candidate = (
            (
                f["rel_font_size"] >= Config.REL_FONT_HEADING_MIN
                or (f["rel_font_size"] >= Config.REL_FONT_HEADING_LOWERED and f["is_bold"])
                or (f["is_bold"] and f["word_count"] <= Config.MAX_SHORT_HEADING_WORDS and not f["ends_with_period"])
                or f["starts_numbering"]
            )
            and 1 <= f["word_count"] <= Config.MAX_HEADING_WORDS
            and f["char_count"] >= 2
        )
        if candidate:
            # Exclusions
            if f["repeat_count"] >= Config.RUNNING_HEADER_MIN_PAGES and (f["repeat_count"]/page_count) >= Config.RUNNING_HEADER_FRACTION:
                candidate = False
            elif f["is_caption_like"]:
                candidate = False
            elif f["has_dot_leader"]:
                candidate = False
            elif f["rel_font_size"] < 1.02 and not f["is_bold"]:
                candidate = False
            elif f["lower_text"].startswith("page "):
                candidate = False
        f["candidate_heading"] = candidate
    return features
