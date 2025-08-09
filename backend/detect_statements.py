import pdfplumber
import re
from collections import defaultdict

# Look for these phrases (case‐insensitive) to tag pages
STATEMENT_PATTERNS = {
    "Income Statement": re.compile(r"Consolidated\s+Statements? of (Operations|Income)", re.I),
    "Balance Sheet":   re.compile(r"Consolidated\s+Balance Sheets?", re.I),
    "Cash Flows":      re.compile(r"Consolidated\s+Statements? of Cash Flows", re.I),
}

def detect_pages(pdf_path):
    result = defaultdict(list)
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            for stype, pat in STATEMENT_PATTERNS.items():
                if pat.search(text):
                    result[stype].append(i)
    return result