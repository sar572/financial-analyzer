import camelot

PDF = "Example10K.pdf"

# Scan only pages 1–10 to speed it up; adjust if your Income Stmt is later
PAGE_RANGES = ["1-10", "11-20", "21-30"]

for pages in PAGE_RANGES:
    for flavor in ("lattice", "stream"):
        try:
            tables = camelot.read_pdf(PDF, pages=pages, flavor=flavor)
            print(f"→ {flavor!r} on pages={pages!r}: {len(tables)} table(s)")
        except Exception as e:
            print(f"‼ {flavor!r} on pages={pages!r} error: {e}")
    print("-" * 40)