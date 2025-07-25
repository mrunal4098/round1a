from app.pdf_loader import load_document
import pprint, sys, os, json

PDF = "/app/input/F_ar.pdf"
print("Trying to load:", PDF, file=sys.stderr)

doc_ctx = load_document(PDF)
print("Type of doc_ctx :", type(doc_ctx))
print("dir(doc_ctx)    :", dir(doc_ctx))
print("page_count      :", getattr(doc_ctx, "page_count", "N/A"))

# If there are pages, show the first page object's attributes
pages = getattr(doc_ctx, "pages", [])
print("pages length    :", len(pages))

if pages:
    p0 = pages[0]
    print("\nFirst PageContext dir:")
    pprint.pprint(dir(p0), width=120)
    # Show the first 3 non-dunder attributes & their repr
    print("\nSample of attributes on PageContext:")
    for name in [n for n in dir(p0) if not n.startswith("_")][:3]:
        print(f"  {name} =", repr(getattr(p0, name)))
