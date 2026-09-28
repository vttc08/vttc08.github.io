"""Subset fonts, clean, and remove identifying metadata from a PDF.
```bash
uv add --dependency dev pymupdf
uv run python compress_resume.py input.pdf output.pdf
```
"""

import argparse
from pathlib import Path
import pymupdf


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compress a PDF by subsetting fonts and clearing document metadata."
    )
    parser.add_argument("input_pdf", type=Path)
    parser.add_argument("output_pdf", type=Path)
    args = parser.parse_args()

    if args.input_pdf.resolve() == args.output_pdf.resolve():
        parser.error("Choose a different output path so the original stays unchanged.")

    with pymupdf.open(args.input_pdf) as document:
        document.subset_fonts()
        document.set_metadata({
            "title": "",
            "author": "",
            "subject": "",
            "keywords": "",
            "creator": "",
            "producer": "",
            "creationDate": "",
            "modDate": "",
        })
        document.del_xml_metadata()
        document.save(args.output_pdf, garbage=4, deflate=True, clean=True)

    before = args.input_pdf.stat().st_size
    after = args.output_pdf.stat().st_size
    print(f"Wrote {args.output_pdf} ({before:,} -> {after:,} bytes)")


if __name__ == "__main__":
    main()
