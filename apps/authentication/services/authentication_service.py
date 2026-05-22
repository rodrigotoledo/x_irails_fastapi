import uuid

from sqlalchemy import select

from common.auth import create_access_token, create_password_reset_token, hash_password, verify_password
from irails.database import Service
from irails.apps.users.models import User


class AuthenticationService(Service):
    @classmethod
    def get_user_by_email(cls, email: str) -> User | None:
        return cls.session().execute(select(User).where(User.email == email)).scalar_one_or_none()

    @classmethod
    def get_user_by_username(cls, username: str) -> User | None:
        return cls.session().execute(select(User).where(User.username == username)).scalar_one_or_none()

    @classmethod
    def create_user(
        cls,
        name: str,
        username: str,
        email: str,
        password: str,
        avatar_url: str,
        bio: str,
        phone: str,
        instagram: str,
    ) -> tuple[User, str]:
        session = cls.session()
        user = User(
            id=uuid.uuid4(),
            name=name,
            username=username,
            email=email,
            password=hash_password(password),
            avatar_url=avatar_url,
            bio=bio,
            phone=phone,
            instagram=instagram,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user, create_access_token(str(user.id), user.username)

    @classmethod
    def authenticate_user(cls, email: str, password: str) -> tuple[User | None, str | None]:
        user = cls.get_user_by_email(email)
        if not user or not verify_password(password, user.password):
            return None, None
        return user, create_access_token(str(user.id), user.username)

    @classmethod
    def create_reset_token(cls, email: str) -> str | None:
        user = cls.get_user_by_email(email)
        if not user:
            return None
        return create_password_reset_token(str(user.id))

    @classmethod
    def reset_password(cls, token: str, new_password: str) -> bool:
        from common.auth import decode_token
        import jwt

        try:
            payload = decode_token(token)
        except jwt.PyJWTError:
            return False

        if payload.get("scope") != "password_reset":
            return False

        user_id = payload.get("sub")
        if not user_id:
            return False

        session = cls.session()
        user = session.get(User, uuid.UUID(user_id))
        if not user:
            return False

        user.password = hash_password(new_password)
        session.add(user)
        session.commit()
        return True
