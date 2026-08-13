from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def authorization_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_equipment(client: TestClient, token: str, suffix: str) -> dict[str, object]:
    headers = authorization_header(token)
    category = client.get("/api/v1/catalogs/equipment-categories", headers=headers).json()[0]
    equipment_type = client.get("/api/v1/catalogs/equipment-types", headers=headers).json()[0]
    sector = client.get("/api/v1/catalogs/sectors", headers=headers).json()[0]
    response = client.post(
        "/api/v1/equipments",
        headers=headers,
        json={
            "category_id": category["id"],
            "equipment_type_id": equipment_type["id"],
            "origin_sector_id": sector["id"],
            "asset_number": f"TRIAGE-{suffix}",
            "serial_number": f"TRIAGE-SERIAL-{suffix}",
            "brand": "Marca de triagem",
            "model": f"Modelo {suffix}",
            "initial_condition": "Equipamento usado para teste de triagem.",
            "collection_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        },
    )
    assert response.status_code == 201
    return response.json()


def boolean_answers(client: TestClient, token: str) -> list[dict[str, object]]:
    criteria = client.get(
        "/api/v1/triage-config/criteria",
        headers=authorization_header(token),
    ).json()
    return [
        {"criterion_id": criterion["id"], "value": index % 2 == 0}
        for index, criterion in enumerate(criteria)
        if criterion["is_required"]
    ]


def test_seeded_triage_configuration_is_available(
    client: TestClient,
    admin_token: str,
) -> None:
    headers = authorization_header(admin_token)
    classifications = client.get(
        "/api/v1/triage-config/classifications",
        headers=headers,
    )
    criteria = client.get("/api/v1/triage-config/criteria", headers=headers)

    assert classifications.status_code == 200
    assert {item["code"] for item in classifications.json()} == {
        "REUTILIZAVEL",
        "RECICLAVEL",
        "INUTILIZAVEL",
        "AGUARDANDO_AVALIACAO",
    }
    assert criteria.status_code == 200
    assert len(criteria.json()) == 8
    assert all(item["answer_type"] == "BOOLEAN" for item in criteria.json())


def test_complete_triage_updates_status_events_and_history(
    client: TestClient,
    admin_token: str,
) -> None:
    headers = authorization_header(admin_token)
    equipment = create_equipment(client, admin_token, "COMPLETE")
    started = client.post(
        f"/api/v1/equipments/{equipment['tracking_code']}/triages",
        headers=headers,
    )
    assert started.status_code == 201
    assert started.json()["status"] == "IN_PROGRESS"

    refreshed_equipment = client.get(
        f"/api/v1/equipments/by-code/{equipment['tracking_code']}",
        headers=headers,
    )
    assert refreshed_equipment.json()["current_status"] == "EM_TRIAGEM"

    incomplete = client.post(
        f"/api/v1/triages/{started.json()['id']}/complete",
        headers=headers,
        json={
            "classification_id": client.get(
                "/api/v1/triage-config/classifications",
                headers=headers,
            ).json()[0]["id"],
            "technical_opinion": "Parecer técnico suficiente.",
        },
    )
    assert incomplete.status_code == 400

    saved = client.put(
        f"/api/v1/triages/{started.json()['id']}/answers",
        headers=headers,
        json={"answers": boolean_answers(client, admin_token)},
    )
    assert saved.status_code == 200
    assert len(saved.json()["answers"]) == 8

    reusable = next(
        item
        for item in client.get(
            "/api/v1/triage-config/classifications",
            headers=headers,
        ).json()
        if item["code"] == "REUTILIZAVEL"
    )
    completed = client.post(
        f"/api/v1/triages/{started.json()['id']}/complete",
        headers=headers,
        json={
            "classification_id": reusable["id"],
            "technical_opinion": "Equipamento funcional e apto à reutilização.",
            "observations": "Teste automatizado.",
            "defects": "Nenhum defeito impeditivo.",
            "reusable_components": "Equipamento completo.",
        },
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETED"
    assert completed.json()["classification"]["code"] == "REUTILIZAVEL"

    refreshed_equipment = client.get(
        f"/api/v1/equipments/by-code/{equipment['tracking_code']}",
        headers=headers,
    ).json()
    assert refreshed_equipment["current_status"] == "SEPARADO_REUTILIZACAO"
    timeline = client.get(
        f"/api/v1/equipments/{equipment['id']}/timeline",
        headers=headers,
    ).json()
    assert [item["event_type"] for item in timeline][-3:] == [
        "TRIAGE_STARTED",
        "TRIAGE_COMPLETED",
        "CLASSIFIED",
    ]
    history = client.get(
        f"/api/v1/equipments/{equipment['tracking_code']}/triages",
        headers=headers,
    )
    assert history.status_code == 200
    assert history.json()[0]["id"] == started.json()["id"]

    invalid_restart = client.post(
        f"/api/v1/equipments/{equipment['tracking_code']}/triages",
        headers=headers,
    )
    assert invalid_restart.status_code == 400


def test_cancelled_triage_returns_equipment_to_queue(
    client: TestClient,
    admin_token: str,
) -> None:
    headers = authorization_header(admin_token)
    equipment = create_equipment(client, admin_token, "CANCEL")
    started = client.post(
        f"/api/v1/equipments/{equipment['tracking_code']}/triages",
        headers=headers,
    ).json()
    cancelled = client.post(
        f"/api/v1/triages/{started['id']}/cancel",
        headers=headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"
    refreshed = client.get(
        f"/api/v1/equipments/by-code/{equipment['tracking_code']}",
        headers=headers,
    ).json()
    assert refreshed["current_status"] == "AGUARDANDO_TRIAGEM"


def test_auditor_cannot_execute_or_configure_triage(
    client: TestClient,
    admin_token: str,
) -> None:
    admin_headers = authorization_header(admin_token)
    username = "triage-auditor"
    created = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": username,
            "email": "triage-auditor@example.com",
            "full_name": "Auditor da triagem",
            "password": "triage-auditor-password",
            "role_codes": ["AUDITOR"],
        },
    )
    assert created.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": "triage-auditor-password"},
    )
    auditor_headers = authorization_header(login.json()["access_token"])
    equipment = create_equipment(client, admin_token, "AUDITOR")

    assert client.get(
        f"/api/v1/equipments/{equipment['tracking_code']}/triages",
        headers=auditor_headers,
    ).status_code == 200
    assert client.post(
        f"/api/v1/equipments/{equipment['tracking_code']}/triages",
        headers=auditor_headers,
    ).status_code == 403
    assert client.post(
        "/api/v1/triage-config/criteria",
        headers=auditor_headers,
        json={
            "code": "OPTIONAL_NOTE",
            "question": "Existe alguma observação adicional?",
            "answer_type": "TEXT",
            "is_required": False,
        },
    ).status_code == 403
