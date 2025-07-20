import fitz
from dataclasses import dataclass
from typing import List

@dataclass
class PageContext:
    index: int
    width: float
    height: float
    raw_dict: dict  # PyMuPDF "dict" extraction structure

@dataclass
class DocumentContext:
    path: str
    page_count: int
    pages: List[PageContext]

def load_document(pdf_path: str) -> DocumentContext:
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        # Use dict extraction to preserve structure: blocks -> lines -> spans
        raw = page.get_text("dict")
        pages.append(PageContext(
            index=i,
            width=page.rect.width,
            height=page.rect.height,
            raw_dict=raw
        ))
    return DocumentContext(path=pdf_path, page_count=doc.page_count, pages=pages)
