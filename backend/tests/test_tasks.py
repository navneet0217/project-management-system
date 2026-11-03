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


def test_developer_cannot_create_task(client, world):
    res = client.post(f"/api/v1/projects/{world.p1.id}/tasks", json={"title": "Nope nope"}, headers=auth(world.dev1))
    assert res.status_code == 403


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


def test_developer_cannot_edit_task_details(client, world):
    res = client.patch(f"/api/v1/tasks/{world.t1.id}", json={"title": "Renamed by dev"}, headers=auth(world.dev1))
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
    assert client.delete(f"/api/v1/tasks/{world.t1.id}", headers=auth(world.m2)).status_code == 404


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
