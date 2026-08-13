from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def authorization_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def get_catalog_ids(client: TestClient, token: str) -> dict[str, str]:
    headers = authorization_header(token)
    category = client.get("/api/v1/catalogs/equipment-categories", headers=headers).json()[0]
    equipment_type = client.get("/api/v1/catalogs/equipment-types", headers=headers).json()[0]
    sector = client.get("/api/v1/catalogs/sectors", headers=headers).json()[0]
    return {
        "category_id": category["id"],
        "equipment_type_id": equipment_type["id"],
        "origin_sector_id": sector["id"],
    }


def equipment_payload(client: TestClient, token: str, suffix: str) -> dict[str, object]:
    return {
        **get_catalog_ids(client, token),
        "asset_number": f"PAT-{suffix}",
        "serial_number": f"SERIAL-{suffix}",
        "brand": "Marca de teste",
        "model": f"Modelo {suffix}",
        "description": "Equipamento usado em teste automatizado.",
        "initial_condition": "Usado, aguardando avaliação.",
        "collection_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        "collection_notes": "Recolhimento fictício.",
    }


def test_registration_generates_sequential_code_and_timeline(
    client: TestClient,
    admin_token: str,
) -> None:
    headers = authorization_header(admin_token)
    first = client.post(
        "/api/v1/equipments",
        headers=headers,
        json=equipment_payload(client, admin_token, "SEQ-A"),
    )
    second = client.post(
        "/api/v1/equipments",
        headers=headers,
        json=equipment_payload(client, admin_token, "SEQ-B"),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    first_code = first.json()["tracking_code"]
    second_code = second.json()["tracking_code"]
    assert first_code.startswith(f"REEE-{datetime.now(UTC).year}-")
    assert int(second_code.rsplit("-", 1)[1]) == int(first_code.rsplit("-", 1)[1]) + 1

    timeline = client.get(
        f"/api/v1/equipments/{first.json()['id']}/timeline",
        headers=headers,
    )
    assert timeline.status_code == 200
    assert [event["event_type"] for event in timeline.json()] == [
        "COLLECTED",
        "EQUIPMENT_REGISTERED",
        "QUEUED_FOR_TRIAGE",
    ]


def test_duplicate_asset_number_is_rejected(client: TestClient, admin_token: str) -> None:
    headers = authorization_header(admin_token)
    payload = equipment_payload(client, admin_token, "DUPLICATE")
    assert client.post("/api/v1/equipments", headers=headers, json=payload).status_code == 201

    duplicate = client.post("/api/v1/equipments", headers=headers, json=payload)

    assert duplicate.status_code == 409
    assert duplicate.json()["error"] == "conflict"


def test_search_qr_code_and_label(client: TestClient, admin_token: str) -> None:
    headers = authorization_header(admin_token)
    created = client.post(
        "/api/v1/equipments",
        headers=headers,
        json=equipment_payload(client, admin_token, "VISUAL"),
    ).json()

    search = client.get("/api/v1/equipments?query=VISUAL", headers=headers)
    assert search.status_code == 200
    assert search.json()["total"] == 1
    assert search.json()["items"][0]["id"] == created["id"]

    qr_code = client.get(f"/api/v1/equipments/{created['id']}/qr-code", headers=headers)
    assert qr_code.status_code == 200
    assert qr_code.headers["content-type"] == "image/png"
    assert qr_code.content.startswith(b"\x89PNG")

    label = client.get(f"/api/v1/equipments/{created['id']}/label", headers=headers)
    assert label.status_code == 200
    assert label.headers["content-type"] == "application/pdf"
    assert label.content.startswith(b"%PDF")


def test_auditor_can_read_but_cannot_register_equipment(
    client: TestClient,
    admin_token: str,
) -> None:
    headers = authorization_header(admin_token)
    created_user = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "username": "equipment-auditor",
            "email": "equipment-auditor@example.com",
            "full_name": "Auditor de equipamentos",
            "password": "equipment-auditor-password",
            "role_codes": ["AUDITOR"],
        },
    )
    assert created_user.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "equipment-auditor", "password": "equipment-auditor-password"},
    )
    auditor_headers = authorization_header(login.json()["access_token"])

    assert client.get("/api/v1/equipments", headers=auditor_headers).status_code == 200
    forbidden = client.post(
        "/api/v1/equipments",
        headers=auditor_headers,
        json=equipment_payload(client, admin_token, "AUDITOR"),
    )
    assert forbidden.status_code == 403

