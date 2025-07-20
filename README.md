# PDF Outline Extractor (Round 1A)

## Status
Step 1: Environment + container scaffold complete.

## Quick Start (current stage)
Build:
  docker build --platform=linux/amd64 -t pdf1a:dev .
Run (empty processing):
  mkdir input output
  docker run --rm -v "C:\Users\Munnu\pdf-outline-1A/input:/app/input" -v "C:\Users\Munnu\pdf-outline-1A/output:/app/output" --network none pdf1a:dev

## Next Steps
Add parsing & line assembly logic (Step 2).

## Final Usage (Submission Mode)

Place PDFs (≤50 pages each) into input/ then run:
'''bash
make run
