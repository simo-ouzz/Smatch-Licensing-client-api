from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProductCreateRequest(BaseModel):
    product_name: str = Field(..., max_length=150)
    product_code: str = Field(..., max_length=100)


class ProductCreateResponse(BaseModel):
    product_id: int
    product_name: str
    product_code: str
    creation_date: datetime


class ProductListItem(BaseModel):
    product_id: int
    product_name: str
    product_code: str
    creation_date: datetime


class ProductDetailsResponse(BaseModel):
    product_id: int
    product_name: str
    product_code: str
    creation_date: datetime


class ProductUpdateRequest(BaseModel):
    product_name: str = Field(..., max_length=150)


class ProductDeleteResponse(BaseModel):
    success: bool
    reason: Optional[str] = None


