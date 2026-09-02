"""message reactions

Revision ID: af3c1d9b2e40
Revises: e80b7866ae85
Create Date: 2026-09-02 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'af3c1d9b2e40'
down_revision: str | None = 'e80b7866ae85'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

chat_reactions_mode = postgresql.ENUM(
    'all', 'some', 'none', name='chat_reactions_mode'
)


def upgrade() -> None:
    chat_reactions_mode.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'chats',
        sa.Column(
            'reactions_mode',
            chat_reactions_mode,
            server_default='all',
            nullable=False,
        ),
    )
    op.add_column(
        'chats',
        sa.Column(
            'allowed_reactions',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default='[]',
            nullable=False,
        ),
    )

    op.create_table(
        'message_reactions',
        sa.Column('message_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('emoji', sa.String(length=32), nullable=False),
        sa.Column('chat_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('message_id', 'user_id', 'emoji'),
    )
    op.create_index(
        'ix_message_reactions_recent',
        'message_reactions',
        ['message_id', 'emoji', 'created_at'],
        unique=False,
    )
    op.create_index(
        'ix_message_reactions_chat_message',
        'message_reactions',
        ['chat_id', 'message_id'],
        unique=False,
    )

    op.create_table(
        'message_reaction_counters',
        sa.Column('message_id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('emoji', sa.String(length=32), nullable=False),
        sa.Column('chat_id', sa.UUID(), nullable=False),
        sa.Column('count', sa.BigInteger(), nullable=False),
        sa.Column('version', sa.BigInteger(), nullable=False),
        sa.Column('first_reacted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_reacted_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('message_id', 'emoji'),
    )
    op.create_index(
        'ix_message_reaction_counters_chat_message',
        'message_reaction_counters',
        ['chat_id', 'message_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        'ix_message_reaction_counters_chat_message',
        table_name='message_reaction_counters',
    )
    op.drop_table('message_reaction_counters')

    op.drop_index('ix_message_reactions_chat_message', table_name='message_reactions')
    op.drop_index('ix_message_reactions_recent', table_name='message_reactions')
    op.drop_table('message_reactions')

    op.drop_column('chats', 'allowed_reactions')
    op.drop_column('chats', 'reactions_mode')

    chat_reactions_mode.drop(op.get_bind(), checkfirst=True)
