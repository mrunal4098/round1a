from app.pdf_loader import load_document
from app.features   import compute_features
import itertools, json

PDF = "/app/input/F_ar.pdf"        # change if needed

doc_ctx = load_document(PDF)       # returns a DocumentContext

# Flatten all lines from every page into one list
lines = list(itertools.chain.from_iterable(doc_ctx.pages))

# Compute features
feats = compute_features(lines, doc_ctx.page_count)

# Pick only the lines that the algorithm marked as candidate headings
cands = [f for f in feats if f["candidate_heading"]]

print("\n=== candidate headings ===")
print(json.dumps(cands, ensure_ascii=False, indent=2))

print("\n=== first-5 raw feature rows ===")
print(json.dumps(feats[:5], ensure_ascii=False, indent=2))