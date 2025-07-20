from typing import List
from dataclasses import dataclass, field
from .pdf_loader import DocumentContext

@dataclass
class Line:
    page: int
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    spans: list = field(default_factory=list)
    font_sizes: list = field(default_factory=list)
    primary_font: str = ""
    avg_size: float = 0.0
    bold_frac: float = 0.0

def _is_span_bold(font_name: str) -> bool:
    if not font_name: return False
    fn = font_name.lower()
    return ("bold" in fn) or ("black" in fn) or ("semibold" in fn) or ("heavy" in fn)

def build_lines(doc_ctx: DocumentContext) -> List[Line]:
    lines: List[Line] = []
    for page_ctx in doc_ctx.pages:
        for blk in page_ctx.raw_dict.get("blocks", []):
            if blk.get("type",0) != 0:
                continue
            for l in blk.get("lines", []):
                spans = l.get("spans", [])
                if not spans:
                    continue
                raw_text = "".join(s.get("text","") for s in spans).strip()
                if not raw_text:
                    continue
                x0 = min(s["bbox"][0] for s in spans)
                y0 = min(s["bbox"][1] for s in spans)
                x1 = max(s["bbox"][2] for s in spans)
                y1 = max(s["bbox"][3] for s in spans)
                sizes = [float(s.get("size",0)) for s in spans if s.get("size")]
                fonts = [s.get("font","") for s in spans]
                bold_flags = [_is_span_bold(f) for f in fonts]
                avg_size = sum(sizes)/len(sizes) if sizes else 0.0
                bold_frac = sum(bold_flags)/len(bold_flags) if bold_flags else 0.0
                lines.append(Line(
                    page=page_ctx.index,
                    text=raw_text,
                    x0=x0,y0=y0,x1=x1,y1=y1,
                    spans=spans,
                    font_sizes=sizes,
                    primary_font=fonts[0] if fonts else "",
                    avg_size=avg_size,
                    bold_frac=bold_frac
                ))
    lines.sort(key=lambda ln: (ln.page, ln.y0, ln.x0))
    return lines
