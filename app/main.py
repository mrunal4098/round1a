import json, time, pathlib, sys
from .pdf_loader import load_document
from .layout import build_lines
from .features import compute_features

INPUT_DIR = pathlib.Path("/app/input")
OUTPUT_DIR = pathlib.Path("/app/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def process_pdf(pdf_path: pathlib.Path):
    doc_ctx = load_document(str(pdf_path))
    lines = build_lines(doc_ctx)
    feats = compute_features(lines, doc_ctx.page_count)

    # debug previews
    preview_lines = [{
        "page": f["page"],
        "text": f["text"][:120],
        "avg_size": f["avg_size"],
        "rel_font": f["rel_font_size"],
        "bold": f["is_bold"]
    } for f in feats[:10]]

    candidates = [{
        "page": f["page"],
        "text": f["text"][:140],
        "rel_font": f["rel_font_size"],
        "is_bold": f["is_bold"],
        "starts_numbering": f["starts_numbering"]
    } for f in feats if f["candidate_heading"]]

    data = {
        "title": pdf_path.stem,
        "outline": [],  # still empty this step
        "_debug_line_preview": preview_lines,
        "_debug_candidates": candidates
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
    print(f"[INFO] Step 3 feature extraction done in {time.time()-t0:.2f}s", file=sys.stderr)

if __name__ == "__main__":
    main()
