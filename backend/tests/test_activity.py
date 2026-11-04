from tests.conftest import auth


def _log(client, project, user, **params):
    res = client.get(f"/api/v1/projects/{project.id}/activities", params=params, headers=auth(user))
    assert res.status_code == 200
    return res.json()["items"]


def _actions(items):
    return [i["action"] for i in items]


def test_project_update_is_logged_with_old_and_new_values(client, world):
    res = client.patch(f"/api/v1/projects/{world.p1.id}", json={"status": "ON_HOLD", "description": "New scope"}, headers=auth(world.m1))
    assert res.status_code == 200
    items = _log(client, world.p1, world.m1, category="project")
    by_field = {i["field"]: i for i in items}
    assert (by_field["status"]["old_value"], by_field["status"]["new_value"]) == ("ACTIVE", "ON_HOLD")
    assert by_field["description"]["new_value"] == "New scope"
    assert all(i["action"] == "PROJECT_UPDATED" and i["actor"]["id"] == world.m1.id for i in items)


def test_unchanged_values_are_not_logged(client, world):
    client.patch(f"/api/v1/projects/{world.p1.id}", json={"status": "ACTIVE"}, headers=auth(world.m1))
    assert _log(client, world.p1, world.m1) == []


def test_task_changes_are_logged(client, world):
    tid = world.t1.id
    client.patch(f"/api/v1/tasks/{tid}/status", json={"status": "IN_PROGRESS"}, headers=auth(world.dev1))
    client.patch(f"/api/v1/tasks/{tid}", json={"priority": "LOW", "title": "Renamed"}, headers=auth(world.m1))
    client.patch(f"/api/v1/tasks/{tid}", json={"assignee_id": world.dev2.id}, headers=auth(world.m1))
    client.post(f"/api/v1/tasks/{tid}/comments", json={"body": "On it"}, headers=auth(world.dev2))
    items = _log(client, world.p1, world.m1)
    assert set(_actions(items)) == {
        "TASK_STATUS_CHANGED",
        "TASK_PRIORITY_CHANGED",
        "TASK_UPDATED",
        "TASK_REASSIGNED",
        "COMMENT_ADDED",
    }
    status = next(i for i in items if i["action"] == "TASK_STATUS_CHANGED")
    assert (status["old_value"], status["new_value"]) == ("TODO", "IN_PROGRESS")
    prio = next(i for i in items if i["action"] == "TASK_PRIORITY_CHANGED")
    assert (prio["old_value"], prio["new_value"]) == ("HIGH", "LOW")
    reassigned = next(i for i in items if i["action"] == "TASK_REASSIGNED")
    assert reassigned["new_value"] == world.dev2.full_name
    assert reassigned["old_value"] == world.dev1.full_name


def test_new_task_logs_creation_and_assignment(client, world):
    body = {"title": "Brand new", "assignee_id": world.dev2.id}
    client.post(f"/api/v1/projects/{world.p1.id}/tasks", json=body, headers=auth(world.m1))
    assert set(_actions(_log(client, world.p1, world.m1))) == {"TASK_CREATED", "TASK_ASSIGNED"}


def test_member_add_and_remove_are_logged(client, world):
    url = f"/api/v1/projects/{world.p1.id}/members"
    assert client.post(url, json={"user_id": world.dev3.id}, headers=auth(world.m1)).status_code == 201
    assert client.delete(f"{url}/{world.dev3.id}", headers=auth(world.m1)).status_code == 204
    items = _log(client, world.p1, world.m1, category="members")
    assert _actions(items) == ["MEMBER_REMOVED", "MEMBER_ADDED"]  # newest first
    assert items[0]["target_user"]["id"] == world.dev3.id
    assert items[0]["entity_label"] == world.dev3.full_name


def test_removing_member_logs_their_unassigned_tasks(client, world):
    client.delete(f"/api/v1/projects/{world.p1.id}/members/{world.dev1.id}", headers=auth(world.m1))
    items = _log(client, world.p1, world.m1)
    assert {"MEMBER_REMOVED", "TASK_REASSIGNED"} <= set(_actions(items))
    task_entry = next(i for i in items if i["action"] == "TASK_REASSIGNED")
    assert task_entry["new_value"] is None and task_entry["old_value"] == world.dev1.full_name


def test_cannot_add_duplicate_or_inactive_member(client, world, db):
    url = f"/api/v1/projects/{world.p1.id}/members"
    assert client.post(url, json={"user_id": world.dev1.id}, headers=auth(world.m1)).status_code == 409
    world.dev3.is_active = False
    db.commit()
    res = client.post(url, json={"user_id": world.dev3.id}, headers=auth(world.m1))
    assert res.status_code == 400
    assert "Inactive" in res.json()["detail"]
    assert _log(client, world.p1, world.m1, category="members") == []  # nothing was logged for the failures


def test_category_filter_and_paging(client, world):
    for n in range(3):
        client.post(f"/api/v1/projects/{world.p1.id}/tasks", json={"title": f"Extra {n}"}, headers=auth(world.m1))
    client.patch(f"/api/v1/projects/{world.p1.id}", json={"status": "ON_HOLD"}, headers=auth(world.m1))
    assert set(_actions(_log(client, world.p1, world.m1, category="project"))) == {"PROJECT_UPDATED"}
    assert "PROJECT_UPDATED" not in _actions(_log(client, world.p1, world.m1, category="tasks"))
    page = client.get(f"/api/v1/projects/{world.p1.id}/activities", params={"size": 2, "page": 1}, headers=auth(world.m1)).json()
    assert len(page["items"]) == 2 and page["total"] == 4  # 3 created + 1 project update


def test_activity_visibility_follows_project_access(client, world):
    client.patch(f"/api/v1/projects/{world.p1.id}", json={"status": "ON_HOLD"}, headers=auth(world.m1))
    assert client.get(f"/api/v1/projects/{world.p1.id}/activities", headers=auth(world.dev1)).status_code == 200  # member
    assert client.get(f"/api/v1/projects/{world.p1.id}/activities", headers=auth(world.dev3)).status_code == 404  # not a member
    assert client.get(f"/api/v1/projects/{world.p1.id}/activities", headers=auth(world.m2)).status_code == 404  # other manager
    assert client.get(f"/api/v1/projects/{world.p1.id}/activities").status_code == 401


def test_activity_is_stored_in_the_database(client, world, db):
    from app.models import ProjectActivity

    client.patch(f"/api/v1/projects/{world.p1.id}", json={"status": "ON_HOLD"}, headers=auth(world.m1))
    rows = db.query(ProjectActivity).filter_by(project_id=world.p1.id).all()
    assert len(rows) == 1 and rows[0].actor_id == world.m1.id
