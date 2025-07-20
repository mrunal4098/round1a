import math
from typing import Dict
from .config import Config

def score_candidate(feat: Dict) -> float:
    # Base
    s = 0.0
    rel = feat["rel_font_size"]
    # Boost relative font
    s += Config.W_REL_FONT * min(rel, 2.0)

    if feat["is_bold"]:
        s += Config.W_BOLD
    if feat["starts_numbering"]:
        s += Config.W_NUMBERING
    # Gap above isolation
    gap = feat.get("gap_above")
    if gap is not None and gap >= Config.GAP_ABOVE_MIN_ISOLATION:
        s += Config.W_GAP_ABOVE
    if feat.get("title_case"):
        s += Config.W_TITLE_CASE
    if feat.get("all_caps"):
        s += Config.W_ALL_CAPS

    # Penalties
    if feat["ends_with_period"]:
        s -= 0.6
    if feat["word_count"] > Config.MAX_HEADING_WORDS:
        s -= 1.0
    # Slight penalty for extremely short 1-word all lower:
    if feat["word_count"] == 1 and feat["text"].islower():
        s -= 0.3

    return round(s, 3)
