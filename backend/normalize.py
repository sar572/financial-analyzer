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

def _clean_text(s):  # normalize spacing/case for matching
    return re.sub(r"\s+", " ", str(s)).strip().lower()

# Canonical maps (extend these over time)
INCOME_MAP = {
    "total revenues": "revenue", "sales and revenue": "revenue", "net sales": "revenue", "revenue": "revenue",
    "cost of sales": "cogs", "cost of goods sold": "cogs",
    "gross profit": "gross_profit",
    "selling, general and administrative expenses": "sga",
    "research and engineering": "rd", "research and development": "rd",
    "operating income": "operating_income",
    "interest expense": "interest_expense",
    "provision for income taxes": "income_tax_expense", "income tax": "income_tax_expense",
    "net income": "net_income", "net income/(loss)": "net_income",
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
    maps = {
        "Income Statement": INCOME_MAP,
        "Balance Sheet": BALANCE_MAP,
        "Cash Flows": CASHFLOWS_MAP
    }.get(stype, {})
    # longest key first -> best match
    for k, v in sorted(maps.items(), key=lambda kv: len(kv[0]), reverse=True):
        if k in r:
            return v
    return r  # fallback to cleaned original

def normalize_statement(df: pd.DataFrame, stype: str) -> pd.DataFrame:
    """
    Input: raw Camelot df (already has headers in df.columns).
    Output: tidy frame with ['line_item','col1','col2','col3'] and numeric values.
    """
    cols = list(df.columns)

    # choose 3 rightmost "value" columns (usually years). If fewer exist, take last columns.
    value_cols = [c for c in cols if any(ch.isdigit() for ch in str(c))][-3:] or cols[-3:]
    label_col = [c for c in cols if c not in value_cols][0]

    out = df[[label_col] + value_cols].copy()
    out.columns = ["line_item", "col1", "col2", "col3"][:len(out.columns)]

    # clean labels + numbers
    out["line_item"] = out["line_item"].map(lambda s: _canonical_name(s, stype))
    for c in ["col1","col2","col3"]:
        if c in out.columns:
            out[c] = out[c].map(_to_number)

    # drop rows with no numeric data
    if {"col1","col2","col3"} & set(out.columns):
        keep_cols = [c for c in ["col1","col2","col3"] if c in out.columns]
        out = out.dropna(how="all", subset=keep_cols)

    return out.reset_index(drop=True)