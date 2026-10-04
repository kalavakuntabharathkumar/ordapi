from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    price: float = Field(gt=0)
    quantity: int = Field(ge=0)
class ProductPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    price: float | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, ge=0)
class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; sku: str; name: str; price: float; quantity: int
class OrderLine(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=160)
    items: list[OrderLine] = Field(min_length=1)
class OrderStatusPatch(BaseModel):
    status: str
class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; customer_name: str; status: str; total: float; created_at: datetime
