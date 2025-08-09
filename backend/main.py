from fastapi import FastAPI, File, UploadFile
from parse_pdf import extract_tables
from detect_statements import detect_pages
from normalize import normalize_statement
import tempfile

app = FastAPI(title="Financial Analyzer", version="0.1")

@app.post("/parse_pdf")
async def parse_pdf_endpoint(
    file: UploadFile = File(...),
    pages: str = "1-end",
    stype: str = "Unknown"
):
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(await file.read()); tmp.flush()
    df = extract_tables(tmp.name, pages=pages)
    if stype != "Unknown":
        df = normalize_statement(df, stype)
    return {"columns": list(df.columns), "rows": df.to_dict(orient="records")}

@app.post("/auto_extract")
async def auto_extract_endpoint(file: UploadFile = File(...)):
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(await file.read()); tmp.flush()
    pdf_path = tmp.name

    pages_map = detect_pages(pdf_path)
    output = {}
    for stype, pages in pages_map.items():
        page_str = ",".join(map(str, pages))
        df_raw = extract_tables(pdf_path, pages=page_str)
        df = normalize_statement(df_raw, stype)
        output[stype] = {"columns": list(df.columns), "rows": df.to_dict(orient="records")}
    return output
