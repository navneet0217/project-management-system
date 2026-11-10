# Manual Functionality Test and Showcase

Use a local/test database. These checks create and change data. Mark each result Pass, Fail, or Not Tested; record failures with a screenshot.

## Setup

- Open your running app (Vite: http://localhost:5173; Docker: http://localhost:8080).
- Start Docker first: Vite now sends `/api` to port 8080, so Vite, Docker and Cloudflare share the same database. Sign in separately on each origin. Source-code changes require a Docker rebuild to update 8080/public, even though Vite updates immediately.
- Log in as `admin@demo.dev` using its current password. Confirm the name is Navneet Admin if the SQL rename was committed.
- In Users, create one MANAGER and two DEVELOPER accounts using distinct test emails. Admin-created accounts can log in without email verification.
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
| 24 | Add a developer as project member and assign them a task (as manager) | The developer's bell shows both notifications; the manager's bell shows none for their own actions | Not Tested |
| 25 | Open Users and Removed at 360/390/820/1440 px; scroll to Actions, hover/focus each icon and open Edit/Profile; check Remove confirmation and Restore using disposable users | Icon actions have tooltips and accessible names; status toggle remains usable; compact Actions does not overlay data on mobile/tablet and stays fixed on desktop; existing safeguards still work | Not Tested |

## Notifications (bell icon)

Notifications are in-app only: no email is needed. Use two browser profiles (for example manager and developer).

1. As the manager, assign a task to the developer. In the developer's session the bell in the header shows a red count within 30 seconds (or open the bell to refresh at once).
2. Open the bell: the title and text name the task and who did it. Click the item: it is marked read and opens the project.
3. Have the developer change the task status or add a comment: the manager's bell gets a notification, the developer's own bell does not (nobody is notified about their own action).
4. Use "Mark all read": the count clears. Reload: it stays cleared.
5. Adding a member, reassigning, deleting a task (with its reason) and comments also notify the people involved.

## Forgot Password (switched off for now)

The Forgot password link, its pages and the `/auth/forgot-password` and `/auth/reset-password` endpoints are commented out and will be re-enabled later. Do not demo it. Signup still sends a verification email (needs `RESEND_API_KEY`; the Resend sandbox only delivers to the account owner's address). Admin-created users need no email, so demo with those.

## Current Limits

- Multiple users can share roles; one user can have multiple roles through admin Add/Edit User. Permissions combine, but manager access remains limited to their own projects. Signup cannot grant privileged roles. The dashboard uses the highest assigned role.
- Forgot password is disabled; its automated tests are skipped. Notifications refresh every 30 seconds (no websockets).