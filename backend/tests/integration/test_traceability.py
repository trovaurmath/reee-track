from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_equipment(client: TestClient, token: str) -> dict[str, object]:
    authorization = headers(token)
    category = client.get(
        "/api/v1/catalogs/equipment-categories", headers=authorization
    ).json()[0]
    equipment_type = client.get(
        "/api/v1/catalogs/equipment-types", headers=authorization
    ).json()[0]
    sector = client.get("/api/v1/catalogs/sectors", headers=authorization).json()[0]
    response = client.post(
        "/api/v1/equipments",
        headers=authorization,
        json={
            "category_id": category["id"],
            "equipment_type_id": equipment_type["id"],
            "origin_sector_id": sector["id"],
            "asset_number": "TRACEABILITY-0001",
            "brand": "Marca rastreável",
            "model": "Modelo V0.4",
            "initial_condition": "Equipamento para teste do histórico operacional.",
            "collection_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        },
    )
    assert response.status_code == 201
    return response.json()


def complete_as_reusable(
    client: TestClient, token: str, equipment: dict[str, object]
) -> None:
    authorization = headers(token)
    triage = client.post(
        f"/api/v1/equipments/{equipment['tracking_code']}/triages",
        headers=authorization,
    ).json()
    criteria = client.get(
        "/api/v1/triage-config/criteria", headers=authorization
    ).json()
    saved = client.put(
        f"/api/v1/triages/{triage['id']}/answers",
        headers=authorization,
        json={
            "answers": [
                {"criterion_id": criterion["id"], "value": True}
                for criterion in criteria
                if criterion["is_required"]
            ]
        },
    )
    assert saved.status_code == 200
    reusable = next(
        item
        for item in client.get(
            "/api/v1/triage-config/classifications", headers=authorization
        ).json()
        if item["code"] == "REUTILIZAVEL"
    )
    completed = client.post(
        f"/api/v1/triages/{triage['id']}/complete",
        headers=authorization,
        json={
            "classification_id": reusable["id"],
            "technical_opinion": "Apto a seguir para reintrodução.",
        },
    )
    assert completed.status_code == 200


def test_manual_transition_note_and_global_feed(
    client: TestClient, admin_token: str
) -> None:
    authorization = headers(admin_token)
    equipment = create_equipment(client, admin_token)
    complete_as_reusable(client, admin_token, equipment)

    options = client.get(
        f"/api/v1/equipments/{equipment['id']}/workflow-options",
        headers=authorization,
    )
    assert options.status_code == 200
    assert {item["code"] for item in options.json()} == {
        "ARMAZENADO",
        "PREPARANDO_REINTRODUCAO",
        "SEPARADO_LEILAO",
    }

    invalid = client.post(
        f"/api/v1/equipments/{equipment['id']}/transitions",
        headers=authorization,
        json={
            "new_status": "RECICLADO",
            "description": "Tentativa incompatível que deve ser bloqueada.",
        },
    )
    assert invalid.status_code == 400

    transitioned = client.post(
        f"/api/v1/equipments/{equipment['id']}/transitions",
        headers=authorization,
        json={
            "new_status": "PREPARANDO_REINTRODUCAO",
            "description": "Equipamento encaminhado para preparação de reintrodução.",
            "location": "Oficina técnica",
        },
    )
    assert transitioned.status_code == 200
    assert transitioned.json()["current_status"] == "PREPARANDO_REINTRODUCAO"

    note = client.post(
        f"/api/v1/equipments/{equipment['id']}/timeline-notes",
        headers=authorization,
        json={
            "description": "Limpeza externa e conferência de acessórios concluídas.",
            "location": "Oficina técnica",
        },
    )
    assert note.status_code == 201
    assert note.json()["event_type"] == "OPERATIONAL_NOTE"

    timeline = client.get(
        f"/api/v1/equipments/{equipment['id']}/timeline",
        headers=authorization,
    ).json()
    assert [event["event_type"] for event in timeline][-2:] == [
        "STATUS_CHANGED",
        "OPERATIONAL_NOTE",
    ]

    feed = client.get(
        "/api/v1/traceability/events",
        headers=authorization,
        params={"query": equipment["tracking_code"]},
    )
    assert feed.status_code == 200
    assert feed.json()["total"] >= 8
    assert all(
        item["tracking_code"] == equipment["tracking_code"]
        for item in feed.json()["items"]
    )
    assert feed.json()["items"][0]["event_type"] == "OPERATIONAL_NOTE"
