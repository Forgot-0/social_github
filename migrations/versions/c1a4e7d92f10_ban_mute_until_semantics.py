"""chat_members: banned_to/muted_to -> banned_until/muted_until, NULL = ограничения нет

Старая семантика: NULL означал «забанен навсегда», а обычный участник создавался
со значением в прошлом. Из-за этого предикат «активный участник» приходилось
писать вручную (`banned_to IS NOT NULL AND banned_to < now()`), и любая строка,
вставленная мимо фабрики, оказывалась забаненной.

Новая семантика: NULL — ограничения нет, бессрочный бан/мьют — 9999-12-31.

Revision ID: c1a4e7d92f10
Revises: b2bbb67eacf9
Create Date: 2026-09-03 16:20:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c1a4e7d92f10'
down_revision: str | None = 'b2bbb67eacf9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMANENT = "'9999-12-31 00:00:00+00'::timestamptz"


def upgrade() -> None:
    op.alter_column('chat_members', 'banned_to', new_column_name='banned_until')
    op.alter_column('chat_members', 'muted_to', new_column_name='muted_until')
    op.alter_column('chat_member_bans', 'banned_to', new_column_name='banned_until')

    for column in ('banned_until', 'muted_until'):
        op.execute(
            sa.text(
                f"""
                UPDATE chat_members
                SET {column} = CASE
                    WHEN {column} IS NULL THEN {PERMANENT}
                    WHEN {column} > now() THEN {column}
                    ELSE NULL
                END
                """
            )
        )

    # Журнал банов хранит запрошенный срок: бессрочный бан был записан как NULL.
    op.execute(sa.text(f"UPDATE chat_member_bans SET banned_until = {PERMANENT} WHERE banned_until IS NULL"))


def downgrade() -> None:
    op.execute(
        sa.text(
            f"""
            UPDATE chat_member_bans
            SET banned_until = NULL
            WHERE banned_until >= {PERMANENT}
            """
        )
    )

    for column in ('banned_until', 'muted_until'):
        op.execute(
            sa.text(
                f"""
                UPDATE chat_members
                SET {column} = CASE
                    WHEN {column} IS NULL THEN now() - interval '1 second'
                    WHEN {column} >= {PERMANENT} THEN NULL
                    ELSE {column}
                END
                """
            )
        )

    op.alter_column('chat_member_bans', 'banned_until', new_column_name='banned_to')
    op.alter_column('chat_members', 'muted_until', new_column_name='muted_to')
    op.alter_column('chat_members', 'banned_until', new_column_name='banned_to')
