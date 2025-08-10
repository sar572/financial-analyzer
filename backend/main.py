# main.py
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from parse_pdf import extract_tables
from detect_statements import detect_pages
from normalize import normalize_statement
import tempfile
import os

app = FastAPI(title="Financial Analyzer", version="0.1")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/parse_pdf")
async def parse_pdf_endpoint(
    file: UploadFile = File(...),
    pages: str = "1-end",
    stype: str = "Unknown",
):
    """
    Upload a PDF and extract tables from `pages`.
    If `stype` is provided (e.g., 'Income Statement', 'Balance Sheet', 'Cash Flows'),
    the result is normalized to a tidy schema.
    """
    # 1) Save the upload to a temp file
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    try:
        tmp.write(await file.read())
        tmp.flush()

        # 2) Extract the table(s)
        df_raw = extract_tables(tmp.name, pages=pages)
        print(f"[parse_pdf] pages={pages} columns={list(df_raw.columns)} shape={df_raw.shape}")

        # 3) Normalize if requested
        if stype != "Unknown":
            df = normalize_statement(df_raw, stype)
            return {"columns": list(df.columns), "rows": df.to_dict(orient="records")}
        else:
            return {"columns": list(df_raw.columns), "rows": df_raw.to_dict(orient="records")}
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


@app.post("/auto_extract")
async def auto_extract_endpoint(file: UploadFile = File(...)):
    """
    Upload a PDF, auto-detect statement pages (Income, Balance Sheet, Cash Flows),
    extract tables for each, normalize, and return everything as JSON.

    This endpoint is resilient: if one statement fails to extract, it will
    include an 'error' for that statement instead of failing the whole request.
    """
    # 1) Save upload
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    try:
        tmp.write(await file.read())
        tmp.flush()
        pdf_path = tmp.name

        # 2) Detect pages per statement type
        pages_map = detect_pages(pdf_path)  # e.g. {"Income Statement":[110], "Balance Sheet":[105], "Cash Flows":[113]}
        print(f"[auto_extract] detected pages: {pages_map}")

        # 3) Extract + normalize each statement
        output = {}
        for stype, pages in pages_map.items():
            page_str = ",".join(map(str, pages))
            try:
                df_raw = extract_tables(pdf_path, pages=page_str)
                print(f"[{stype}] pages={page_str} columns={list(df_raw.columns)} shape={df_raw.shape}")

                df = normalize_statement(df_raw, stype)
                output[stype] = {
                    "columns": list(df.columns),
                    "rows": df.to_dict(orient="records"),
                    "pages": pages,
                }
            except Exception as e:
                # Do not 500 the whole request—report the specific failure
                print(f"[{stype}] extraction error on pages={page_str}: {e}")
                output[stype] = {
                    "error": str(e),
                    "pages": pages,
                }

        return JSONResponse(output)

    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
