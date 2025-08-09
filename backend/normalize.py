import re
import pandas as pd

# ---------- helpers ----------
def _to_number(x):
    if x is None: return None
    s = str(x).strip()
    if s in {"", "-", "—", "–"}: return None
    s = s.replace(",", "")
    if re.match(r"^\(.*\)$", s):  # (1,234) -> -1234
        s = "-" + s[1:-1]
    try:
        return float(s)
    except:
        return None

def _clean_text(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()

def _mostly_numeric(series: pd.Series) -> float:
    """Return fraction of cells that look numeric."""
    vals = series.dropna().astype(str)
    if len(vals) == 0: return 0.0
    ok = 0
    for v in vals:
        if _to_number(v) is not None:
            ok += 1
    return ok / len(vals)

# Canonical maps (extend over time)
INCOME_MAP = {
    "total revenues": "revenue", "sales and revenue": "revenue", "net sales": "revenue", "revenue": "revenue",
    "cost of sales": "cogs", "cost of goods sold": "cogs",
    "gross profit": "gross_profit",
    "selling, general and administrative expenses": "sga",
    "research and engineering": "rd", "research and development": "rd",
    "operating income": "operating_income",
    "interest expense": "interest_expense",
    "provision for income taxes": "income_tax_expense", "income tax": "income_tax_expense",
    "net income/(loss)": "net_income", "net income": "net_income",
}
BALANCE_MAP = {
    "cash and cash equivalents": "cash",
    "accounts receivable": "receivables", "trade receivables": "receivables",
    "inventories": "inventory",
    "total current assets": "total_current_assets",
    "property, plant and equipment": "ppe",
    "total assets": "total_assets",
    "accounts payable": "accounts_payable",
    "total current liabilities": "total_current_liabilities",
    "long-term debt": "long_term_debt",
    "total liabilities": "total_liabilities",
    "total stockholders' equity": "total_equity", "total equity": "total_equity",
}
CASHFLOWS_MAP = {
    "net cash provided by/(used in) operating activities": "cfo",
    "net cash provided by/(used in) investing activities": "cfi",
    "net cash provided by/(used in) financing activities": "cff",
    "cash, cash equivalents, and restricted cash at end of period": "cash_end",
}

def _canonical_name(raw, stype):
    r = _clean_text(raw)
    maps = {"Income Statement": INCOME_MAP, "Balance Sheet": BALANCE_MAP, "Cash Flows": CASHFLOWS_MAP}.get(stype, {})
    for k, v in sorted(maps.items(), key=lambda kv: len(kv[0]), reverse=True):
        if k in r:
            return v
    return r

def _pick_label_and_values(df: pd.DataFrame):
    cols = list(df.columns)
    if len(cols) == 0:
        return None, []

    # score columns
    year_re = re.compile(r"(19|20)\d{2}")
    scores = []
    for i, c in enumerate(cols):
        header = str(c)
        yr = bool(year_re.search(header))
        ratio = _mostly_numeric(df[c])
        scores.append({"idx": i, "col": c, "year_flag": yr, "num_ratio": ratio})

    # label = column with LOWEST numeric ratio (i.e., mostly text). Prefer no-year columns.
    label_candidates = sorted(scores, key=lambda s: (s["num_ratio"], s["year_flag"], s["idx"]))
    label_col = label_candidates[0]["col"]

    # values = columns that look like years OR mostly numeric, keep original order
    value_cols = [s["col"] for s in scores if s["col"] != label_col and (s["year_flag"] or s["num_ratio"] >= 0.5)]

    # fallback: if we still didn't get value cols, just take the rightmost up to 3 (excluding label)
    if not value_cols:
        value_cols = [c for c in cols if c != label_col][-3:]

    # cap at 3 for consistency
    value_cols = value_cols[-3:]
    return label_col, value_cols

def normalize_statement(df: pd.DataFrame, stype: str) -> pd.DataFrame:
    """Return tidy frame with ['line_item','col1','col2','col3'] and numeric values."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["line_item","col1","col2","col3"])

    label_col, value_cols = _pick_label_and_values(df)

    keep = [label_col] + value_cols
    out = df[keep].copy()

    # rename to standard column names
    new_cols = ["line_item"] + [f"col{i+1}" for i in range(len(value_cols))]
    out.columns = new_cols

    # clean labels & numbers
    out["line_item"] = out["line_item"].map(lambda s: _canonical_name(s, stype))
    for c in new_cols[1:]:
        out[c] = out[c].map(_to_number)

    # drop rows with no numeric data in the value cols
    if len(new_cols) > 1:
        out = out.dropna(how="all", subset=new_cols[1:])

    return out.reset_index(drop=True)
