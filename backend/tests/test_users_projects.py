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
