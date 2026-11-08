from tests.conftest import auth


def _mail(outbox, to=None):
    return [m for m in outbox.sent if to is None or m.to == to]


def test_assigning_a_task_emails_the_assignee_not_the_actor(client, world, outbox):
    body = {"title": "Write docs", "assignee_id": world.dev2.id}
    client.post(f"/api/v1/projects/{world.p1.id}/tasks", json=body, headers=auth(world.m1))
    assert [m.to for m in outbox.sent] == ["dev2@test.dev"]  # m1 is the manager AND the actor: not emailed
    assert "assigned" in outbox.sent[0].subject.lower() or "assigned" in outbox.sent[0].html
    assert f"/projects/{world.p1.id}" in outbox.sent[0].html


def test_status_change_emails_manager_when_the_developer_acts(client, world, outbox):
    client.patch(f"/api/v1/tasks/{world.t1.id}/status", json={"status": "IN_PROGRESS"}, headers=auth(world.dev1))
    assert [m.to for m in outbox.sent] == ["m1@test.dev"]  # dev1 did it, so only the manager hears about it
    assert "IN_PROGRESS" in outbox.sent[0].html


def test_manager_edit_emails_the_assignee(client, world, outbox):
    client.patch(f"/api/v1/tasks/{world.t1.id}", json={"priority": "LOW"}, headers=auth(world.m1))
    assert [m.to for m in outbox.sent] == ["dev1@test.dev"]


def test_comment_emails_assignee_and_manager_except_author(client, world, outbox):
    client.post(f"/api/v1/tasks/{world.t1.id}/comments", json={"body": "Please check"}, headers=auth(world.m1))
    assert [m.to for m in outbox.sent] == ["dev1@test.dev"]
    assert "Please check" in outbox.sent[0].html
    outbox.sent.clear()
    client.post(f"/api/v1/tasks/{world.t1.id}/comments", json={"body": "On it"}, headers=auth(world.dev1))
    assert [m.to for m in outbox.sent] == ["m1@test.dev"]


def test_delete_email_contains_the_reason(client, world, outbox):
    client.request("DELETE", f"/api/v1/tasks/{world.t1.id}", json={"reason": "Duplicate work"}, headers=auth(world.m1))
    assert [m.to for m in outbox.sent] == ["dev1@test.dev"] and "Duplicate work" in outbox.sent[0].html


def test_member_added_emails_the_new_member(client, world, outbox):
    client.post(f"/api/v1/projects/{world.p1.id}/members", json={"user_id": world.dev3.id}, headers=auth(world.m1))
    assert [m.to for m in outbox.sent] == ["dev3@test.dev"]


def test_no_email_for_inactive_users_or_project_edits(client, world, outbox, db):
    world.dev1.is_active = False
    db.commit()
    client.patch(f"/api/v1/tasks/{world.t1.id}", json={"priority": "LOW"}, headers=auth(world.m1))
    assert outbox.sent == []  # the only possible recipient is inactive
    client.patch(f"/api/v1/projects/{world.p1.id}", json={"status": "ON_HOLD"}, headers=auth(world.m1))
    assert outbox.sent == []  # project-level edits are not emailed


def test_failed_change_sends_nothing(client, world, outbox):
    # unknown assignee -> 400, rolled back: no email may leave
    body = {"title": "Bad assign", "assignee_id": world.dev3.id}  # dev3 is not a member
    assert client.post(f"/api/v1/projects/{world.p1.id}/tasks", json=body, headers=auth(world.m1)).status_code == 400
    assert outbox.sent == []


def test_a_broken_email_provider_never_breaks_the_request(client, world, outbox):
    from app.services import email_service

    class Broken:
        def send(self, email):
            raise RuntimeError("provider down")

    email_service._provider = Broken()
    res = client.patch(f"/api/v1/tasks/{world.t1.id}", json={"priority": "LOW"}, headers=auth(world.m1))
    assert res.status_code == 200 and res.json()["priority"] == "LOW"
