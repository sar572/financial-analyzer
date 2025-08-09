from fastapi import FastAPI, File, UploadFile
from parse_pdf         import extract_tables
from detect_statements import detect_pages
import tempfile

app = FastAPI(title="Financial Analyzer", version="0.1")

@app.post("/parse_pdf")
async def parse_pdf_endpoint(
    file: UploadFile = File(...),
    pages: str = "1-end"
):
    """
    Upload a PDF and extract tables from specified pages.
    """
    # 1) Save upload
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(await file.read()); tmp.flush()
    # 2) Run your Camelot parser
    df = extract_tables(tmp.name, pages=pages)
    return {"table": df.to_dict(orient="records")}


@app.post("/auto_extract")
async def auto_extract_endpoint(
    file: UploadFile = File(...)
):
    """
    Upload a PDF, detect statement pages, and extract each table.
    """
    # 1) Save upload
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(await file.read()); tmp.flush()
    pdf_path = tmp.name

    # 2) Detect which pages are Income, Balance, Cash Flows, etc.
    pages_map = detect_pages(pdf_path)

    # 3) Extract each statement
    output = {}
    for stype, pages in pages_map.items():
        page_str = ",".join(map(str, pages))
        df = extract_tables(pdf_path, pages=page_str)
        output[stype] = df.to_dict(orient="records")

    return output