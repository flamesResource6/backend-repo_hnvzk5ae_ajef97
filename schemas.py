"""
Database Schemas for Blossom (Flower Store)

Each Pydantic model represents a MongoDB collection. The collection name is the lowercase
of the class name (e.g., FlowerProduct -> "flowerproduct").

These schemas are used for validation before inserting into the database.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


class FlowerProduct(BaseModel):
    name: str = Field(..., description="Flower or bouquet name")
    description: Optional[str] = Field(None, description="Short description")
    price: float = Field(..., ge=0, description="Price in USD")
    image_url: str = Field(..., description="Public image URL")
    in_stock: bool = Field(True, description="Whether item is in stock")
    tags: Optional[List[str]] = Field(default=None, description="Search tags")


class OrderItem(BaseModel):
    product_id: str = Field(..., description="ID of the product")
    name: str = Field(..., description="Product name at time of purchase")
    price: float = Field(..., ge=0)
    qty: int = Field(..., ge=1)


class CustomerInfo(BaseModel):
    name: str
    email: EmailStr
    address: Optional[str] = None
    note: Optional[str] = None


class Order(BaseModel):
    items: List[OrderItem]
    customer: CustomerInfo
    total: float = Field(..., ge=0)
    status: str = Field("pending", description="Order status")
