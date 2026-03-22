import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query

from services.inventory_service.models import Car, InventoryMutationRequest, InventoryMutationResponse
from services.inventory_service.repository import InventoryRepository


repository = InventoryRepository(
    os.getenv("INVENTORY_DB_PATH", "services/inventory_service/data/inventory.db")
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    repository.initialize()
    yield


app = FastAPI(
    title="Inventory Service",
    version="1.0.0",
    description="Microsservico responsavel pelo catalogo e disponibilidade dos carros.",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "inventory"}


@app.get("/cars", response_model=list[Car])
def list_cars(
    city: str | None = None,
    available_only: bool = Query(default=False),
) -> list[Car]:
    return [Car(**car) for car in repository.list_cars(city=city, available_only=available_only)]


@app.get("/cars/{car_id}", response_model=Car)
def get_car(car_id: str) -> Car:
    car = repository.get_car(car_id)
    if car is None:
        raise HTTPException(status_code=404, detail="Carro nao encontrado.")
    return Car(**car)


@app.post("/internal/cars/{car_id}/hold", response_model=InventoryMutationResponse)
def hold_car(car_id: str, payload: InventoryMutationRequest) -> InventoryMutationResponse:
    try:
        car = repository.hold_car(car_id, quantity=payload.quantity)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    if car is None:
        raise HTTPException(status_code=404, detail="Carro nao encontrado.")

    return InventoryMutationResponse(
        car_id=car_id,
        available_units=car["available_units"],
        message="Unidade reservada no inventario.",
    )


@app.post("/internal/cars/{car_id}/release", response_model=InventoryMutationResponse)
def release_car(car_id: str, payload: InventoryMutationRequest) -> InventoryMutationResponse:
    car = repository.release_car(car_id, quantity=payload.quantity)
    if car is None:
        raise HTTPException(status_code=404, detail="Carro nao encontrado.")

    return InventoryMutationResponse(
        car_id=car_id,
        available_units=car["available_units"],
        message="Unidade devolvida ao inventario.",
    )
