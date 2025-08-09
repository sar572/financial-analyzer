import sys
import camelot
import pandas as pd

def _make_cols_unique(cols):
    counts = {}
    out = []
    for c in cols:
        counts[c] = counts.get(c, 0) + 1
        out.append(c if counts[c] == 1 else f"{c}.{counts[c]}")
    return out

def extract_tables(pdf_path, pages="1-end", table_areas=None):
    def read(flavor):
        return camelot.read_pdf(
            pdf_path,
            pages=pages,
            flavor=flavor,
            table_areas=table_areas if table_areas else None
        )

    print(f"[*] Trying lattice on pages={pages} …")
    tables = read("lattice")
    print(f"    → lattice found {len(tables)} table(s)")
    if not tables:
        print("[*] No lattice tables, trying stream …")
        tables = read("stream")
        print(f"    → stream found {len(tables)} table(s)")
    if not tables:
        raise ValueError(f"No tables found on pages={pages}")

    df = tables[0].df
    df.columns = _make_cols_unique(df.iloc[0].tolist())
    df = df[1:].reset_index(drop=True)
    return df

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_pdf.py <PDF_PATH> [pages]")
        sys.exit(1)
    pdf_path = sys.argv[1]
    pages = sys.argv[2] if len(sys.argv) > 2 else "1-end"
    df = extract_tables(pdf_path, pages=pages)
    print(df.to_json(orient="records"))
