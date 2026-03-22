import sqlite3
from pathlib import Path
from typing import Any


SEED_CARS: list[dict[str, Any]] = [
    {
        "id": "car-001",
        "brand": "Toyota",
        "model": "Corolla Cross",
        "year": 2024,
        "category": "SUV",
        "city": "Sao Paulo",
        "daily_rate": 249.9,
        "total_units": 6,
        "available_units": 6,
    },
    {
        "id": "car-002",
        "brand": "Volkswagen",
        "model": "T-Cross",
        "year": 2024,
        "category": "SUV",
        "city": "Campinas",
        "daily_rate": 219.9,
        "total_units": 5,
        "available_units": 5,
    },
    {
        "id": "car-003",
        "brand": "Chevrolet",
        "model": "Onix",
        "year": 2023,
        "category": "Hatch",
        "city": "Rio de Janeiro",
        "daily_rate": 149.9,
        "total_units": 8,
        "available_units": 8,
    },
    {
        "id": "car-004",
        "brand": "Jeep",
        "model": "Compass",
        "year": 2024,
        "category": "SUV",
        "city": "Belo Horizonte",
        "daily_rate": 289.9,
        "total_units": 4,
        "available_units": 4,
    },
    {
        "id": "car-005",
        "brand": "BYD",
        "model": "Dolphin",
        "year": 2025,
        "category": "Electric",
        "city": "Curitiba",
        "daily_rate": 269.9,
        "total_units": 3,
        "available_units": 3,
    },
]


class InventoryRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cars (
                    id TEXT PRIMARY KEY,
                    brand TEXT NOT NULL,
                    model TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    city TEXT NOT NULL,
                    daily_rate REAL NOT NULL,
                    total_units INTEGER NOT NULL,
                    available_units INTEGER NOT NULL
                )
                """
            )
            existing_count = connection.execute("SELECT COUNT(*) FROM cars").fetchone()[0]
            if existing_count == 0:
                connection.executemany(
                    """
                    INSERT INTO cars (
                        id, brand, model, year, category, city, daily_rate, total_units, available_units
                    ) VALUES (
                        :id, :brand, :model, :year, :category, :city, :daily_rate, :total_units, :available_units
                    )
                    """,
                    SEED_CARS,
                )
            connection.commit()

    def list_cars(self, city: str | None = None, available_only: bool = False) -> list[dict[str, Any]]:
        query = "SELECT * FROM cars"
        conditions: list[str] = []
        params: list[Any] = []

        if city:
            conditions.append("LOWER(city) = LOWER(?)")
            params.append(city)
        if available_only:
            conditions.append("available_units > 0")

        if conditions:
            query = f"{query} WHERE {' AND '.join(conditions)}"
        query = f"{query} ORDER BY daily_rate ASC"

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_car(self, car_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM cars WHERE id = ?", (car_id,)).fetchone()
        return dict(row) if row else None

    def hold_car(self, car_id: str, quantity: int = 1) -> dict[str, Any] | None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM cars WHERE id = ?", (car_id,)).fetchone()
            if row is None:
                connection.rollback()
                return None
            if row["available_units"] < quantity:
                connection.rollback()
                raise ValueError("Not enough units available to hold.")

            updated_units = row["available_units"] - quantity
            connection.execute(
                "UPDATE cars SET available_units = ? WHERE id = ?",
                (updated_units, car_id),
            )
            connection.commit()

        updated_car = self.get_car(car_id)
        assert updated_car is not None
        return updated_car

    def release_car(self, car_id: str, quantity: int = 1) -> dict[str, Any] | None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM cars WHERE id = ?", (car_id,)).fetchone()
            if row is None:
                connection.rollback()
                return None

            updated_units = min(row["available_units"] + quantity, row["total_units"])
            connection.execute(
                "UPDATE cars SET available_units = ? WHERE id = ?",
                (updated_units, car_id),
            )
            connection.commit()

        updated_car = self.get_car(car_id)
        assert updated_car is not None
        return updated_car
