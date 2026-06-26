from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    prod_date: Optional[str] = Field(default=None, alias="Prod date")
    exp_date: Optional[str] = Field(default=None, alias="Exp date")
    product_name: Optional[str] = Field(default=None, alias="Product Name")
    batch_no: Optional[str] = Field(default=None, alias="Batch No.")
    ph: Optional[str] = Field(default=None, alias="pH")

    def to_schema_dict(self) -> dict:
        dumped = self.model_dump(by_alias=True)
        return {
            "Prod date": dumped.get("Prod date"),
            "Exp date": dumped.get("Exp date"),
            "Product Name": dumped.get("Product Name"),
            "Batch No.": dumped.get("Batch No."),
            "pH": dumped.get("pH"),
        }


class ProductTable(BaseModel):
    model_config = ConfigDict(extra="ignore")
    rows: List[ProductRow]


class OCRDebugData(BaseModel):
    raw_text: str
    llm_text: str


class ExtractTableResponse(BaseModel):
    rows: List[ProductRow]
    debug: Optional[OCRDebugData] = None
