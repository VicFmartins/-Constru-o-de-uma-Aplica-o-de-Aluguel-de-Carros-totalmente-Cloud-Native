from pathlib import Path

from services.inventory_service.repository import InventoryRepository


def test_hold_and_release_car_updates_availability(tmp_path: Path) -> None:
    repository = InventoryRepository(str(tmp_path / "inventory.db"))
    repository.initialize()

    original = repository.get_car("car-001")
    assert original is not None

    held = repository.hold_car("car-001")
    assert held is not None
    assert held["available_units"] == original["available_units"] - 1

    released = repository.release_car("car-001")
    assert released is not None
    assert released["available_units"] == original["available_units"]


def test_hold_car_raises_when_inventory_is_empty(tmp_path: Path) -> None:
    repository = InventoryRepository(str(tmp_path / "inventory.db"))
    repository.initialize()

    car = repository.get_car("car-005")
    assert car is not None

    for _ in range(car["total_units"]):
        repository.hold_car("car-005")

    try:
        repository.hold_car("car-005")
    except ValueError as error:
        assert "Not enough units" in str(error)
    else:
        raise AssertionError("Expected hold_car to raise ValueError when stock is empty.")
