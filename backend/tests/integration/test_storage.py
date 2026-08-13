from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def authorization_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_equipment(client: TestClient, token: str, suffix: str) -> dict[str, object]:
    headers = authorization_header(token)
    category = client.get(
        "/api/v1/catalogs/equipment-categories", headers=headers
    ).json()[0]
    equipment_type = client.get(
        "/api/v1/catalogs/equipment-types", headers=headers
    ).json()[0]
    sector = client.get("/api/v1/catalogs/sectors", headers=headers).json()[0]
    response = client.post(
        "/api/v1/equipments",
        headers=headers,
        json={
            "category_id": category["id"],
            "equipment_type_id": equipment_type["id"],
            "origin_sector_id": sector["id"],
            "asset_number": f"PAT-{suffix}",
            "serial_number": f"SERIAL-{suffix}",
            "brand": "Marca de teste",
            "model": f"Modelo {suffix}",
            "initial_condition": "Usado, aguardando avaliação.",
            "collection_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        },
    )
    assert response.status_code == 201
    return response.json()


def create_location(
    client: TestClient, token: str, code: str, capacity: int = 1
) -> dict[str, object]:
    response = client.post(
        "/api/v1/storage/locations",
        headers=authorization_header(token),
        json={
            "code": code,
            "warehouse": "Depósito de testes",
            "aisle": "A",
            "rack": "E01",
            "shelf": "P01",
            "position": "01",
            "capacity": capacity,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_location_crud_and_capacity(client: TestClient, admin_token: str) -> None:
    headers = authorization_header(admin_token)
    location = create_location(client, admin_token, "TEST-LOC-CRUD", capacity=2)

    updated = client.patch(
        f"/api/v1/storage/locations/{location['id']}",
        headers=headers,
        json={"capacity": 3, "notes": "Posição atualizada."},
    )
    assert updated.status_code == 200
    assert updated.json()["capacity"] == 3

    listing = client.get(
        "/api/v1/storage/locations?include_inactive=true", headers=headers
    )
    assert any(item["id"] == location["id"] for item in listing.json())

    deleted = client.delete(
        f"/api/v1/storage/locations/{location['id']}", headers=headers
    )
    assert deleted.status_code == 204

    inactive = client.get(
        "/api/v1/storage/locations?include_inactive=true", headers=headers
    ).json()
    item = next(item for item in inactive if item["id"] == location["id"])
    assert item["is_active"] is False


def test_storage_entry_transfer_exit_and_timeline(
    client: TestClient, admin_token: str
) -> None:
    headers = authorization_header(admin_token)
    equipment = create_equipment(client, admin_token, "STORAGE-FLOW")
    first = create_location(client, admin_token, "TEST-LOC-A")
    second = create_location(client, admin_token, "TEST-LOC-B")

    entry = client.post(
        "/api/v1/storage/movements",
        headers=headers,
        json={"equipment_id": equipment["id"], "to_location_id": first["id"]},
    )
    assert entry.status_code == 201
    assert entry.json()["movement_type"] == "ENTRY"

    occupied_delete = client.delete(
        f"/api/v1/storage/locations/{first['id']}", headers=headers
    )
    assert occupied_delete.status_code == 409

    transfer = client.post(
        "/api/v1/storage/movements",
        headers=headers,
        json={"equipment_id": equipment["id"], "to_location_id": second["id"]},
    )
    assert transfer.status_code == 201
    assert transfer.json()["movement_type"] == "TRANSFER"

    occupancies = client.get("/api/v1/storage/occupancies", headers=headers)
    assert occupancies.status_code == 200
    assignment = next(
        item for item in occupancies.json() if item["equipment_id"] == equipment["id"]
    )
    assert assignment["location"]["code"] == "TEST-LOC-B"

    exit_response = client.post(
        "/api/v1/storage/movements",
        headers=headers,
        json={"equipment_id": equipment["id"], "to_location_id": None},
    )
    assert exit_response.status_code == 201
    assert exit_response.json()["movement_type"] == "EXIT"

    timeline = client.get(
        f"/api/v1/equipments/{equipment['id']}/timeline", headers=headers
    ).json()
    assert [item["event_type"] for item in timeline[-3:]] == [
        "STORAGE_ENTRY",
        "STORAGE_TRANSFER",
        "STORAGE_EXIT",
    ]


def test_equipment_safe_delete_preserves_timeline(
    client: TestClient, admin_token: str
) -> None:
    headers = authorization_header(admin_token)
    equipment = create_equipment(client, admin_token, "SAFE-DELETE")
    response = client.request(
        "DELETE",
        f"/api/v1/equipments/{equipment['id']}",
        headers=headers,
        json={"reason": "Registro duplicado criado para teste."},
    )
    assert response.status_code == 200
    assert response.json()["is_archived"] is True

    active = client.get(
        "/api/v1/equipments?query=SAFE-DELETE", headers=headers
    ).json()
    assert active["total"] == 0

    archived = client.get(
        "/api/v1/equipments?query=SAFE-DELETE&include_archived=true", headers=headers
    ).json()
    assert archived["total"] == 1

    timeline = client.get(
        f"/api/v1/equipments/{equipment['id']}/timeline", headers=headers
    )
    assert timeline.status_code == 200
    assert timeline.json()[-1]["event_type"] == "EQUIPMENT_ARCHIVED"
