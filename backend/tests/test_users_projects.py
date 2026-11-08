from tests.conftest import auth


def test_only_admin_can_list_users(client, world):
    assert client.get("/api/v1/users", headers=auth(world.dev1)).status_code == 403
    assert client.get("/api/v1/users", headers=auth(world.m1)).status_code == 403
    res = client.get("/api/v1/users", headers=auth(world.admin))
    assert res.status_code == 200
    assert res.json()["total"] == 6


def test_admin_creates_user_and_duplicate_email_conflicts(client, world):
    body = {"email": "New@Test.dev", "full_name": "New Person", "password": "Passw0rd1", "role": "DEVELOPER"}
    assert client.post("/api/v1/users", json=body, headers=auth(world.admin)).status_code == 201
    dup = client.post("/api/v1/users", json={**body, "email": "new@test.dev"}, headers=auth(world.admin))
    assert dup.status_code == 409


def test_weak_password_rejected(client, world):
    body = {"email": "x@test.dev", "full_name": "Weak Pass", "password": "onlyletters", "role": "DEVELOPER"}
    assert client.post("/api/v1/users", json=body, headers=auth(world.admin)).status_code == 422


def test_admin_cannot_deactivate_self(client, world):
    res = client.patch(f"/api/v1/users/{world.admin.id}", json={"is_active": False}, headers=auth(world.admin))
    assert res.status_code == 400


def test_manager_sees_only_own_projects(client, world):
    res = client.get("/api/v1/projects", headers=auth(world.m1))
    assert [p["name"] for p in res.json()["items"]] == ["Project One"]
    assert client.get(f"/api/v1/projects/{world.p2.id}", headers=auth(world.m1)).status_code == 404


def test_developer_sees_only_member_projects(client, world):
    assert client.get(f"/api/v1/projects/{world.p1.id}", headers=auth(world.dev1)).status_code == 200
    assert client.get(f"/api/v1/projects/{world.p1.id}", headers=auth(world.dev3)).status_code == 404
    assert client.get("/api/v1/projects", headers=auth(world.dev3)).json()["total"] == 0


def test_developer_cannot_create_project(client, world):
    res = client.post("/api/v1/projects", json={"name": "Sneaky"}, headers=auth(world.dev1))
    assert res.status_code == 403


def test_manager_creates_project_as_own_manager(client, world):
    res = client.post("/api/v1/projects", json={"name": "Brand New"}, headers=auth(world.m1))
    assert res.status_code == 201
    assert res.json()["manager"]["id"] == world.m1.id


def test_manager_cannot_edit_other_managers_project(client, world):
    # m1 can't even see p2, so it is a 404 rather than leaking that it exists.
    res = client.patch(f"/api/v1/projects/{world.p2.id}", json={"name": "Hacked name"}, headers=auth(world.m1))
    assert res.status_code == 404


def test_only_admin_changes_project_manager(client, world):
    url = f"/api/v1/projects/{world.p1.id}"
    assert client.patch(url, json={"manager_id": world.m2.id}, headers=auth(world.m1)).status_code == 403
    assert client.patch(url, json={"manager_id": world.m2.id}, headers=auth(world.admin)).status_code == 200


def test_member_management_rules(client, world):
    url = f"/api/v1/projects/{world.p1.id}/members"
    ok = client.post(url, json={"user_id": world.dev3.id}, headers=auth(world.m1))
    assert ok.status_code == 201
    assert client.post(url, json={"user_id": world.dev3.id}, headers=auth(world.m1)).status_code == 409
    assert client.post(url, json={"user_id": world.m2.id}, headers=auth(world.m1)).status_code == 400
    assert client.post(url, json={"user_id": world.dev3.id}, headers=auth(world.dev1)).status_code == 403


def test_removing_member_unassigns_their_tasks(client, world):
    url = f"/api/v1/projects/{world.p1.id}/members/{world.dev1.id}"
    assert client.delete(url, headers=auth(world.m1)).status_code == 204
    task = client.get(f"/api/v1/tasks/{world.t1.id}", headers=auth(world.m1)).json()
    assert task["assignee"] is None


def test_delete_project_blocked_while_tasks_open(client, world):
    res = client.delete(f"/api/v1/projects/{world.p1.id}", headers=auth(world.m1))
    assert res.status_code == 409
    client.patch(f"/api/v1/tasks/{world.t1.id}/status", json={"status": "DONE"}, headers=auth(world.m1))
    assert client.delete(f"/api/v1/projects/{world.p1.id}", headers=auth(world.m1)).status_code == 204


def test_project_completion_percentage(client, world):
    client.patch(f"/api/v1/tasks/{world.t1.id}/status", json={"status": "DONE"}, headers=auth(world.m1))
    project = client.get(f"/api/v1/projects/{world.p1.id}", headers=auth(world.m1)).json()
    assert project["completion_percentage"] == 100.0
    assert project["member_count"] == 2


def _search(client, user, text):
    res = client.get("/api/v1/projects", params={"search": text}, headers=auth(user))
    assert res.status_code == 200
    return {p["name"] for p in res.json()["items"]}


def test_project_search_matches_name_description_and_manager(client, world):
    client.patch(
        f"/api/v1/projects/{world.p1.id}", json={"description": "Quarterly marketing refresh"}, headers=auth(world.m1)
    )
    assert _search(client, world.admin, "one") == {"Project One"}  # name
    assert _search(client, world.admin, "marketing") == {"Project One"}  # description
    assert _search(client, world.admin, "m2") == {"Project Two"}  # manager name


def test_project_search_respects_visibility(client, world):
    # m1 can only ever see their own project, even when searching for another manager's name
    assert _search(client, world.m1, "m2") == set()
    assert _search(client, world.m1, "project") == {"Project One"}
    # dev1 is a member of p1 only
    assert _search(client, world.dev1, "project") == {"Project One"}


def test_users_list_sorting(client, world):
    def names(**params):
        res = client.get("/api/v1/users", params=params, headers=auth(world.admin))
        assert res.status_code == 200
        return [u["full_name"] for u in res.json()["items"]]

    asc = names(sort_by="full_name", order="asc")
    assert asc == sorted(asc, key=str.lower) or asc == sorted(asc)
    assert names(sort_by="full_name", order="desc") == list(reversed(asc))
    roles = [u["role"] for u in client.get("/api/v1/users", params={"sort_by": "role", "order": "asc"}, headers=auth(world.admin)).json()["items"]]
    assert roles == sorted(roles)
    assert client.get("/api/v1/users", params={"sort_by": "password"}, headers=auth(world.admin)).status_code == 400


def test_users_list_includes_current_projects(client, world):
    items = client.get("/api/v1/users", headers=auth(world.admin)).json()["items"]
    by_email = {u["email"]: u for u in items}
    assert [p["name"] for p in by_email["dev1@test.dev"]["projects"]] == ["Project One"]  # as a member
    assert [p["name"] for p in by_email["m1@test.dev"]["projects"]] == ["Project One"]  # as the manager
    assert by_email["dev3@test.dev"]["projects"] == []


def test_completed_projects_leave_the_projects_column(client, world):
    client.patch(f"/api/v1/projects/{world.p1.id}", json={"status": "COMPLETED"}, headers=auth(world.m1))
    items = client.get("/api/v1/users", headers=auth(world.admin)).json()["items"]
    assert next(u for u in items if u["email"] == "dev1@test.dev")["projects"] == []


def test_user_profile_sections(client, world):
    res = client.get(f"/api/v1/users/{world.dev1.id}/profile", headers=auth(world.admin))
    assert res.status_code == 200
    body = res.json()
    assert body["user"]["email"] == "dev1@test.dev" and body["user"]["is_active"] is True
    assert [m["id"] for m in body["managers"]] == [world.m1.id]
    assert [p["name"] for p in body["current_projects"]] == ["Project One"]
    assert body["current_projects"][0]["relation"] == "Member"
    assert body["past_projects"] == []
    assert [t["title"] for t in body["tasks"]] == ["First task"]
    assert body["tasks"][0]["project_name"] == "Project One"


def test_profile_past_projects_and_activity(client, world):
    client.patch(f"/api/v1/projects/{world.p1.id}", json={"status": "COMPLETED"}, headers=auth(world.m1))
    client.delete(f"/api/v1/projects/{world.p1.id}/members/{world.dev2.id}", headers=auth(world.m1))
    dev1 = client.get(f"/api/v1/users/{world.dev1.id}/profile", headers=auth(world.admin)).json()
    assert dev1["current_projects"] == []
    assert [(p["name"], p["relation"]) for p in dev1["past_projects"]] == [("Project One", "Member")]
    dev2 = client.get(f"/api/v1/users/{world.dev2.id}/profile", headers=auth(world.admin)).json()
    assert [(p["name"], p["relation"]) for p in dev2["past_projects"]] == [("Project One", "Removed")]
    assert dev2["activity"][0]["action"] == "MEMBER_REMOVED"  # the removal concerns dev2
    m1 = client.get(f"/api/v1/users/{world.m1.id}/profile", headers=auth(world.admin)).json()
    assert {a["action"] for a in m1["activity"]} == {"PROJECT_UPDATED", "MEMBER_REMOVED"}  # what m1 did


def test_profile_access_rules(client, world):
    assert client.get(f"/api/v1/users/{world.dev1.id}/profile", headers=auth(world.dev2)).status_code == 403
    assert client.get(f"/api/v1/users/{world.dev1.id}/profile", headers=auth(world.m2)).status_code == 200
    assert client.get(f"/api/v1/users/{world.m1.id}/profile", headers=auth(world.m2)).status_code == 403
    assert client.get(f"/api/v1/users/{world.admin.id}/profile", headers=auth(world.m1)).status_code == 403
    assert client.get("/api/v1/users/99999/profile", headers=auth(world.admin)).status_code == 404
    assert client.get(f"/api/v1/users/{world.dev1.id}/profile").status_code == 401


def _remove(client, actor, user):
    return client.delete(f"/api/v1/users/{user.id}", headers=auth(actor))


def _emails(client, actor, **params):
    res = client.get("/api/v1/users", params={"size": 100, **params}, headers=auth(actor))
    assert res.status_code == 200
    return {u["email"] for u in res.json()["items"]}


def test_remove_user_is_soft_and_hides_them(client, world):
    assert _remove(client, world.admin, world.dev3).status_code == 204
    assert "dev3@test.dev" not in _emails(client, world.admin)  # hidden from the normal list
    assert "dev3@test.dev" in _emails(client, world.admin, removed=True)  # visible in the Removed view
    removed = next(u for u in client.get("/api/v1/users", params={"removed": True}, headers=auth(world.admin)).json()["items"])
    assert removed["deleted_at"] is not None and removed["is_active"] is False
    assert client.get(f"/api/v1/users/{world.dev3.id}", headers=auth(world.admin)).status_code == 200  # row still exists


def test_removed_user_cannot_login_or_use_old_token(client, world):
    token_before = client.post("/api/v1/auth/login", json={"email": "dev3@test.dev", "password": "Passw0rd1"}).json()
    _remove(client, world.admin, world.dev3)
    assert client.post("/api/v1/auth/login", json={"email": "dev3@test.dev", "password": "Passw0rd1"}).status_code == 403
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": token_before["refresh_token"]}).status_code == 401
    assert client.get("/api/v1/auth/me", headers=auth(world.dev3)).status_code == 401  # access token dies too


def test_remove_user_rules(client, world):
    assert _remove(client, world.admin, world.admin).status_code == 400  # not yourself
    assert _remove(client, world.dev1, world.dev2).status_code == 403  # admin only
    assert _remove(client, world.m1, world.dev2).status_code == 403
    assert client.delete("/api/v1/users/99999", headers=auth(world.admin)).status_code == 404
    assert client.delete(f"/api/v1/users/{world.dev1.id}").status_code == 401
    # m1 manages the active Project One: cannot be removed until it is reassigned or completed
    res = _remove(client, world.admin, world.m1)
    assert res.status_code == 409 and "active project" in res.json()["detail"]
    assert "m1@test.dev" in _emails(client, world.admin)


def test_removal_keeps_history_and_can_be_restored(client, world):
    _remove(client, world.admin, world.dev1)  # dev1 has a task and is a member
    profile = client.get(f"/api/v1/users/{world.dev1.id}/profile", headers=auth(world.admin)).json()
    assert [t["title"] for t in profile["tasks"]] == ["First task"]  # history is intact
    assert client.post(f"/api/v1/users/{world.dev1.id}/restore", headers=auth(world.admin)).status_code == 200
    assert "dev1@test.dev" in _emails(client, world.admin)
    # restored users stay inactive until an admin activates them
    assert client.post("/api/v1/auth/login", json={"email": "dev1@test.dev", "password": "Passw0rd1"}).status_code == 403
    assert client.patch(f"/api/v1/users/{world.dev1.id}", json={"is_active": True}, headers=auth(world.admin)).status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": "dev1@test.dev", "password": "Passw0rd1"}).status_code == 200


def test_cannot_activate_a_removed_user_without_restoring(client, world):
    _remove(client, world.admin, world.dev3)
    res = client.patch(f"/api/v1/users/{world.dev3.id}", json={"is_active": True}, headers=auth(world.admin))
    assert res.status_code == 400 and "Restore" in res.json()["detail"]


def test_removed_users_are_not_offered_for_projects(client, world):
    _remove(client, world.admin, world.dev3)
    options = client.get("/api/v1/users/options", params={"role": "DEVELOPER"}, headers=auth(world.admin)).json()
    assert world.dev3.id not in [u["id"] for u in options]


def test_users_list_shows_managers_of_current_projects(client, world):
    by_email = {u["email"]: u for u in client.get("/api/v1/users", headers=auth(world.admin)).json()["items"]}
    assert [m["id"] for m in by_email["dev1@test.dev"]["managers"]] == [world.m1.id]
    assert by_email["dev3@test.dev"]["managers"] == []  # not on any project
    assert by_email["m1@test.dev"]["managers"] == []  # managers have no reporting manager here


def test_creating_a_project_is_logged(client, world):
    res = client.post("/api/v1/projects", json={"name": "Brand new project"}, headers=auth(world.m1))
    assert res.status_code == 201
    items = client.get(f"/api/v1/projects/{res.json()['id']}/activities", headers=auth(world.m1)).json()["items"]
    assert [i["action"] for i in items] == ["PROJECT_CREATED"]
    assert items[0]["entity_label"] == "Brand new project" and items[0]["actor"]["id"] == world.m1.id
