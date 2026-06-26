import json
import os
import tempfile
from typing import Tuple

from ollama import chat
from pydantic import ValidationError

from app.schemas import ProductTable


def extract_json_candidate(text: str) -> str:
    """Extract a JSON-looking substring from model output."""
    stripped = text.strip()
    if stripped.startswith("{"):
        return stripped

    start = stripped.find("{")
    if start == -1:
        return stripped

    return stripped[start:]


def repair_json_text(text: str) -> str:
    """Repair common truncated JSON issues in LLM responses."""
    candidate = extract_json_candidate(text).strip()
    if not candidate:
        return candidate

    open_curly = candidate.count("{")
    close_curly = candidate.count("}")
    if close_curly < open_curly:
        candidate += "}" * (open_curly - close_curly)

    open_square = candidate.count("[")
    close_square = candidate.count("]")
    if close_square < open_square:
        candidate += "]" * (open_square - close_square)

    return candidate


def coerce_table_with_pydantic(structured_text: str, parser_model: str) -> ProductTable:
    """Validate and coerce LLM output into strict schema using Pydantic."""
    attempts = [structured_text, repair_json_text(structured_text)]

    for attempt in attempts:
        try:
            parsed_json = json.loads(extract_json_candidate(attempt))
            return ProductTable.model_validate(parsed_json)
        except (json.JSONDecodeError, ValidationError):
            continue

    fallback_response = chat(
        model=parser_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Return ONLY valid JSON with exact schema: "
                    "{\"rows\": [{\"Prod date\": null, \"Exp date\": null, \"Product Name\": null, \"Batch No.\": null, \"pH\": null}]}. "
                    "No markdown, no explanation, no extra keys."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Fix this malformed JSON and return valid JSON only:\n\n"
                    f"{structured_text}"
                ),
            },
        ],
    )

    fixed_text = fallback_response.message.content
    parsed_fixed = json.loads(repair_json_text(fixed_text))
    return ProductTable.model_validate(parsed_fixed)


def run_ocr_and_parse(
    image_bytes: bytes,
    filename: str,
    ocr_model: str = "glm-ocr:q8_0",
    parser_model: str = "llama3.2:1b",
) -> Tuple[ProductTable, str, str]:
    suffix = os.path.splitext(filename)[1] or ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
        tmp_file.write(image_bytes)
        temp_image_path = tmp_file.name

    try:
        ocr_response = chat(
            model=ocr_model,
            messages=[
                {
                    "role": "user",
                    "content": "Extract all table text from this image exactly as it appears.",
                    "images": [temp_image_path],
                }
            ],
        )
        raw_text = ocr_response.message.content

        llm_response = chat(
            model=parser_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract structured table rows from OCR text. "
                        "Return ONLY valid JSON (no markdown, no explanation). "
                        "Use this exact schema with exact keys and same case: "
                        "{\"rows\": [{\"Prod date\": null, \"Exp date\": null, \"Product Name\": null, \"Batch No.\": null, \"pH\": null}]}. "
                        "If multiple table rows exist, include all rows. "
                        "If a field is missing or unclear, set it to null."
                    ),
                },
                {
                    "role": "user",
                    "content": f"OCR text:\n\n{raw_text}",
                },
            ],
        )
        structured_text = llm_response.message.content
        table = coerce_table_with_pydantic(structured_text, parser_model=parser_model)
        table.rows = [r for r in table.rows if r.batch_no is not None]
        return table, raw_text, structured_text
    finally:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
