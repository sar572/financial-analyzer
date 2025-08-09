import sys
import camelot
import pandas as pd

def _make_cols_unique(cols):
    """Given a list of column names, append “.2”, “.3”… to duplicates."""
    counts = {}
    new_cols = []
    for col in cols:
        if col in counts:
            counts[col] += 1
            new_cols.append(f"{col}.{counts[col]}")
        else:
            counts[col] = 1
            new_cols.append(col)
    return new_cols

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
        print(f"[*] No lattice tables, trying stream …")
        tables = read("stream")
        print(f"    → stream found {len(tables)} table(s)")
    
    if not tables:
        raise ValueError(f"No tables found on pages={pages}")
    
    # Take the first table and convert to DataFrame
    df = tables[0].df

    # Promote the first row to header
    df.columns = df.iloc[0].tolist()
    df = df[1:].reset_index(drop=True)

    # Make column names unique
    df.columns = _make_cols_unique(df.columns)

    return df

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_pdf.py <PDF_PATH> [pages]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    pages    = sys.argv[2] if len(sys.argv) > 2 else "1-end"
    
    df = extract_tables(pdf_path, pages=pages)
    print(df.to_json(orient="records"))
