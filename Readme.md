## Document Table Extraction API (FastAPI)

Prototype API to upload a table image, run OCR with `glm-ocr`, parse using an LLM, validate with Pydantic, and return structured rows in this schema:

- `Prod date`
- `Exp date`
- `Product Name`
- `Batch No.`
- `pH`

## Project Structure

```text
doc_automation/
	app/
		__init__.py
		main.py
		ocr_service.py
		schemas.py
	data/
	notebooks/
		model_testing.ipynb
	pyproject.toml
	Readme.md
```

## Requirements

1. Python 3.13+
2. Ollama installed and running
3. Models pulled locally:

```bash
ollama pull glm-ocr:q8_0
ollama pull llama3.2:1b
```

## Install Dependencies

Using `uv`:

```bash
uv sync
```

Or with `pip`:

```bash
pip install fastapi uvicorn python-multipart ollama pydantic
```

## Run API

```bash
uv run uvicorn app.main:app --reload
```

Open docs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

### `GET /health`

Health check endpoint.

Response:

```json
{
	"status": "ok"
}
```

### `POST /extract-table`

Accepts multipart form-data.

Form fields:

- `image` (required): image file
- `include_debug` (optional, default `false`): include OCR/LLM raw text in response
- `ocr_model` (optional, default `glm-ocr:q8_0`)
- `parser_model` (optional, default `llama3.2:1b`)

Example using curl:

```bash
curl -X POST "http://127.0.0.1:8000/extract-table" \
	-F "image=@data/image-13.png" \
	-F "include_debug=true"
```

Example response:

```json
{
	"rows": [
		{
			"Prod date": "04.11.23",
			"Exp date": "04.11.24",
			"Product Name": "DB2 Stabiliser",
			"Batch No.": "893",
			"pH": "7.17"
		}
	],
	"debug": {
		"raw_text": "... OCR output ...",
		"llm_text": "... parser model output ..."
	}
}
```

## Notes

- Output validation uses Pydantic models (`ProductRow`, `ProductTable`).
- If parser JSON is malformed, the service attempts lightweight repair and a fallback LLM repair prompt.
- Missing or unclear fields are returned as `null`.