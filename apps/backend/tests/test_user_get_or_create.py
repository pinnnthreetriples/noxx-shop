"""Race-safety of get-or-create-user (Sentry: duplicate key on ix_users_telegram_id).

Two concurrent first-time requests for the same telegram_id both miss the SELECT
and both INSERT; one loses on the unique index. The repository must swallow that
IntegrityError and return the row the winner committed — never a 500."""
from sqlalchemy import func, select

from app.modules.users.models import User
from app.modules.users.repository import UserRepository


async def test_get_or_create_is_idempotent_no_duplicate(db_session):
    repo = UserRepository(db_session)
    first = await repo.get_or_create_by_telegram_id(111, {"username": "a"})
    await db_session.commit()

    second = await repo.get_or_create_by_telegram_id(111, {"username": "changed"})
    assert second.id == first.id
    assert second.username == "a"  # existing user is not mutated

    total = await db_session.scalar(
        select(func.count()).select_from(User).where(User.telegram_id == 111)
    )
    assert total == 1


async def test_get_or_create_recovers_from_concurrent_insert(db_session):
    # The race winner has already committed telegram_id=222.
    db_session.add(User(telegram_id=222, username="winner"))
    await db_session.commit()

    repo = UserRepository(db_session)
    real = repo.get_by_telegram_id
    calls = {"n": 0}

    async def flaky(telegram_id):
        # First existence check misses (as if the winner committed just after we
        # looked), so we attempt the INSERT and hit the unique constraint.
        calls["n"] += 1
        return None if calls["n"] == 1 else await real(telegram_id)

    repo.get_by_telegram_id = flaky

    user = await repo.get_or_create_by_telegram_id(222, {"username": "loser"})
    assert user.telegram_id == 222
    assert user.username == "winner"  # got the committed winner, not a duplicate

    total = await db_session.scalar(
        select(func.count()).select_from(User).where(User.telegram_id == 222)
    )
    assert total == 1
