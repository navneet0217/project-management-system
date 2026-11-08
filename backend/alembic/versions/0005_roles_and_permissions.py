"""roles, permissions, role_permissions, user_roles

Revision ID: 0005
Revises: 0004
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSIONS = {
    "ADMIN": ["user.manage", "project.create", "project.manage", "task.manage", "task.update_own", "audit.view"],
    "MANAGER": ["project.create", "project.manage", "task.manage", "task.update_own", "audit.view"],
    "DEVELOPER": ["task.update_own"],
}


def upgrade() -> None:
    roles = op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(30), nullable=False, unique=True),
    )
    perms = op.create_table(
        "permissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(60), nullable=False, unique=True),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", sa.Integer, sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )

    role_ids = {name: i for i, name in enumerate(PERMISSIONS, start=1)}
    op.bulk_insert(roles, [{"id": i, "name": n} for n, i in role_ids.items()])
    codes = sorted({c for cs in PERMISSIONS.values() for c in cs})
    perm_ids = {c: i for i, c in enumerate(codes, start=1)}
    op.bulk_insert(perms, [{"id": i, "code": c} for c, i in perm_ids.items()])
    link = sa.table("role_permissions", sa.column("role_id"), sa.column("permission_id"))
    op.bulk_insert(
        link,
        [{"role_id": role_ids[r], "permission_id": perm_ids[c]} for r, cs in PERMISSIONS.items() for c in cs],
    )
    # every existing user keeps exactly the role they already have
    op.execute(
        "INSERT INTO user_roles (user_id, role_id) "
        "SELECT u.id, r.id FROM users u JOIN roles r ON r.name = u.role"
    )


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
