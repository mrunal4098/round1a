import os, json, time, pathlib, sys

INPUT_DIR = pathlib.Path("/app/input")
OUTPUT_DIR = pathlib.Path("/app/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def process_pdf(pdf_path):
    # Placeholder: produce dummy outline (empty) and fake title
    data = {
        "title": pdf_path.stem,
        "outline": []
    }
    out_path = OUTPUT_DIR / (pdf_path.stem + ".json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    t0 = time.time()
    pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdfs:
        print("[INFO] No PDFs found in /app/input (this is fine for Step 1).", file=sys.stderr)
    for p in pdfs:
        print(f"[INFO] Processing {p.name}", file=sys.stderr)
        process_pdf(p)
    print(f"[INFO] Done in {time.time()-t0:.2f}s", file=sys.stderr)

if __name__ == "__main__":
    main()
