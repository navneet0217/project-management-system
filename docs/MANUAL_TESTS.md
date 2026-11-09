# Manual Functionality Test and Showcase

Use a local/test database. These checks create and change data. Mark each result Pass, Fail, or Not Tested; record failures with a screenshot.

## Setup

- Open your running app (Vite: http://localhost:5173; Docker: http://localhost:8080).
- Start Docker first: Vite now sends `/api` to port 8080, so Vite, Docker and Cloudflare share the same database. Sign in separately on each origin. Source-code changes require a Docker rebuild to update 8080/public, even though Vite updates immediately.
- Log in as `admin@demo.dev` using its current password. Confirm the name is Navneet Admin if the SQL rename was committed.
- In Users, create one MANAGER and two DEVELOPER accounts using distinct test emails. Use an inbox you control for the password-reset test. Admin-created accounts can log in without email verification.
- Use separate browser profiles/private sessions to demonstrate different users.

## Showcase Checklist

| ID | Action | Expected result | Result |
|---|---|---|---|
| 1 | Try an incorrect password, then the correct admin login | Incorrect login rejected; correct login opens dashboard | Not Tested |
| 2 | Open Users; search, filter and sort; view a profile | Matching rows and relevant profile details appear | Not Tested |
| 3 | Edit a test user's name | Saved name appears after reload | Not Tested |
| 4 | Deactivate a test developer; try their login; reactivate | Login blocked while inactive, restored when active | Not Tested |
| 5 | Create an ACTIVE project with a manager and dates | Project appears in the list and detail screen | Not Tested |
| 6 | Add both developers through Members; inspect details popup | Members and their details appear; activity records the additions | Not Tested |
| 7 | Create tasks with different priorities, deadlines and assignees | List shows saved values; tasks appear for their assignees | Not Tested |
| 8 | Search, filter and sort tasks | Results match selected criteria | Not Tested |
| 9 | Drag a task between Kanban columns; reload | New status persists and appears in activity | Not Tested |
| 10 | Edit a task's priority, deadline and assignee; add a comment | Saved changes, comment and relevant activity are visible | Not Tested |
| 11 | Log in as a developer; open My Tasks and edit their task | Own tasks and permitted controls work; Users administration is unavailable | Not Tested |
| 12 | As developer, attempt another user's restricted task update through Swagger | Server rejects the operation, not just the UI | Not Tested |
| 13 | Delete a disposable task without a reason, then with a valid reason | Empty reason blocked; valid deletion succeeds and reason appears in project activity | Not Tested |
| 14 | As admin, remove a project member with assigned tasks | Membership removed, tasks unassigned, activity recorded | Not Tested |
| 15 | Try deleting a disposable project containing unfinished tasks | Deletion blocked; after completing its tasks, deletion succeeds | Not Tested |
| 16 | Open dashboard; inspect KPIs, charts, recent-item popups and View All links | Values reflect test data; links open the relevant lists | Not Tested |
| 17 | Toggle light/dark mode; inspect project tags in the admin Users table and profiles; reload and check narrow/mobile layout | Project names remain readable in both themes; theme persists and controls remain usable | Not Tested |
| 18 | Log out; revisit a protected screen | Login is required | Not Tested |
| 19 | As admin, give one user MANAGER + DEVELOPER; save and reopen | Both roles appear in the user table, form and profile | Not Tested |
| 20 | Give that user their own managed project and membership in another manager's project | Both projects are visible; only their managed project allows member/project administration | Not Tested |
| 21 | Assign a task to that mixed-role user in the other project; log in as them | Task appears in My Tasks and can be edited; they cannot reassign it or manage that project | Not Tested |
| 22 | As admin, remove their MANAGER role; try a restricted operation using their existing session | Backend immediately applies the remaining role; reload refreshes navigation | Not Tested |
| 23 | Try removing your own ADMIN role or saving an empty role selection | Request rejected; admin access preserved | Not Tested |
| 24 | Create a user with a real Gmail inbox; add as member and allocate a task | Membership and assignment emails arrive; actor receives no email about their own action | Not Tested |
| 25 | Open Users and Removed at 360/390/820/1440 px; scroll to Actions, hover/focus each icon and open Edit/Profile; check Remove confirmation and Restore using disposable users | Icon actions have tooltips and accessible names; status toggle remains usable; compact Actions does not overlay data on mobile/tablet and stays fixed on desktop; existing safeguards still work | Not Tested |

## Forgot Password Locally

1. Use a disposable active account with a real email you control, not `admin@demo.dev`.
2. Log out, select Forgot Password, submit that email. Expect a generic confirmation (not proof of delivery).
3. If `RESEND_API_KEY` is unset, the reset email/link is printed in backend logs, not delivered. For Docker, run `docker compose logs --tail=100 backend` from the repository root; for a local backend, inspect its terminal.
4. If Resend is configured, check the inbox and backend errors. Sandbox delivery is limited to the Resend account owner's email until a sending domain is verified.
5. Set shared email configuration in root `.env`; local Uvicorn also reads `backend/.env`, whose values override root settings. Ensure `APP_URL` matches the running frontend origin. Restart local Uvicorn after changing configuration; for Compose environment changes run `docker compose up -d --force-recreate backend` from the repository root.
6. Open the reset link, enter a password with at least 8 characters, a letter and a number. Confirm new-password login succeeds and old-password login fails.
7. Reuse the link: expect rejection. Request two links: only the newest should work. An unknown email should get the same generic confirmation.

Reset links expire after 30 minutes by default. Existing refresh tokens are revoked; already-issued access tokens are not immediately invalidated by this implementation. Never share reset links or screenshots containing tokens.

## Current Limits

- Multiple users can share roles; one user can have multiple roles through admin Add/Edit User. Permissions combine, but manager access remains limited to their own projects. Signup cannot grant privileged roles. The dashboard uses the highest assigned role.
- Automated reset tests use a test database and captured email, not your actual SMTP/Resend delivery or browser. Complete the local steps above before claiming the deployed flow works.