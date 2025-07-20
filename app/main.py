import json, time, pathlib, sys
from .pdf_loader import load_document
from .layout import build_lines
from .features import compute_features
from .level_assign import assign_levels

INPUT_DIR = pathlib.Path("/app/input")
OUTPUT_DIR = pathlib.Path("/app/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def process_pdf(pdf_path: pathlib.Path):
    doc_ctx = load_document(str(pdf_path))
    lines = build_lines(doc_ctx)
    feats = compute_features(lines, doc_ctx.page_count)

    # Build candidate list with richer fields for level assignment
    cand_list = []
    for f in feats:
        if f["candidate_heading"]:
            cand_list.append({
                "page": f["page"],
                "text": f["text"],
                "avg_size": f["avg_size"],
                "rel_font_size": f["rel_font_size"],
                "is_bold": f["is_bold"],
                "starts_numbering": f["starts_numbering"],
                "gap_above": f["gap_above"]
            })

    level_debug = []
    title_text = pdf_path.stem
    outline_entries = []

    if cand_list:
        assigned, title_c = assign_levels(cand_list, doc_ctx.page_count)
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
            level_debug.append({
                "page": c["page"],
                "text": c["text"][:140],
                "assigned": lvl,
                "avg_size": c["avg_size"],
                "rel_font": c["rel_font_size"]
            })

    # Sort outline by page then keep doc order (already mostly)
    outline_entries.sort(key=lambda x: (x["page"]))

    # Fill JSON
    preview = [{
        "page": f["page"],
        "text": f["text"][:100],
        "rel_font": f["rel_font_size"],
        "bold": f["is_bold"]
    } for f in feats[:10]]

    candidates_preview = [{
        "page": c["page"],
        "text": c["text"][:100]
    } for c in cand_list]

    data = {
        "title": title_text,
        "outline": outline_entries,
        "_debug_line_preview": preview,
        "_debug_candidates": candidates_preview,
        "_debug_level_assign": level_debug
    }

    out_file = OUTPUT_DIR / (pdf_path.stem + ".json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    t0 = time.time()
    pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdfs:
        print("[INFO] No PDFs found in /app/input.", file=sys.stderr)
    for p in pdfs:
        print(f"[INFO] Processing {p.name}", file=sys.stderr)
        process_pdf(p)
    print(f"[INFO] Step 4 level assignment done in {time.time()-t0:.2f}s", file=sys.stderr)

if __name__ == "__main__":
    main()
