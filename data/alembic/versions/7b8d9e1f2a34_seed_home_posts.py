"""seed_home_posts

Revision ID: 7b8d9e1f2a34
Revises: 2c9d8f4a1b77
Create Date: 2026-05-23 00:30:00.000000

"""
from datetime import UTC, datetime, timedelta
import random
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '7b8d9e1f2a34'
down_revision = '2c9d8f4a1b77'
branch_labels = None
depends_on = None


SEED_POST_COUNT = 200
SEED_NAMESPACE = 'home-seed'


def upgrade() -> None:
    now = datetime.now(UTC)
    started_at = now - timedelta(days=7)
    rng = random.Random(20260523)

    users = [
        {
            'id': uuid.uuid5(uuid.NAMESPACE_DNS, f'{SEED_NAMESPACE}-user-{index}'),
            'name': name,
            'username': username,
            'email': f'{username}@seed.local',
            'password': '$2b$12$C6UzMDM.H6dfI/f/IKcEe.6fkmZDl7VbEt6NgY3lhr22Y4cM9uW8K',
            'avatar_url': '',
            'bio': 'Seed account for the home timeline.',
            'phone': f'+15550120{index:02d}',
            'instagram': username,
            'created_at': started_at,
            'updated_at': started_at,
        }
        for index, (name, username) in enumerate(
            [
                ('Ava Morgan', 'avamorgan'),
                ('Noah Reed', 'noahreed'),
                ('Mia Chen', 'miachen'),
                ('Leo Santos', 'leosantos'),
                ('Ivy Brooks', 'ivybrooks'),
                ('Owen Patel', 'owenpatel'),
                ('Zoe Rivera', 'zoerivera'),
                ('Eli Walker', 'eliwalker'),
            ],
            start=1,
        )
    ]

    user_rows = sa.table(
        'users',
        sa.column('id', postgresql.UUID(as_uuid=True)),
        sa.column('name', sa.String),
        sa.column('username', sa.String),
        sa.column('email', sa.String),
        sa.column('password', sa.String),
        sa.column('avatar_url', sa.Text),
        sa.column('bio', sa.Text),
        sa.column('phone', sa.String),
        sa.column('instagram', sa.String),
        sa.column('created_at', sa.DateTime(timezone=True)),
        sa.column('updated_at', sa.DateTime(timezone=True)),
    )
    op.bulk_insert(user_rows, users)

    subjects = [
        'product polish',
        'timeline performance',
        'design systems',
        'API contracts',
        'database migrations',
        'release notes',
        'search filters',
        'observability',
        'auth flows',
        'mobile layout',
    ]
    verbs = [
        'tightened up',
        'tested',
        'rewrote',
        'reviewed',
        'shipped',
        'debugged',
        'documented',
        'benchmarked',
    ]
    endings = [
        'and the result feels much cleaner.',
        'before the next round of feedback.',
        'with a focus on repeatable behavior.',
        'so the team can move faster tomorrow.',
        'without changing the public interface.',
        'and found a couple of useful edge cases.',
    ]

    posts = []
    total_seconds = int((now - started_at).total_seconds())
    for index in range(SEED_POST_COUNT):
        created_at = started_at + timedelta(seconds=rng.randrange(total_seconds + 1))
        user = users[index % len(users)]
        content = (
            f'{verbs[index % len(verbs)].capitalize()} {subjects[rng.randrange(len(subjects))]} '
            f'{endings[rng.randrange(len(endings))]}'
        )
        posts.append(
            {
                'id': uuid.uuid5(uuid.NAMESPACE_DNS, f'{SEED_NAMESPACE}-post-{index}'),
                'user_id': user['id'],
                'idempotency_key': f'{SEED_NAMESPACE}-post-{index}',
                'content': content,
                'created_at': created_at,
                'updated_at': created_at,
            }
        )

    post_rows = sa.table(
        'posts',
        sa.column('id', postgresql.UUID(as_uuid=True)),
        sa.column('user_id', postgresql.UUID(as_uuid=True)),
        sa.column('idempotency_key', sa.String),
        sa.column('content', sa.Text),
        sa.column('created_at', sa.DateTime(timezone=True)),
        sa.column('updated_at', sa.DateTime(timezone=True)),
    )
    op.bulk_insert(post_rows, sorted(posts, key=lambda row: row['created_at']))


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("DELETE FROM posts WHERE idempotency_key LIKE :prefix"),
        {'prefix': f'{SEED_NAMESPACE}-post-%'},
    )
    bind.execute(
        sa.text("DELETE FROM users WHERE email LIKE :suffix"),
        {'suffix': '%@seed.local'},
    )
