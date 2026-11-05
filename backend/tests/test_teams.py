from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

TEAM = {
    "name": "Night Wolves",
    "members": [
        {"user_id": 1, "role": "captain"},
        {"user_id": 2, "role": "main"},
        {"user_id": 3, "role": "sub"},
    ],
}


def test_create_team_with_member_roles() -> None:
    response = client.post("/teams", json=TEAM)
    assert response.status_code == 201
    body = response.json()
    assert body["captain_id"] == 1
    assert [member["role"] for member in body["members"]] == ["captain", "main", "sub"]
    assert body["members"][0]["nickname"]
    assert "avatar_url" in body["members"][0]


def test_get_team_has_member_profiles() -> None:
    response = client.get("/teams/5")
    assert response.status_code == 200
    members = response.json()["members"]
    assert members[-1]["role"] == "sub"
    assert members[0]["nickname"]
    assert "avatar_url" in members[0]


def test_create_team_rejects_empty_or_long_name_and_invalid_members() -> None:
    assert client.post("/teams", json={**TEAM, "name": ""}).status_code == 422
    assert client.post("/teams", json={**TEAM, "name": "x" * 65}).status_code == 422
    assert client.post("/teams", json={**TEAM, "members": []}).status_code == 422
    repeated = {**TEAM, "members": [TEAM["members"][0]] * 3}
    assert client.post("/teams", json=repeated).status_code == 422


def test_register_team_for_tournament() -> None:
    response = client.post("/tournaments/8/registrations", json={"team_id": 5})
    assert response.status_code == 201
    assert response.json() == {"tournament_id": 8, "team_id": 5, "status": "pending"}


def test_update_registration_status_requires_valid_body_status() -> None:
    path = "/tournaments/8/registrations/5"
    assert client.patch(path, json={"status": "approved"}).status_code == 200
    assert client.patch(path, json={"status": "lol"}).status_code == 422
    assert client.patch(path, params={"status": "lol"}).status_code == 422
