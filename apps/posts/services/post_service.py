import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, func, select

from irails.apps.users.models import User
from irails.database import Service

from ..models import Comment, Like, Post, Repost


class PostService(Service):
    @classmethod
    def get_post(cls, post_id: uuid.UUID) -> Post | None:
        return cls.session().get(Post, post_id)

    @classmethod
    def create_post(cls, user_id: uuid.UUID, content: str) -> Post:
        session = cls.session()
        post = Post(user_id=user_id, content=content)
        session.add(post)
        session.commit()
        session.refresh(post)
        return post

    @classmethod
    def list_feed(
        cls,
        page: int,
        limit: int,
        filter_name: str | None,
        query_text: str | None,
    ) -> tuple[list[Post], int]:
        session = cls.session()
        statement = select(Post)
        count_statement = select(func.count()).select_from(Post)

        since = cls._filter_since(filter_name)
        if since is not None:
            statement = statement.where(Post.created_at >= since)
            count_statement = count_statement.where(Post.created_at >= since)

        if query_text:
            search = f"%{query_text}%"
            statement = statement.where(Post.content.ilike(search))
            count_statement = count_statement.where(Post.content.ilike(search))

        total = int(session.execute(count_statement).scalar_one())
        posts = session.execute(
            statement.order_by(desc(Post.created_at)).offset((page - 1) * limit).limit(limit)
        ).scalars().all()
        return posts, total

    @classmethod
    def list_user_posts(cls, user_id: uuid.UUID, page: int, limit: int) -> tuple[list[Post], int]:
        session = cls.session()
        total = int(session.execute(select(func.count()).select_from(Post).where(Post.user_id == user_id)).scalar_one())
        posts = session.execute(
            select(Post)
            .where(Post.user_id == user_id)
            .order_by(desc(Post.created_at))
            .offset((page - 1) * limit)
            .limit(limit)
        ).scalars().all()
        return posts, total

    @classmethod
    def delete_post(cls, post: Post) -> None:
        session = cls.session()
        session.delete(post)
        session.commit()

    @classmethod
    def like_post(cls, user_id: uuid.UUID, post_id: uuid.UUID) -> bool:
        session = cls.session()
        existing = session.execute(select(Like).where(Like.user_id == user_id, Like.post_id == post_id)).scalar_one_or_none()
        if existing:
            return False
        session.add(Like(user_id=user_id, post_id=post_id))
        session.commit()
        return True

    @classmethod
    def unlike_post(cls, user_id: uuid.UUID, post_id: uuid.UUID) -> None:
        session = cls.session()
        like = session.execute(select(Like).where(Like.user_id == user_id, Like.post_id == post_id)).scalar_one_or_none()
        if like:
            session.delete(like)
            session.commit()

    @classmethod
    def repost_post(cls, user_id: uuid.UUID, post_id: uuid.UUID) -> bool:
        session = cls.session()
        existing = session.execute(select(Repost).where(Repost.user_id == user_id, Repost.post_id == post_id)).scalar_one_or_none()
        if existing:
            return False
        session.add(Repost(user_id=user_id, post_id=post_id))
        session.commit()
        return True

    @classmethod
    def unrepost_post(cls, user_id: uuid.UUID, post_id: uuid.UUID) -> None:
        session = cls.session()
        repost = session.execute(select(Repost).where(Repost.user_id == user_id, Repost.post_id == post_id)).scalar_one_or_none()
        if repost:
            session.delete(repost)
            session.commit()

    @classmethod
    def list_comments(cls, post_id: uuid.UUID, page: int, limit: int) -> tuple[list[Comment], int]:
        session = cls.session()
        total = int(session.execute(select(func.count()).select_from(Comment).where(Comment.post_id == post_id)).scalar_one())
        comments = session.execute(
            select(Comment)
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at)
            .offset((page - 1) * limit)
            .limit(limit)
        ).scalars().all()
        return comments, total

    @classmethod
    def create_comment(cls, user_id: uuid.UUID, post_id: uuid.UUID, content: str) -> Comment:
        session = cls.session()
        comment = Comment(user_id=user_id, post_id=post_id, content=content)
        session.add(comment)
        session.commit()
        session.refresh(comment)
        return comment

    @classmethod
    def get_comment(cls, comment_id: uuid.UUID) -> Comment | None:
        return cls.session().get(Comment, comment_id)

    @classmethod
    def delete_comment(cls, comment: Comment) -> None:
        session = cls.session()
        session.delete(comment)
        session.commit()

    @classmethod
    def serialize_post(cls, post: Post, viewer_id: uuid.UUID | None = None) -> dict:
        session = cls.session()
        author = session.get(User, post.user_id)
        likes_count = int(session.execute(select(func.count()).select_from(Like).where(Like.post_id == post.id)).scalar_one())
        reposts_count = int(session.execute(select(func.count()).select_from(Repost).where(Repost.post_id == post.id)).scalar_one())
        comments_count = int(session.execute(select(func.count()).select_from(Comment).where(Comment.post_id == post.id)).scalar_one())
        liked_by_me = False
        reposted_by_me = False
        if viewer_id:
            liked_by_me = session.execute(select(Like).where(Like.post_id == post.id, Like.user_id == viewer_id)).scalar_one_or_none() is not None
            reposted_by_me = session.execute(select(Repost).where(Repost.post_id == post.id, Repost.user_id == viewer_id)).scalar_one_or_none() is not None
        return {
            "id": str(post.id),
            "content": post.content,
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat(),
            "likes_count": likes_count,
            "reposts_count": reposts_count,
            "comments_count": comments_count,
            "liked_by_me": liked_by_me,
            "reposted_by_me": reposted_by_me,
            "user": {
                "id": str(author.id),
                "name": author.name,
                "username": author.username,
                "avatar_url": author.avatar_url,
            },
        }

    @classmethod
    def serialize_comment(cls, comment: Comment) -> dict:
        session = cls.session()
        author = session.get(User, comment.user_id)
        return {
            "id": str(comment.id),
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat(),
            "user": {
                "id": str(author.id),
                "name": author.name,
                "username": author.username,
                "avatar_url": author.avatar_url,
            },
        }

    @staticmethod
    def _filter_since(filter_name: str | None):
        if not filter_name or filter_name == "latest":
            return None

        now = datetime.now(UTC)
        start_of_today = datetime(now.year, now.month, now.day, tzinfo=UTC)
        if filter_name == "today":
            return start_of_today
        if filter_name == "yesterday":
            return start_of_today - timedelta(days=1)
        if filter_name == "this_week":
            return start_of_today - timedelta(days=start_of_today.weekday())
        if filter_name == "last_week":
            return start_of_today - timedelta(days=start_of_today.weekday() + 7)
        if filter_name == "this_month":
            return datetime(now.year, now.month, 1, tzinfo=UTC)
        if filter_name == "this_year":
            return datetime(now.year, 1, 1, tzinfo=UTC)
        return None