from datetime import date, timedelta

from tests.conftest import auth


def test_manager_creates_task_and_activity_is_logged(client, world):
    body = {"title": "Write docs", "priority": "LOW", "assignee_id": world.dev2.id}
    res = client.post(f"/api/v1/projects/{world.p1.id}/tasks", json=body, headers=auth(world.m1))
    assert res.status_code == 201
    acts = client.get(f"/api/v1/tasks/{res.json()['id']}/activities", headers=auth(world.m1)).json()
    assert acts[0]["type"] == "CREATED"


def test_cannot_assign_non_member(client, world):
    body = {"title": "Bad assign", "assignee_id": world.dev3.id}
    res = client.post(f"/api/v1/projects/{world.p1.id}/tasks", json=body, headers=auth(world.m1))
    assert res.status_code == 400


def _delete(client, task_id, user, reason="No longer needed"):
    # DELETE carries a JSON body (the mandatory reason), so use the generic request method
    return client.request("DELETE", f"/api/v1/tasks/{task_id}", json={"reason": reason}, headers=auth(user))


def test_developer_creates_task_for_self_in_own_project(client, world):
    res = client.post(f"/api/v1/projects/{world.p1.id}/tasks", json={"title": "My own task"}, headers=auth(world.dev1))
    assert res.status_code == 201
    assert res.json()["assignee"]["id"] == world.dev1.id  # forced to the creator


def test_developer_cannot_assign_to_someone_else_or_use_foreign_project(client, world):
    other = {"title": "For dev2", "assignee_id": world.dev2.id}
    assert client.post(f"/api/v1/projects/{world.p1.id}/tasks", json=other, headers=auth(world.dev1)).status_code == 403
    # dev3 is not a member of p1 (404: the project is invisible to them)
    mine = {"title": "Sneaky task"}
    assert client.post(f"/api/v1/projects/{world.p1.id}/tasks", json=mine, headers=auth(world.dev3)).status_code == 404


def test_assignee_can_change_own_status_and_it_is_logged(client, world):
    url = f"/api/v1/tasks/{world.t1.id}/status"
    res = client.patch(url, json={"status": "IN_PROGRESS"}, headers=auth(world.dev1))
    assert res.status_code == 200
    assert res.json()["status"] == "IN_PROGRESS"
    acts = client.get(f"/api/v1/tasks/{world.t1.id}/activities", headers=auth(world.dev1)).json()
    assert acts[0]["type"] == "STATUS_CHANGED"
    assert (acts[0]["old_value"], acts[0]["new_value"]) == ("TODO", "IN_PROGRESS")
    assert acts[0]["user"]["id"] == world.dev1.id


def test_other_developer_cannot_change_status(client, world):
    url = f"/api/v1/tasks/{world.t1.id}/status"
    assert client.patch(url, json={"status": "DONE"}, headers=auth(world.dev2)).status_code == 403


def test_non_member_gets_404_for_task(client, world):
    assert client.get(f"/api/v1/tasks/{world.t1.id}", headers=auth(world.dev3)).status_code == 404
    assert client.patch(f"/api/v1/tasks/{world.t1.id}/status", json={"status": "DONE"}, headers=auth(world.dev3)).status_code == 404


def test_owner_can_edit_own_task_but_not_the_assignee(client, world):
    url = f"/api/v1/tasks/{world.t1.id}"
    res = client.patch(url, json={"title": "Renamed by owner", "priority": "LOW"}, headers=auth(world.dev1))
    assert res.status_code == 200
    assert (res.json()["title"], res.json()["priority"]) == ("Renamed by owner", "LOW")
    assert client.patch(url, json={"assignee_id": world.dev2.id}, headers=auth(world.dev1)).status_code == 403


def test_other_developer_cannot_edit_task(client, world):
    res = client.patch(f"/api/v1/tasks/{world.t1.id}", json={"title": "Not mine"}, headers=auth(world.dev2))
    assert res.status_code == 403


def test_reassigning_logs_assignee_change(client, world):
    res = client.patch(f"/api/v1/tasks/{world.t1.id}", json={"assignee_id": world.dev2.id}, headers=auth(world.m1))
    assert res.status_code == 200
    assert res.json()["assignee"]["id"] == world.dev2.id
    acts = client.get(f"/api/v1/tasks/{world.t1.id}/activities", headers=auth(world.m1)).json()
    assert acts[0]["type"] == "ASSIGNEE_CHANGED"
    assert acts[0]["new_value"] == world.dev2.full_name


def test_other_manager_cannot_touch_task(client, world):
    assert client.patch(f"/api/v1/tasks/{world.t1.id}", json={"title": "Hijack"}, headers=auth(world.m2)).status_code == 404
    assert _delete(client, world.t1.id, world.m2).status_code == 404


def test_comments_member_only(client, world):
    url = f"/api/v1/tasks/{world.t1.id}/comments"
    assert client.post(url, json={"body": "Looking at it"}, headers=auth(world.dev2)).status_code == 201
    assert client.post(url, json={"body": "Intruder"}, headers=auth(world.dev3)).status_code == 404
    comments = client.get(url, headers=auth(world.m1)).json()
    assert [c["body"] for c in comments] == ["Looking at it"]


def test_filters_search_sort_and_pagination(client, world):
    base = f"/api/v1/projects/{world.p1.id}/tasks"
    for title, prio in [("Alpha job", "LOW"), ("Beta job", "CRITICAL"), ("Gamma job", "MEDIUM")]:
        client.post(base, json={"title": title, "priority": prio}, headers=auth(world.m1))
    h = auth(world.m1)
    assert client.get(base, params={"search": "beta"}, headers=h).json()["total"] == 1
    assert client.get(base, params={"priority": "LOW"}, headers=h).json()["total"] == 1
    by_prio = client.get(base, params={"sort_by": "priority", "order": "desc"}, headers=h).json()["items"]
    assert by_prio[0]["priority"] == "CRITICAL"
    page = client.get(base, params={"size": 2, "page": 2}, headers=h).json()
    assert page["total"] == 4 and len(page["items"]) == 2
    assert client.get(base, params={"sort_by": "password"}, headers=h).status_code == 400


def test_overdue_and_due_soon_flags(client, world):
    base = f"/api/v1/projects/{world.p1.id}/tasks"
    past = (date.today() - timedelta(days=3)).isoformat()
    soon = (date.today() + timedelta(days=1)).isoformat()
    a = client.post(base, json={"title": "Late one", "deadline": past}, headers=auth(world.m1)).json()
    b = client.post(base, json={"title": "Soon one", "deadline": soon}, headers=auth(world.m1)).json()
    assert a["is_overdue"] is True and a["due_soon"] is False
    assert b["is_overdue"] is False and b["due_soon"] is True
    done = client.patch(f"/api/v1/tasks/{a['id']}/status", json={"status": "DONE"}, headers=auth(world.m1)).json()
    assert done["is_overdue"] is False


def test_my_tasks_only_returns_assigned(client, world):
    res = client.get("/api/v1/tasks/my", headers=auth(world.dev1)).json()
    assert [t["id"] for t in res["items"]] == [world.t1.id]
    assert client.get("/api/v1/tasks/my", headers=auth(world.dev2)).json()["total"] == 0


def test_dashboards_are_role_specific(client, world):
    admin = client.get("/api/v1/dashboard", headers=auth(world.admin)).json()
    assert admin["summary"]["total_users"] == 6 and admin["summary"]["total_projects"] == 2
    manager = client.get("/api/v1/dashboard", headers=auth(world.m1)).json()
    assert manager["summary"]["managed_projects"] == 1 and manager["summary"]["total_tasks"] == 1
    other = client.get("/api/v1/dashboard", headers=auth(world.m2)).json()
    assert other["summary"]["total_tasks"] == 0
    dev = client.get("/api/v1/dashboard", headers=auth(world.dev1)).json()
    assert dev["summary"]["assigned_tasks"] == 1 and dev["summary"]["pending_tasks"] == 1
    assert set(dev["tasks_by_status"]) == {"TODO", "IN_PROGRESS", "IN_REVIEW", "DONE"}


def test_health(client):
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def _make_task(client, world, project, title, **extra):
    res = client.post(f"/api/v1/projects/{project.id}/tasks", json={"title": title, **extra}, headers=auth(world.admin))
    assert res.status_code == 201
    return res.json()


def test_visible_tasks_are_scoped_by_role(client, world):
    _make_task(client, world, world.p2, "Second project task")
    admin = client.get("/api/v1/tasks", headers=auth(world.admin)).json()
    assert admin["total"] == 2  # t1 + the new one
    # a manager only sees tasks in the projects they manage
    m1 = client.get("/api/v1/tasks", headers=auth(world.m1)).json()
    assert [t["title"] for t in m1["items"]] == ["First task"]
    m2 = client.get("/api/v1/tasks", headers=auth(world.m2)).json()
    assert [t["title"] for t in m2["items"]] == ["Second project task"]
    # a developer only sees tasks assigned to them
    assert client.get("/api/v1/tasks", headers=auth(world.dev1)).json()["total"] == 1
    assert client.get("/api/v1/tasks", headers=auth(world.dev2)).json()["total"] == 0


def test_visible_tasks_newest_first_and_include_project_name(client, world):
    _make_task(client, world, world.p1, "Newest one")
    items = client.get("/api/v1/tasks", params={"sort_by": "created_at", "order": "desc", "size": 5}, headers=auth(world.admin)).json()["items"]
    assert items[0]["title"] == "Newest one"
    assert items[0]["project_name"] == "Project One"


def test_visible_tasks_need_login(client, world):
    assert client.get("/api/v1/tasks").status_code == 401


def test_delete_requires_a_reason(client, world):
    url = f"/api/v1/tasks/{world.t1.id}"
    assert client.request("DELETE", url, headers=auth(world.m1)).status_code == 422  # no body
    assert _delete(client, world.t1.id, world.m1, reason="   ").status_code == 422  # blank
    assert _delete(client, world.t1.id, world.m1, reason="ab").status_code == 422  # too short
    assert client.get(url, headers=auth(world.m1)).status_code == 200  # still there


def test_developer_can_delete_only_self_created_own_task(client, world):
    # t1 is assigned to dev1 but was created by the manager: dev1 may not delete it
    assert _delete(client, world.t1.id, world.dev1).status_code == 403
    mine = client.post(f"/api/v1/projects/{world.p1.id}/tasks", json={"title": "Scratch task"}, headers=auth(world.dev1)).json()
    assert _delete(client, mine["id"], world.dev2).status_code == 403  # someone else's task
    assert _delete(client, mine["id"], world.dev1).status_code == 204


def test_delete_reason_is_saved_in_project_activity(client, world):
    assert _delete(client, world.t1.id, world.m1, reason="Duplicate of another task").status_code == 204
    log = client.get(f"/api/v1/projects/{world.p1.id}/activities", headers=auth(world.m1)).json()["items"]
    deleted = [a for a in log if a["action"] == "TASK_DELETED"]
    assert len(deleted) == 1
    assert deleted[0]["comment"] == "Duplicate of another task"
    assert deleted[0]["entity_label"] == "First task"
    assert deleted[0]["actor"]["id"] == world.m1.id
