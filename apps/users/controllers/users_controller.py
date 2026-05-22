from typing import Annotated

from fastapi import File, Query, UploadFile
from pydantic import BaseModel, Field

from common.auth import get_current_user
from common.responses import data_response, error_response, no_content_response, paginated_response
from common.uploads import save_avatar_upload
from irails import BaseController, api, route
from irails.database import Service

from irails.apps.posts.services import PostService

from ..services import UserService


class UpdateProfilePayload(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    bio: str | None = Field(default=None, max_length=160)
    avatar_url: str | None = Field(default=None, max_length=2048)
    phone: str | None = Field(default=None, max_length=32)
    instagram: str | None = Field(default=None, max_length=50)


@route(path="/api/{controller}", auth="none")
class UsersController(BaseController):
    @api.get("/me")
    def me(self):
        session = Service.session()
        user = get_current_user(self.request, session)
        if not user:
            return error_response("UNAUTHORIZED", "Authentication required", 401)
        return data_response(UserService.serialize_user(user, user.id))

    @api.patch("/me")
    def update_me(self, payload: UpdateProfilePayload):
        session = Service.session()
        user = get_current_user(self.request, session)
        if not user:
            return error_response("UNAUTHORIZED", "Authentication required", 401)
        user = UserService.update_profile(user, payload.name, payload.bio, payload.avatar_url, payload.phone, payload.instagram)
        return data_response(UserService.serialize_user(user, user.id))

    @api.patch("/me/avatar")
    def update_avatar(self, avatar: UploadFile = File(...)):
        session = Service.session()
        user = get_current_user(self.request, session)
        if not user:
            return error_response("UNAUTHORIZED", "Authentication required", 401)
        try:
            avatar_url = save_avatar_upload(avatar)
        except ValueError as exc:
            return error_response("VALIDATION_ERROR", str(exc), 422)
        user = UserService.update_profile(user, None, None, avatar_url, None, None)
        return data_response(UserService.serialize_user(user, user.id))

    @api.get("/{username}")
    def profile(self, username: str):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        user = UserService.get_by_username(username)
        if not user:
            return error_response("NOT_FOUND", "User not found", 404)
        return data_response(UserService.serialize_user(user, viewer.id if viewer else None))

    @api.get("/{username}/posts")
    def user_posts(
        self,
        username: str,
        page: Annotated[int, Query(ge=1)] = 1,
        limit: Annotated[int, Query(ge=1, le=50)] = 20,
    ):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        user = UserService.get_by_username(username)
        if not user:
            return error_response("NOT_FOUND", "User not found", 404)
        posts, total = PostService.list_user_posts(user.id, page, limit)
        data = [PostService.serialize_post(post, viewer.id if viewer else None) for post in posts]
        return paginated_response(data, page, limit, total)

    @api.post("/{username}/follow")
    def follow(self, username: str):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        if not viewer:
            return error_response("UNAUTHORIZED", "Authentication required", 401)
        user = UserService.get_by_username(username)
        if not user:
            return error_response("NOT_FOUND", "User not found", 404)
        if not UserService.follow_user(viewer.id, user.id):
            return error_response("FORBIDDEN", "Unable to follow user", 403)
        return data_response(UserService.serialize_user(user, viewer.id))

    @api.delete("/{username}/follow")
    def unfollow(self, username: str):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        if not viewer:
            return error_response("UNAUTHORIZED", "Authentication required", 401)
        user = UserService.get_by_username(username)
        if not user:
            return error_response("NOT_FOUND", "User not found", 404)
        UserService.unfollow_user(viewer.id, user.id)
        return no_content_response()

    @api.get("/{username}/followers")
    def followers(
        self,
        username: str,
        page: Annotated[int, Query(ge=1)] = 1,
        limit: Annotated[int, Query(ge=1, le=50)] = 20,
    ):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        user = UserService.get_by_username(username)
        if not user:
            return error_response("NOT_FOUND", "User not found", 404)
        followers, total = UserService.list_followers(user.id, page, limit)
        data = [UserService.serialize_user(follower, viewer.id if viewer else None) for follower in followers]
        return paginated_response(data, page, limit, total)

    @api.get("/{username}/following")
    def following(
        self,
        username: str,
        page: Annotated[int, Query(ge=1)] = 1,
        limit: Annotated[int, Query(ge=1, le=50)] = 20,
    ):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        user = UserService.get_by_username(username)
        if not user:
            return error_response("NOT_FOUND", "User not found", 404)
        following, total = UserService.list_following(user.id, page, limit)
        data = [UserService.serialize_user(item, viewer.id if viewer else None) for item in following]
        return paginated_response(data, page, limit, total)
