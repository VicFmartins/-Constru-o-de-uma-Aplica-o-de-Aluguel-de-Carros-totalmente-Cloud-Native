import sqlite3
from pathlib import Path
from typing import Any


class ReservationRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reservations (
                    id TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    customer_document TEXT NOT NULL,
                    car_id TEXT NOT NULL,
                    car_label TEXT NOT NULL,
                    pickup_city TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    total_days INTEGER NOT NULL,
                    total_price REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def create(self, reservation: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO reservations (
                    id, customer_name, customer_document, car_id, car_label, pickup_city,
                    start_date, end_date, total_days, total_price, status, created_at
                ) VALUES (
                    :id, :customer_name, :customer_document, :car_id, :car_label, :pickup_city,
                    :start_date, :end_date, :total_days, :total_price, :status, :created_at
                )
                """,
                reservation,
            )
            connection.commit()
        return reservation

    def list_all(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM reservations ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, reservation_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM reservations WHERE id = ?",
                (reservation_id,),
            ).fetchone()
        return dict(row) if row else None

    def update_status(self, reservation_id: str, status: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE reservations SET status = ? WHERE id = ?",
                (status, reservation_id),
            )
            connection.commit()
        return self.get(reservation_id)
