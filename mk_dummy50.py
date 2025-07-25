import fitz, sys
src = fitz.open("/app/input/A.pdf")  # any small 1–2 page pdf is fine
out = fitz.open()
for _ in range(50):
    out.insert_pdf(src, from_page=0, to_page=0)   # duplicate first page
out.save("/app/input/dummy50.pdf")
