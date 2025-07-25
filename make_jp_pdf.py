# make_jp_pdf.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# Register built-in CID fonts that ship with ReportLab
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))  # sans
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))     # serif

H1 = "HeiseiKakuGo-W5"
H2 = "HeiseiKakuGo-W5"
BODY = "HeiseiMin-W3"

def page(c, h1=None, h2_list=None):
    if h1:
        c.setFont(H1, 24)
        c.drawString(72, 780, h1)
    if h2_list:
        c.setFont(H2, 16)
        y = 742
        for s in h2_list:
            c.drawString(72, y, s)
            y -= 26
    c.setFont(BODY, 12)
    c.drawString(72, 700, "本文テキスト…これは本文サンプルです。")
    c.showPage()

c = canvas.Canvas("jp_small.pdf", pagesize=A4)
page(c, "第1章 緒論", ["1.1 背景"])
page(c, "第2章 手法")
page(c, "第3章 まとめ")
c.save()
print("Wrote jp_small.pdf")