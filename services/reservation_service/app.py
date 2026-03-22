import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from services.reservation_service.models import (
    ReservationCancelResponse,
    ReservationCreateRequest,
    ReservationRecord,
)
from services.reservation_service.repository import ReservationRepository
from services.reservation_service.service import HttpInventoryClient, ReservationService


repository = ReservationRepository(
    os.getenv("RESERVATION_DB_PATH", "services/reservation_service/data/reservations.db")
)
service = ReservationService(
    repository=repository,
    inventory_client=HttpInventoryClient(
        os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8001")
    ),
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    repository.initialize()
    yield


app = FastAPI(
    title="Reservation Service",
    version="1.0.0",
    description="Microsservico responsavel pela criacao e cancelamento das reservas.",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "reservations"}


@app.get("/reservations", response_model=list[ReservationRecord])
def list_reservations() -> list[ReservationRecord]:
    return [ReservationRecord(**item) for item in service.list_reservations()]


@app.post("/reservations", response_model=ReservationRecord, status_code=201)
def create_reservation(payload: ReservationCreateRequest) -> ReservationRecord:
    return ReservationRecord(**service.create_reservation(payload))


@app.post("/reservations/{reservation_id}/cancel", response_model=ReservationCancelResponse)
def cancel_reservation(reservation_id: str) -> ReservationCancelResponse:
    reservation = service.cancel_reservation(reservation_id)
    return ReservationCancelResponse(
        reservation_id=reservation_id,
        status=reservation["status"],
        message="Reserva cancelada com sucesso.",
    )
