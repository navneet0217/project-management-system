from tests.conftest import auth


def _inbox(client, user):
    return client.get("/api/v1/notifications", headers=auth(user)).json()


def test_assigning_a_task_notifies_the_assignee_not_the_actor(client, world):
    body = {"title": "Write docs", "assignee_id": world.dev2.id}
    client.post(f"/api/v1/projects/{world.p1.id}/tasks", json=body, headers=auth(world.m1))
    inbox = _inbox(client, world.dev2)
    assert inbox["unread"] == 1 and "Write docs" in inbox["items"][0]["title"]
    assert inbox["items"][0]["project_id"] == world.p1.id
    assert _inbox(client, world.m1)["items"] == []  # m1 is the manager AND the actor


def test_status_change_notifies_the_manager_when_the_developer_acts(client, world):
    client.patch(f"/api/v1/tasks/{world.t1.id}/status", json={"status": "IN_PROGRESS"}, headers=auth(world.dev1))
    assert "IN_PROGRESS" in _inbox(client, world.m1)["items"][0]["body"]
    assert _inbox(client, world.dev1)["items"] == []


def test_comment_and_member_notifications(client, world):
    client.post(f"/api/v1/tasks/{world.t1.id}/comments", json={"body": "Please check"}, headers=auth(world.m1))
    assert "Please check" in _inbox(client, world.dev1)["items"][0]["body"]
    client.post(f"/api/v1/projects/{world.p1.id}/members", json={"user_id": world.dev3.id}, headers=auth(world.m1))
    assert _inbox(client, world.dev3)["unread"] == 1


def test_delete_notification_contains_the_reason(client, world):
    client.request("DELETE", f"/api/v1/tasks/{world.t1.id}", json={"reason": "Duplicate work"}, headers=auth(world.m1))
    assert "Duplicate work" in _inbox(client, world.dev1)["items"][0]["body"]


def test_no_notification_for_inactive_users_or_project_edits(client, world, db):
    world.dev1.is_active = False
    db.commit()
    client.patch(f"/api/v1/tasks/{world.t1.id}", json={"priority": "LOW"}, headers=auth(world.m1))
    assert _inbox(client, world.m1)["items"] == []
    client.patch(f"/api/v1/projects/{world.p1.id}", json={"status": "ON_HOLD"}, headers=auth(world.m1))
    assert _inbox(client, world.m1)["items"] == []


def test_failed_change_leaves_no_notification(client, world):
    body = {"title": "Bad assign", "assignee_id": world.dev3.id}  # dev3 is not a member -> 400, rolled back
    assert client.post(f"/api/v1/projects/{world.p1.id}/tasks", json=body, headers=auth(world.m1)).status_code == 400
    assert _inbox(client, world.dev3)["items"] == []


def test_mark_read_only_affects_my_own_notifications(client, world):
    client.patch(f"/api/v1/tasks/{world.t1.id}", json={"priority": "LOW"}, headers=auth(world.m1))
    note = _inbox(client, world.dev1)["items"][0]
    assert client.post(f"/api/v1/notifications/{note['id']}/read", headers=auth(world.dev2)).status_code == 204
    assert _inbox(client, world.dev1)["unread"] == 1  # another user cannot mark it read
    assert client.post("/api/v1/notifications/read-all", headers=auth(world.dev1)).status_code == 204
    assert _inbox(client, world.dev1)["unread"] == 0
    assert client.get("/api/v1/notifications").status_code == 401
