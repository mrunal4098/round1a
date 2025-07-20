import json, time, pathlib, sys
from .pdf_loader import load_document
from .layout import build_lines
from .features import compute_features
from .level_assign import assign_levels
from .scoring import score_candidate
from .config import Config

INPUT_DIR = pathlib.Path("/app/input")
OUTPUT_DIR = pathlib.Path("/app/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def process_pdf(pdf_path: pathlib.Path):
    doc_ctx = load_document(str(pdf_path))
    lines = build_lines(doc_ctx)
    feats = compute_features(lines, doc_ctx.page_count)

    # Build enriched candidates
    cand_list = []
    for f in feats:
        if f["candidate_heading"]:
            sc = score_candidate(f)
            cand_list.append({
                "page": f["page"],
                "text": f["text"],
                "avg_size": f["avg_size"],
                "rel_font_size": f["rel_font_size"],
                "is_bold": f["is_bold"],
                "starts_numbering": f["starts_numbering"],
                "gap_above": f["gap_above"],
                "score": sc
            })

    # Keep stable order (page), then maybe by score only for debug display later
    cand_list.sort(key=lambda c: (c["page"], -c["score"]))

    outline_entries = []
    level_debug = []
    title_text = pdf_path.stem

    if cand_list:
        assigned, title_c = assign_levels(cand_list, doc_ctx.page_count)
        if title_c:
            title_text = title_c["text"]
        for c in assigned:
            lvl = c["proposed_level"]
            if lvl == "TITLE":
                continue
            outline_entries.append({
                "level": lvl,
                "text": c["text"],
                "page": c["page"]
            })
            if Config.INCLUDE_DEBUG:
                level_debug.append({
                    "page": c["page"],
                    "text": c["text"][:140],
                    "assigned": lvl,
                    "avg_size": c["avg_size"],
                    "rel_font": c["rel_font_size"],
                    "score": c.get("score")
                })

    outline_entries.sort(key=lambda x: (x["page"]))

    if Config.INCLUDE_DEBUG:
        preview = [{
            "page": f["page"],
            "text": f["text"][:100],
            "rel_font": f["rel_font_size"],
            "bold": f["is_bold"]
        } for f in feats[:10]]
        candidates_preview = [{
            "page": c["page"],
            "text": c["text"][:100],
            "score": c["score"]
        } for c in cand_list]
    else:
        preview = []
        candidates_preview = []
        level_debug = []

    data = {
        "title": title_text,
        "outline": outline_entries
    }
    if Config.INCLUDE_DEBUG:
        data["_debug_line_preview"] = preview
        data["_debug_candidates"] = candidates_preview
        data["_debug_level_assign"] = level_debug

    out_file = OUTPUT_DIR / (pdf_path.stem + ".json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    t0 = time.time()
    # Case-insensitive discovery of PDFs
    pdfs = sorted([p for p in INPUT_DIR.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"])
    if not pdfs:
        print("[INFO] No PDFs found in /app/input.", file=sys.stderr)
    for p in pdfs:
        print(f"[INFO] Processing {p.name}", file=sys.stderr)
        process_pdf(p)
    print(f"[INFO] Step 5 (scoring+tuning) done in {time.time()-t0:.2f}s", file=sys.stderr)

if __name__ == "__main__":
    main()
