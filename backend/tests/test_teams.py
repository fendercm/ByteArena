TEAM = {
    "name": "Night Wolves",
    "members": [
        {"nickname": "Alpha", "user_id": 2, "role": "main"},
        {"nickname": "Bravo", "user_id": 3, "role": "main"},
        {"nickname": "Charlie", "role": "main"},
        {"nickname": "Delta", "user_id": 5, "role": "main"},
        {"nickname": "Echo", "role": "sub"},
    ],
}


def test_create_team_with_member_roles(logged_in) -> None:
    response = logged_in.post("/teams", json=TEAM, headers={"X-User-Id": "999"})
    assert response.status_code == 201
    body = response.json()
    assert body["captain_id"] == 1
    assert [member["role"] for member in body["members"]] == [
        "captain",
        "main",
        "main",
        "main",
        "main",
        "sub",
    ]
    assert body["members"][0] == {"nickname": "Organizer", "user_id": 1, "role": "captain"}
    assert body["members"][3]["user_id"] is None


def test_get_team_has_member_profiles(client) -> None:
    response = client.get("/teams/5")
    assert response.status_code == 200
    members = response.json()["members"]
    assert members[0]["user_id"] == response.json()["captain_id"]
    assert any(member["user_id"] is None for member in members)
    assert all(member["nickname"] for member in members)


def test_create_team_requires_login(client) -> None:
    response = client.post("/teams", json=TEAM)
    assert response.status_code == 401
    assert response.json() == {"detail": "Сначала войдите через Discord"}


def test_create_team_validates_name_roster_and_unique_nicknames(logged_in) -> None:
    assert logged_in.post("/teams", json={**TEAM, "name": "A"}).status_code == 422
    assert logged_in.post("/teams", json={**TEAM, "name": "x" * 33}).status_code == 422
    assert (
        logged_in.post("/teams", json={**TEAM, "members": TEAM["members"][:3]}).status_code == 422
    )
    duplicate = {
        **TEAM,
        "members": [
            TEAM["members"][0],
            {**TEAM["members"][1], "nickname": "alpha"},
            *TEAM["members"][2:],
        ],
    }
    assert logged_in.post("/teams", json=duplicate).status_code == 422
    too_many_subs = {
        **TEAM,
        "members": [
            *TEAM["members"],
            {"nickname": "Foxtrot", "role": "sub"},
            {"nickname": "Golf", "role": "sub"},
        ],
    }
    assert logged_in.post("/teams", json=too_many_subs).status_code == 422


def test_tournament_teams_returns_fake_teams(client) -> None:
    response = client.get("/tournaments/8/teams")
    assert response.status_code == 200
    body = response.json()
    assert 2 <= len(body["items"]) <= 3
    assert body["total"] == len(body["items"])
    assert all(team["members"] for team in body["items"])


def test_register_team_for_tournament_requires_login(client) -> None:
    unauthorized = client.post("/tournaments/8/registrations", json={"team_id": 5})
    assert unauthorized.status_code == 401


def test_register_team_for_tournament_uses_authenticated_user(logged_in) -> None:
    response = logged_in.post("/tournaments/8/registrations", json={"team_id": 5})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "tournament_id": 8, "team_id": 5, "status": "pending"}


def test_my_registration_requires_login(client) -> None:
    assert client.get("/tournaments/8/my-registration").status_code == 401


def test_my_registration_uses_authenticated_user(logged_in) -> None:
    response = logged_in.get("/tournaments/8/my-registration", headers={"X-User-Id": "999"})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "tournament_id": 8, "team_id": 1, "status": "approved"}
