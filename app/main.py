from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.ocr_service import run_ocr_and_parse
from app.schemas import ExtractTableResponse, OCRDebugData

app = FastAPI(
    title="Document Table Extraction API",
    version="0.1.0",
    description=(
        "Upload an image, run OCR with glm-ocr, and parse table rows into the "
        "schema: Prod date, Exp date, Product Name, Batch No., pH."
    ),
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/extract-table", response_model=ExtractTableResponse)
async def extract_table(
    image: UploadFile = File(..., description="Image file containing the target table"),
    include_debug: bool = Form(default=False),
    # ocr_model: str = Form(default="glm-ocr:q8_0"),
    ocr_model: str = Form(default="deepseek-ocr:3b"),
    parser_model: str = Form(default="llama3.2:1b"),
) -> ExtractTableResponse:
    content_type = image.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    try:
        table, raw_text, llm_text = run_ocr_and_parse(
            image_bytes=image_bytes,
            filename=image.filename or "upload.png",
            ocr_model=ocr_model,
            parser_model=parser_model,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to extract table: {exc}") from exc

    response = ExtractTableResponse(rows=table.rows)
    if include_debug:
        response.debug = OCRDebugData(raw_text=raw_text, llm_text=llm_text)

    return response
