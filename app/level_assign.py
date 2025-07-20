import re
from typing import List, Dict, Any

_numbering_re = re.compile(r'^(\d+(?:\.\d+)*)\s')

def _extract_number_depth(text: str):
    m = _numbering_re.match(text)
    if not m:
        return None
    seq = m.group(1)
    depth = seq.count('.') + 1
    return min(depth, 3)

def _cluster_font_sizes(candidates: List[Dict[str,Any]], tolerance=0.75):
    """Return list of tiers, each tier is list of avg_sizes; largest first."""
    sizes = sorted({round(c["avg_size"],2) for c in candidates}, reverse=True)
    tiers = []
    for s in sizes:
        placed = False
        for tier in tiers:
            if abs(tier[0] - s) <= tolerance:  # compare with tier representative
                tier.append(s)
                placed = True
                break
        if not placed:
            tiers.append([s])
    return tiers  # already largest first

def assign_levels(candidates: List[Dict[str,Any]], page_count: int):
    """Mutates candidate dicts adding 'proposed_level'."""
    if not candidates:
        return

    # Multi-line merge pass (simple)
    merged = []
    skip_next = False
    for i,c in enumerate(candidates):
        if skip_next:
            skip_next = False
            continue
        if i+1 < len(candidates):
            n = candidates[i+1]
            # same page, vertical gap small, similar font size
            gap = n.get("gap_above")
            if c["page"] == n["page"] and gap is not None and gap <= 2 and abs(c["avg_size"]-n["avg_size"]) <= 0.5:
                # merge
                merged_text = (c["text"] + " " + n["text"]).strip()
                c["text"] = merged_text
                skip_next = True
        merged.append(c)
    candidates = merged

    # Title selection: largest rel_font_size on page 1 else global
    page1 = [c for c in candidates if c["page"] == 1]
    title_candidate = (page1 or candidates)[0]
    # choose max by rel_font then avg_size
    title_candidate = max(page1 or candidates, key=lambda x: (x["rel_font_size"], x["avg_size"]))
    title_candidate["proposed_level"] = "TITLE"

    remaining = [c for c in candidates if c is not title_candidate]

    # Numbering depth preliminary assignment
    for c in remaining:
        depth = _extract_number_depth(c["text"])
        if depth:
            c["proposed_level"] = {1:"H1",2:"H2",3:"H3"}[depth]

    # Font tier clustering for unassigned
    unassigned = [c for c in remaining if "proposed_level" not in c]
    tiers = _cluster_font_sizes(remaining)  # base on remaining
    tier_to_level = {}
    # Map tiers in order: largest->H1, next->H2, next->H3
    for i,tier in enumerate(tiers):
        lvl = "H1" if i==0 else "H2" if i==1 else "H3"
        for s in tier:
            tier_to_level[s] = lvl
    for c in unassigned:
        c["proposed_level"] = tier_to_level.get(round(c["avg_size"],2),"H3")

    # Context promotions
    seen_h1 = False
    last_level = None
    for c in remaining:
        lvl = c["proposed_level"]
        if lvl == "H1":
            seen_h1 = True
        elif lvl == "H2" and not seen_h1:
            c["proposed_level"] = "H1"
            seen_h1 = True
        elif lvl == "H3":
            # if no H2 since last H1, promote
            if last_level not in ("H2","H3"):
                c["proposed_level"] = "H2"
        last_level = c["proposed_level"]

    # Return ordered list again (title + others in original order)
    ordered = []
    # Maintain original relative ordering: iterate original candidates list
    for c in candidates:
        ordered.append(c)
    return ordered, title_candidate

def dedupe_outline(entries):
    seen = set()
    out = []
    for e in entries:
        key = (e["level"], e["text"], e["page"])
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out
