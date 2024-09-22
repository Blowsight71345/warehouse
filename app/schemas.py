from pydantic import BaseModel, Field, condecimal, conint
from typing import List, Optional
from datetime import datetime
from models import OrderStatus


class ProductBase(BaseModel):
    name: str = Field(..., title="Name of the product")
    description: Optional[str] = Field(None, title="Description of the product")
    price: condecimal(gt=0) = Field(...,
                                    title="Price of the product",
                                    description="Must be a positive number")
    stock: conint(gt=0) = Field(..., title="Stock of the product",
                                description="Must be a positive integer")


class Product(ProductBase):
    id: int

    class ConfigDict:
        from_attributes = True


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int


class OrderBase(BaseModel):
    created_at: datetime
    status: OrderStatus
    items: List[OrderItemBase] = []


class Order(OrderBase):
    id: int

    class ConfigDict:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
