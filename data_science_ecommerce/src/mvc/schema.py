from pydantic import BaseModel
from typing import Optional


class Item(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str] = None


class ItemCreate(BaseModel):
    name: str
    price: float
    description: Optional[str] = None


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None