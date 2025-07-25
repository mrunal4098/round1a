# PDF Outline Extractor (Round 1A)

Extract H1/H2 (and deeper) headings from PDFs (≤50 pages) using pure layout/text heuristics.  
Multilingual tweaks (Arabic, Japanese, Devanagari), TOC/caption filtering, running-header removal.

---

## 1. Quick Start

```bash
# Build (Windows Git Bash paths shown)
docker build --platform=linux/amd64 -t pdf1a:dev .

# Put PDFs in ./input, then:
make run          # writes JSONs to ./output
make eval         # prints precision/recall/F1 vs ground_truth
make perf         # synthetic 50-page timing benchmark

Folders:

input/          # your PDFs
output/         # JSON results
ground_truth/   # provided GT for eval
app/            # source


⸻

2. Make Targets (Windows-safe)

Target	What it does
make build	Build docker image pdf1a:dev
make run	Process every *.pdf in input/ → output/*.json
make eval	Compare output/*.json with ground_truth/*.json, print P/R/F1
make perf	Run 50-page synthetic benchmark and print timing JSON
make run_debug	Same as run but sets DEBUG=1 → adds _debug_* keys to each output JSON
make shell	Interactive bash in the container (for ad-hoc debugging)

All targets already set MSYS_NO_PATHCONV=1 for Git Bash.

⸻

3. Performance (Req: ≤10 s for 50 pages)

Measured 2025-07-24 on Windows 11 + Docker Desktop:

TIMEFORMAT="ELAPSED:%R  USER:%U  SYS:%S" && time make perf

Tool JSON:

{
  "timings_sec": {
    "parse": 0.242,
    "line_build": 0.007,
    "feature": 0.032,
    "candidate_filter": 0.000,
    "level_assign": 0.000,
    "total": 0.281
  },
  "page_count": 50,
  "candidates": 51,
  "assigned": 51
}

Shell wall clock: ELAPSED: 2.439 s

✅ Pass: ~0.28 s inner time (~5.6 ms/page), well under 10 s.

⸻

4. Approach

4.1 Parsing / Line Assembly
	•	PyMuPDF (fitz) → page.get_text("dict") preserves block/line/span.
	•	Collapse spans → Line objects (text, bbox, avg font size, bold fraction, page).

4.2 Features (app/features.py)

Per line:
	•	Relative font size vs median body font.
	•	Bold fraction.
	•	Numbering regexes (1., 1.2.3, Roman, Appendix A, 第1章, الفصل 1, अध्याय 1).
	•	Script ratios + dominant script (Latin / Arabic / CJK / Devanagari).
	•	Gap above (vertical whitespace).
	•	Repetition count (running headers).
	•	Caption / TOC hints (Figure, Table, dot leaders).
	•	Casing checks for Latin.

4.3 Candidate Filtering

Positive: large font, bold & short, or numbered.
Negative: repeated headers, captions, dot leaders, “page …”, multi-sentence Latin paragraphs, long body-like lines.

Multilingual rescues: if script is non-Latin, ignore casing; treat Arabic presentation forms as Arabic; keep numbered Arabic/CJK lines even if font is normal.

4.4 Level Assignment (app/level_assign.py)
	1.	Merge obvious two-line headings (tiny gap, same font).
	2.	TITLE = max rel-font on page 1 (fallback: global).
	3.	Numbered depth → H1/H2/H3.
	4.	Cluster remaining font tiers (largest→H1, next→H2, …).
	5.	Context promotions (no H3 before H2, etc.).
	6.	Deduplicate identical (level,text,page).

4.5 Output

{ "title": "...",
  "outline":[ {"level":"H1","text":"...","page":3}, ... ]
}

With DEBUG=1, extra keys: _debug_candidates, _debug_first_lines, etc.

⸻

5. Multilingual Handling
	•	Arabic: normalize RTL, match Arabic/Latin digits, ignore casing, allow normal-sized numbered headings, rescue unknown-script lines containing Arabic glyphs.
	•	Japanese: detect 第N章, support fullwidth dots \uFF0E in numeric depths.
	•	Devanagari (Hindi): allow same non-Latin relaxations.
	•	Roman numerals / Appendix letters for Western docs.

⸻

6. Edge Cases & Mitigations

Edge case	Mitigation
Running headers/footers	Repetition count + fraction threshold
Captions / TOC dot leaders	Prefix filters + ...... leader rejection
Large-font body paragraph	Latin multi-sentence, non-numbered, non-bold filtered hard
Multi-column layouts	Not fully handled (y-order only)
Mixed fonts / noisy OCR	Font tier clustering + context promotions, but still fragile


⸻

7. Dependencies / License
	•	Python 3.11 (in container)
	•	PyMuPDF (MuPDF) – AGPL. If you distribute binaries / run as a service, comply (publish source or get commercial license). Private/internal use is fine; just document.

See requirements.txt for the full list.

⸻

8. Debugging Tips

make run_debug
# Inspect
jq '."_debug_candidates"' output/F_ar.json

If jq missing on host:

docker run --rm \
  -v "$(pwd)/output:/app/output" \
  --entrypoint python pdf1a:dev - <<'PY'
import json,sys
d=json.load(open("/app/output/F_ar.json",encoding="utf-8"))
print(json.dumps(d.get("_debug_candidates",[]),ensure_ascii=False,indent=2))
PY


⸻

9. Compliance Checklist (Round 1A)

Item	Status / Evidence
Runtime ≤10 s / 50 pages	✅ 0.28 s inside app (Sec. 3)
README with approach & instructions	✅ Sections 1–5
Scoring script & reported metrics	✅ make eval prints P/R/F1; results below
Multilingual bonus	✅ Arabic + Japanese + Devanagari heuristics
Edge-case handling	⚠️ Basic ones done; multi-column etc. noted (Sec. 6)
License considerations	⚠️ AGPL note in Sec. 7


⸻

10. Future Work
	•	Multi-column segmentation (x-buckets).
	•	Better script detection (ML model) to drop ad-hoc rescues.
	•	Explicit TOC-page detection to skip entire TOC.
	•	Extend to more scripts (Cyrillic, Thai…).

⸻

11. Evaluation (2025-07-24)

FILE: A
  STRICT : P=0.8571 R=1.0 F1=0.9231 (TP=6 FP=1 FN=0)
  LENIENT: P=0.8571 R=1.0 F1=0.9231 (TP=6 FP=1 FN=0)
FILE: B
  STRICT : P=1.0 R=1.0 F1=1.0 (TP=5 FP=0 FN=0)
FILE: C
  STRICT : P=1.0 R=1.0 F1=1.0 (TP=4 FP=0 FN=0)
FILE: D
  STRICT : P=1.0 R=1.0 F1=1.0 (TP=4 FP=0 FN=0)
FILE: E_real
  STRICT : P=1.0 R=0.6667 F1=0.8 (TP=2 FP=0 FN=1)
FILE: F_ar
  STRICT : P=1.0 R=0.0 F1=0.0 (TP=0 FP=0 FN=3)
FILE: G_hi
  STRICT : P=1.0 R=1.0 F1=1.0 (TP=3 FP=0 FN=0)
FILE: sample
  STRICT : P=1.0 R=1.0 F1=1.0 (TP=3 FP=0 FN=0)

AGGREGATE STRICT : P=0.9643 R=0.8710 F1=0.9153 (TP=27 FP=1 FN=4)
AGGREGATE LENIENT: P=0.9643 R=0.8710 F1=0.9153 (TP=27 FP=1 FN=4)

(See output/*.json vs ground_truth/*.json for diffs.)

⸻

Happy extracting! 🎯

---