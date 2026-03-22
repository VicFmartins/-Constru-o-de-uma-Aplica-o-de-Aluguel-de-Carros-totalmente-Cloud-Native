from datetime import date, datetime

from pydantic import BaseModel, Field


class ReservationCreateRequest(BaseModel):
    customer_name: str = Field(min_length=3, max_length=120)
    customer_document: str = Field(min_length=11, max_length=20)
    car_id: str
    pickup_city: str = Field(min_length=2, max_length=80)
    start_date: date
    end_date: date


class ReservationRecord(BaseModel):
    id: str
    customer_name: str
    customer_document: str
    car_id: str
    car_label: str
    pickup_city: str
    start_date: date
    end_date: date
    total_days: int
    total_price: float
    status: str
    created_at: datetime


class ReservationCancelResponse(BaseModel):
    reservation_id: str
    status: str
    message: str
