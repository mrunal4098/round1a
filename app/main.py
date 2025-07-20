import json, time, pathlib, sys
from .pdf_loader import load_document
from .layout import build_lines

INPUT_DIR = pathlib.Path("/app/input")
OUTPUT_DIR = pathlib.Path("/app/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def process_pdf(pdf_path: pathlib.Path):
    doc_ctx = load_document(str(pdf_path))
    lines = build_lines(doc_ctx)
    preview = [{
        "page": ln.page + 1,
        "text": ln.text[:120],
        "avg_size": ln.avg_size,
        "bold_frac": ln.bold_frac
    } for ln in lines[:15]]

    data = {
        "title": pdf_path.stem,
        "outline": [],
        "_debug_line_preview": preview
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
        print(f"[INFO] Parsing {p.name}", file=sys.stderr)
        process_pdf(p)
    print(f"[INFO] Step 2 parsing done in {time.time()-t0:.2f}s", file=sys.stderr)

if __name__ == "__main__":
    main()
