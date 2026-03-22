import uuid
from datetime import datetime, timezone
from typing import Protocol

import httpx
from fastapi import HTTPException

from services.reservation_service.models import ReservationCreateRequest
from services.reservation_service.repository import ReservationRepository


class InventoryClient(Protocol):
    def get_car(self, car_id: str) -> dict:
        ...

    def hold_car(self, car_id: str, quantity: int = 1) -> None:
        ...

    def release_car(self, car_id: str, quantity: int = 1) -> None:
        ...


class HttpInventoryClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def get_car(self, car_id: str) -> dict:
        response = httpx.get(f"{self.base_url}/cars/{car_id}", timeout=10)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Carro nao encontrado no inventario.")
        response.raise_for_status()
        return response.json()

    def hold_car(self, car_id: str, quantity: int = 1) -> None:
        response = httpx.post(
            f"{self.base_url}/internal/cars/{car_id}/hold",
            json={"quantity": quantity},
            timeout=10,
        )
        if response.status_code == 409:
            raise HTTPException(status_code=409, detail="Nao ha unidades disponiveis para este carro.")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Carro nao encontrado no inventario.")
        response.raise_for_status()

    def release_car(self, car_id: str, quantity: int = 1) -> None:
        response = httpx.post(
            f"{self.base_url}/internal/cars/{car_id}/release",
            json={"quantity": quantity},
            timeout=10,
        )
        response.raise_for_status()


class ReservationService:
    def __init__(
        self,
        repository: ReservationRepository,
        inventory_client: InventoryClient,
    ) -> None:
        self.repository = repository
        self.inventory_client = inventory_client

    @staticmethod
    def calculate_rental_days(start_date, end_date) -> int:
        total_days = (end_date - start_date).days
        if total_days <= 0:
            raise HTTPException(
                status_code=422,
                detail="A data final deve ser posterior a data inicial.",
            )
        return total_days

    def create_reservation(self, payload: ReservationCreateRequest) -> dict:
        total_days = self.calculate_rental_days(payload.start_date, payload.end_date)
        car = self.inventory_client.get_car(payload.car_id)
        self.inventory_client.hold_car(payload.car_id)

        reservation = {
            "id": str(uuid.uuid4()),
            "customer_name": payload.customer_name,
            "customer_document": payload.customer_document,
            "car_id": payload.car_id,
            "car_label": f"{car['brand']} {car['model']}",
            "pickup_city": payload.pickup_city,
            "start_date": payload.start_date.isoformat(),
            "end_date": payload.end_date.isoformat(),
            "total_days": total_days,
            "total_price": round(total_days * float(car["daily_rate"]), 2),
            "status": "CONFIRMED",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.repository.create(reservation)

    def list_reservations(self) -> list[dict]:
        return self.repository.list_all()

    def cancel_reservation(self, reservation_id: str) -> dict:
        reservation = self.repository.get(reservation_id)
        if reservation is None:
            raise HTTPException(status_code=404, detail="Reserva nao encontrada.")
        if reservation["status"] == "CANCELED":
            return reservation

        self.inventory_client.release_car(reservation["car_id"])
        updated = self.repository.update_status(reservation_id, "CANCELED")
        assert updated is not None
        return updated
