from datetime import date
from pathlib import Path

from services.reservation_service.models import ReservationCreateRequest
from services.reservation_service.repository import ReservationRepository
from services.reservation_service.service import ReservationService


class FakeInventoryClient:
    def __init__(self) -> None:
        self.holds = 0
        self.releases = 0

    def get_car(self, car_id: str) -> dict:
        return {
            "id": car_id,
            "brand": "Toyota",
            "model": "Corolla Cross",
            "daily_rate": 249.9,
        }

    def hold_car(self, car_id: str, quantity: int = 1) -> None:
        self.holds += quantity

    def release_car(self, car_id: str, quantity: int = 1) -> None:
        self.releases += quantity


def build_service(tmp_path: Path) -> tuple[ReservationService, FakeInventoryClient]:
    repository = ReservationRepository(str(tmp_path / "reservations.db"))
    repository.initialize()
    client = FakeInventoryClient()
    return ReservationService(repository=repository, inventory_client=client), client


def test_create_reservation_persists_and_holds_car(tmp_path: Path) -> None:
    service, client = build_service(tmp_path)
    payload = ReservationCreateRequest(
        customer_name="Maria Souza",
        customer_document="12345678900",
        car_id="car-001",
        pickup_city="Sao Paulo",
        start_date=date(2030, 5, 10),
        end_date=date(2030, 5, 13),
    )

    reservation = service.create_reservation(payload)

    assert reservation["status"] == "CONFIRMED"
    assert reservation["total_days"] == 3
    assert reservation["total_price"] == 749.7
    assert client.holds == 1


def test_cancel_reservation_releases_car(tmp_path: Path) -> None:
    service, client = build_service(tmp_path)
    payload = ReservationCreateRequest(
        customer_name="Joao Lima",
        customer_document="98765432100",
        car_id="car-002",
        pickup_city="Campinas",
        start_date=date(2030, 7, 1),
        end_date=date(2030, 7, 4),
    )

    created = service.create_reservation(payload)
    canceled = service.cancel_reservation(created["id"])

    assert canceled["status"] == "CANCELED"
    assert client.holds == 1
    assert client.releases == 1
