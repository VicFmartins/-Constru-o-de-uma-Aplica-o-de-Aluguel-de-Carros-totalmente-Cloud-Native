import os

import httpx
from fastapi import FastAPI, HTTPException, Query


inventory_url = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8001").rstrip("/")
reservation_url = os.getenv("RESERVATION_SERVICE_URL", "http://localhost:8002").rstrip("/")

app = FastAPI(
    title="Gateway Service",
    version="1.0.0",
    description="API gateway simples para a demonstracao da plataforma cloud-native.",
)


def _unwrap_response(response: httpx.Response):
    if response.is_error:
        detail = "Erro ao comunicar com microsservico."
        try:
            payload = response.json()
            detail = payload.get("detail", detail)
        except ValueError:
            pass
        raise HTTPException(status_code=response.status_code, detail=detail)
    return response.json()


@app.get("/")
def root() -> dict[str, object]:
    return {
        "project": "car-rental-cloud-native",
        "services": {
            "inventory": f"{inventory_url}/docs",
            "reservations": f"{reservation_url}/docs",
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "gateway"}


@app.get("/catalog")
def catalog(
    city: str | None = None,
    available_only: bool = Query(default=False),
) -> list[dict]:
    response = httpx.get(
        f"{inventory_url}/cars",
        params={"city": city, "available_only": available_only},
        timeout=10,
    )
    return _unwrap_response(response)


@app.post("/reservations", status_code=201)
def create_reservation(payload: dict) -> dict:
    response = httpx.post(f"{reservation_url}/reservations", json=payload, timeout=10)
    return _unwrap_response(response)


@app.get("/reservations")
def list_reservations() -> list[dict]:
    response = httpx.get(f"{reservation_url}/reservations", timeout=10)
    return _unwrap_response(response)


@app.post("/reservations/{reservation_id}/cancel")
def cancel_reservation(reservation_id: str) -> dict:
    response = httpx.post(f"{reservation_url}/reservations/{reservation_id}/cancel", timeout=10)
    return _unwrap_response(response)


@app.get("/dashboard")
def dashboard() -> dict[str, object]:
    cars = httpx.get(f"{inventory_url}/cars", timeout=10).json()
    reservations = httpx.get(f"{reservation_url}/reservations", timeout=10).json()

    return {
        "available_cars": sum(car["available_units"] for car in cars),
        "fleet_size": sum(car["total_units"] for car in cars),
        "active_reservations": len([item for item in reservations if item["status"] == "CONFIRMED"]),
        "services": {
            "inventory": inventory_url,
            "reservations": reservation_url,
        },
    }
