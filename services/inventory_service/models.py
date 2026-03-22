from pydantic import BaseModel, Field


class Car(BaseModel):
    id: str
    brand: str
    model: str
    year: int
    category: str
    city: str
    daily_rate: float
    total_units: int
    available_units: int


class InventoryMutationRequest(BaseModel):
    quantity: int = Field(default=1, ge=1, le=10)


class InventoryMutationResponse(BaseModel):
    car_id: str
    available_units: int
    message: str
