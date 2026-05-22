import uuid

from sqlalchemy import func, select

from irails.apps.posts.models import Post
from irails.database import Service

from ..models import Follow, User


class UserService(Service):
    @classmethod
    def get_by_id(cls, user_id: uuid.UUID) -> User | None:
        return cls.session().get(User, user_id)

    @classmethod
    def get_by_username(cls, username: str) -> User | None:
        return cls.session().execute(select(User).where(User.username == username)).scalar_one_or_none()

    @classmethod
    def get_counts(cls, user_id: uuid.UUID) -> dict[str, int]:
        session = cls.session()
        posts_count = session.execute(select(func.count()).select_from(Post).where(Post.user_id == user_id)).scalar_one()
        followers_count = session.execute(select(func.count()).select_from(Follow).where(Follow.following_id == user_id)).scalar_one()
        following_count = session.execute(select(func.count()).select_from(Follow).where(Follow.follower_id == user_id)).scalar_one()
        return {
            "posts_count": int(posts_count),
            "followers_count": int(followers_count),
            "following_count": int(following_count),
        }

    @classmethod
    def is_following(cls, follower_id: uuid.UUID | None, following_id: uuid.UUID) -> bool:
        if follower_id is None:
            return False
        record = cls.session().execute(
            select(Follow).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id,
            )
        ).scalar_one_or_none()
        return record is not None

    @classmethod
    def serialize_user(cls, user: User, viewer_id: uuid.UUID | None = None) -> dict:
        counts = cls.get_counts(user.id)
        return {
            "id": str(user.id),
            "name": user.name,
            "username": user.username,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "phone": user.phone,
            "instagram": user.instagram,
            "followers_count": counts["followers_count"],
            "following_count": counts["following_count"],
            "posts_count": counts["posts_count"],
            "is_following": cls.is_following(viewer_id, user.id),
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }

    @classmethod
    def update_profile(
        cls,
        user: User,
        name: str | None,
        bio: str | None,
        avatar_url: str | None,
        phone: str | None,
        instagram: str | None,
    ) -> User:
        if name is not None:
            user.name = name
        if bio is not None:
            user.bio = bio
        if avatar_url is not None:
            user.avatar_url = avatar_url
        if phone is not None:
            user.phone = phone
        if instagram is not None:
            user.instagram = instagram
        session = cls.session()
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @classmethod
    def follow_user(cls, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        if follower_id == following_id:
            return False
        if cls.is_following(follower_id, following_id):
            return False
        session = cls.session()
        session.add(Follow(follower_id=follower_id, following_id=following_id))
        session.commit()
        return True

    @classmethod
    def unfollow_user(cls, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        session = cls.session()
        relation = session.execute(
            select(Follow).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id,
            )
        ).scalar_one_or_none()
        if not relation:
            return False
        session.delete(relation)
        session.commit()
        return True

    @classmethod
    def list_followers(cls, user_id: uuid.UUID, page: int, limit: int) -> tuple[list[User], int]:
        session = cls.session()
        total = session.execute(select(func.count()).select_from(Follow).where(Follow.following_id == user_id)).scalar_one()
        users = session.execute(
            select(User)
            .join(Follow, Follow.follower_id == User.id)
            .where(Follow.following_id == user_id)
            .offset((page - 1) * limit)
            .limit(limit)
        ).scalars().all()
        return users, int(total)

    @classmethod
    def list_following(cls, user_id: uuid.UUID, page: int, limit: int) -> tuple[list[User], int]:
        session = cls.session()
        total = session.execute(select(func.count()).select_from(Follow).where(Follow.follower_id == user_id)).scalar_one()
        users = session.execute(
            select(User)
            .join(Follow, Follow.following_id == User.id)
            .where(Follow.follower_id == user_id)
            .offset((page - 1) * limit)
            .limit(limit)
        ).scalars().all()
        return users, int(total)
