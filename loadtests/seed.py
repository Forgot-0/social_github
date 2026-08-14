"""Seed a local docker-compose environment with load test fixtures.

Writes directly to Postgres using the application's own SQLAlchemy table
metadata (no raw DDL, no duplicated column lists). The full auth flow is
deliberately bypassed: registration/login is not what this test measures.

No domain events are emitted, so nothing lands in the outbox and the delivery
pipeline stays idle until the scenarios start.

The resulting dataset (user ids + usernames + chat ids per cohort) is written as
JSON so the Locust scenarios can load it without touching the database.

Usage (inside the loadtest container):

    python -m loadtests.seed --users 500 --direct-chats 200 \\
        --group-chats 20 --group-size 100 \\
        --supergroups 2 --supergroup-size 1200

Cohorts produced:
    direct      ChatType.DIRECT, 2 members         -> fanout_on_write
    group       ChatType.GROUP, size < 500         -> fanout_on_write
    supergroup  ChatType.SUPERGROUP                -> active_subscribers
    channel     ChatType.CHANNEL                   -> channel_subscribers
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from datetime import timedelta
from pathlib import Path
from uuid import UUID, uuid7

from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.auth.models.user import User
from app.chats.config import chat_config
from app.chats.models.chat import Chat, ChatType
from app.chats.models.chat_members import ChatMember
from app.chats.models.chat_roles import ChatRole
from app.chats.models.profile import ChatUserProfile
from app.core.utils import now_utc

from loadtests.config import config

# Role ids come from ChatRolesEnum (app/chats/models/permission.py), seeded by
# app.init_data during migrations.
ROLE_OWNER = 1
ROLE_DIRECT_MEMBER = 4
ROLE_MEMBER = 5
ROLE_VIEWER = 6

USERNAME_PREFIX = "lt_user_"
INSERT_CHUNK = 5_000


@dataclass(slots=True)
class ChatFixture:
    chat_id: str
    chat_type: str
    fanout_strategy: str
    member_count: int
    owner_id: int
    member_ids: list[int]


@dataclass(slots=True)
class Dataset:
    users: dict[str, str] = field(default_factory=dict)
    direct: list[ChatFixture] = field(default_factory=list)
    group: list[ChatFixture] = field(default_factory=list)
    supergroup: list[ChatFixture] = field(default_factory=list)
    channel: list[ChatFixture] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "users": self.users,
            "cohorts": {
                name: [asdict(item) for item in getattr(self, name)]
                for name in ("direct", "group", "supergroup", "channel")
            },
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed load test data")
    parser.add_argument("--users", type=int, default=500, help="N: number of users to create")
    parser.add_argument("--direct-chats", type=int, default=200, help="M: direct chats")
    parser.add_argument("--group-chats", type=int, default=20, help="K: group chats")
    parser.add_argument(
        "--group-size",
        type=int,
        default=100,
        help=f"Members per group chat, must stay below FAN_OUT_WRITE_THRESHOLD "
             f"({chat_config.FAN_OUT_WRITE_THRESHOLD})",
    )
    parser.add_argument("--supergroups", type=int, default=2, help="Supergroups above the threshold")
    parser.add_argument(
        "--supergroup-size",
        type=int,
        default=chat_config.FAN_OUT_WRITE_THRESHOLD * 2,
        help="Members per supergroup",
    )
    parser.add_argument("--channels", type=int, default=1, help="Channels (channel_subscribers)")
    parser.add_argument("--channel-size", type=int, default=1_000, help="Subscribers per channel")
    parser.add_argument(
        "--output",
        default=config.dataset_path,
        help="Where to write the dataset JSON consumed by the scenarios",
    )
    parser.add_argument("--seed", type=int, default=1337, help="RNG seed for reproducible fixtures")
    parser.add_argument(
        "--purge",
        action="store_true",
        help="Delete previously seeded load test data (users prefixed lt_user_) first",
    )
    args = parser.parse_args(argv)

    if args.group_size >= chat_config.FAN_OUT_WRITE_THRESHOLD:
        parser.error(
            f"--group-size must be below FAN_OUT_WRITE_THRESHOLD "
            f"({chat_config.FAN_OUT_WRITE_THRESHOLD}) to exercise fanout_on_write; "
            f"use --supergroups for the active_subscribers path"
        )
    if args.group_size > chat_config.MAX_GROUP_MEMBERS:
        parser.error(f"--group-size exceeds MAX_GROUP_MEMBERS ({chat_config.MAX_GROUP_MEMBERS})")
    if args.supergroups and args.supergroup_size <= chat_config.FAN_OUT_WRITE_THRESHOLD:
        parser.error(
            f"--supergroup-size must exceed FAN_OUT_WRITE_THRESHOLD "
            f"({chat_config.FAN_OUT_WRITE_THRESHOLD}) for the test to be meaningful"
        )

    largest = max(
        [2]
        + ([args.group_size] if args.group_chats else [])
        + ([args.supergroup_size] if args.supergroups else [])
        + ([args.channel_size] if args.channels else [])
    )
    if args.users < largest:
        parser.error(f"--users must be >= the largest chat size ({largest})")

    return args


async def verify_roles(conn: AsyncConnection) -> None:
    rows = (await conn.execute(select(ChatRole.id))).scalars().all()
    missing = {ROLE_OWNER, ROLE_DIRECT_MEMBER, ROLE_MEMBER, ROLE_VIEWER} - set(rows)
    if missing:
        raise SystemExit(
            f"chat_roles rows {sorted(missing)} are missing. "
            "Run the migrations service first (alembic upgrade head && python -m app.init_data)."
        )


async def purge(conn: AsyncConnection) -> None:
    user_ids = (
        await conn.execute(select(User.id).where(User.username.like(f"{USERNAME_PREFIX}%")))
    ).scalars().all()
    if not user_ids:
        print("purge: nothing to remove")
        return

    chat_ids = (
        await conn.execute(select(Chat.id).where(Chat.created_by.in_(user_ids)))
    ).scalars().all()

    if chat_ids:
        # chat_members has ON DELETE CASCADE from chats.
        await conn.execute(delete(Chat).where(Chat.id.in_(chat_ids)))
    await conn.execute(delete(ChatMember).where(ChatMember.user_id.in_(user_ids)))
    await conn.execute(delete(ChatUserProfile).where(ChatUserProfile.user_id.in_(user_ids)))
    await conn.execute(delete(User).where(User.id.in_(user_ids)))
    print(f"purge: removed {len(user_ids)} users and {len(chat_ids)} chats")


async def create_users(conn: AsyncConnection, count: int) -> dict[int, str]:
    offset = (
        await conn.execute(
            select(func.count()).select_from(User).where(User.username.like(f"{USERNAME_PREFIX}%"))
        )
    ).scalar_one()

    rows = []
    for i in range(count):
        username = f"{USERNAME_PREFIX}{offset + i}_{uuid7().hex[:8]}"
        rows.append(
            {
                "email": f"{username}@loadtest.invalid",
                "username": username,
                "password_hash": None,
                "is_active": True,
                "is_verified": True,
            }
        )

    created: dict[int, str] = {}
    for start in range(0, len(rows), INSERT_CHUNK):
        chunk = rows[start:start + INSERT_CHUNK]
        result = await conn.execute(
            insert(User).returning(User.id, User.username),
            chunk,
        )
        created.update({row.id: row.username for row in result})

    # chat_user_profiles is normally filled by the profile projection consumer.
    # Seeding it directly keeps message list/detail queries from returning
    # null authors, which would otherwise skew response sizes.
    profiles = [
        {
            "user_id": user_id,
            "username": username,
            "display_name": username,
            "avatar_s3_key": None,
            "last_event_id": None,
            "source_updated_at": now_utc(),
        }
        for user_id, username in created.items()
    ]
    for start in range(0, len(profiles), INSERT_CHUNK):
        await conn.execute(insert(ChatUserProfile), profiles[start:start + INSERT_CHUNK])

    print(f"users: created {len(created)}")
    return created


def build_chat_rows(
    chat_type: ChatType,
    owner_id: int,
    member_ids: list[int],
    name: str | None,
) -> tuple[dict, list[dict], ChatFixture]:
    chat_id = uuid7()
    all_members = [owner_id, *[m for m in member_ids if m != owner_id]]

    if chat_type == ChatType.DIRECT:
        member_role = ROLE_DIRECT_MEMBER
        owner_role = ROLE_DIRECT_MEMBER
    elif chat_type == ChatType.CHANNEL:
        member_role = ROLE_VIEWER
        owner_role = ROLE_OWNER
    else:
        member_role = ROLE_MEMBER
        owner_role = ROLE_OWNER

    chat_row = {
        "id": chat_id,
        "seq_counter": 0,
        "type": chat_type,
        "name": name,
        "description": None,
        "avatar_s3_key": None,
        "is_public": chat_type in (ChatType.SUPERGROUP, ChatType.CHANNEL),
        "created_by": owner_id,
        "member_count": len(all_members),
        "admin_only": False,
        "slow_mode_seconds": 0,
        "permissions": {},
        "last_activity_at": None,
    }

    # ChatMember.is_banned / is_muted return True when the timestamp is None or
    # in the future, so both must be set to a past instant for the member to be
    # able to send. This mirrors what ChatMember.create does at request time.
    past = now_utc() - timedelta(days=1)
    member_rows = [
        {
            "chat_id": chat_id,
            "user_id": user_id,
            "role_id": owner_role if user_id == owner_id else member_role,
            "muted_to": past,
            "banned_to": past,
            "permissions_overrides": {},
        }
        for user_id in all_members
    ]

    fixture = ChatFixture(
        chat_id=str(chat_id),
        chat_type=chat_type.value,
        fanout_strategy=_expected_strategy(chat_type, len(all_members)),
        member_count=len(all_members),
        owner_id=owner_id,
        member_ids=all_members,
    )
    return chat_row, member_rows, fixture


def _expected_strategy(chat_type: ChatType, member_count: int) -> str:
    # Mirrors Chat.fanout_strategy without needing an ORM instance.
    if chat_type == ChatType.CHANNEL:
        return "channel_subscribers"
    if chat_type == ChatType.SUPERGROUP:
        return "active_subscribers"
    if chat_type == ChatType.GROUP and member_count > chat_config.FAN_OUT_WRITE_THRESHOLD:
        return "active_subscribers"
    return "fanout_on_write"


async def flush(conn: AsyncConnection, chats: list[dict], members: list[dict]) -> None:
    if chats:
        await conn.execute(insert(Chat), chats)
    for start in range(0, len(members), INSERT_CHUNK):
        await conn.execute(insert(ChatMember), members[start:start + INSERT_CHUNK])


async def seed(args: argparse.Namespace) -> Dataset:
    rng = random.Random(args.seed)
    engine = create_async_engine(config.db_dsn, pool_pre_ping=True)
    dataset = Dataset()

    try:
        async with engine.begin() as conn:
            await verify_roles(conn)
            if args.purge:
                await purge(conn)

            users = await create_users(conn, args.users)
            user_ids = sorted(users)
            dataset.users = {str(uid): uname for uid, uname in users.items()}

            chat_rows: list[dict] = []
            member_rows: list[dict] = []

            for i in range(args.direct_chats):
                a, b = rng.sample(user_ids, 2)
                chat, members, fixture = build_chat_rows(ChatType.DIRECT, a, [b], None)
                chat_rows.append(chat)
                member_rows.extend(members)
                dataset.direct.append(fixture)
                if len(member_rows) >= INSERT_CHUNK:
                    await flush(conn, chat_rows, member_rows)
                    chat_rows, member_rows = [], []
                del i

            for i in range(args.group_chats):
                members_sample = rng.sample(user_ids, args.group_size)
                chat, members, fixture = build_chat_rows(
                    ChatType.GROUP, members_sample[0], members_sample, f"lt-group-{i}"
                )
                chat_rows.append(chat)
                member_rows.extend(members)
                dataset.group.append(fixture)
                if len(member_rows) >= INSERT_CHUNK:
                    await flush(conn, chat_rows, member_rows)
                    chat_rows, member_rows = [], []

            for i in range(args.supergroups):
                members_sample = rng.sample(user_ids, args.supergroup_size)
                chat, members, fixture = build_chat_rows(
                    ChatType.SUPERGROUP, members_sample[0], members_sample, f"lt-supergroup-{i}"
                )
                chat_rows.append(chat)
                member_rows.extend(members)
                dataset.supergroup.append(fixture)
                await flush(conn, chat_rows, member_rows)
                chat_rows, member_rows = [], []

            for i in range(args.channels):
                members_sample = rng.sample(user_ids, args.channel_size)
                chat, members, fixture = build_chat_rows(
                    ChatType.CHANNEL, members_sample[0], members_sample, f"lt-channel-{i}"
                )
                chat_rows.append(chat)
                member_rows.extend(members)
                dataset.channel.append(fixture)
                await flush(conn, chat_rows, member_rows)
                chat_rows, member_rows = [], []

            await flush(conn, chat_rows, member_rows)
    finally:
        await engine.dispose()

    return dataset


def write_dataset(dataset: Dataset, output: str) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dataset.to_json(), indent=2))

    counts = {
        name: len(getattr(dataset, name))
        for name in ("direct", "group", "supergroup", "channel")
    }
    print(f"dataset: {len(dataset.users)} users, chats {counts} -> {path}")


async def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    dataset = await seed(args)
    write_dataset(dataset, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))


# Referenced so linters keep the import that documents where chat ids come from.
_ = UUID
