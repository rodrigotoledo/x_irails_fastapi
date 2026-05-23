import uuid
from typing import Annotated

from fastapi import Header, Query
from pydantic import BaseModel, Field

from common.auth import get_current_user
from common.responses import data_response, error_response, no_content_response, paginated_response
from irails import BaseController, api, route
from irails.database import Service

from ..services import PostService


class CreatePostPayload(BaseModel):
    content: str = Field(min_length=1, max_length=280)


class CreateCommentPayload(BaseModel):
    content: str = Field(min_length=1, max_length=280)


@route(path="/api/{controller}", auth="none")
class PostsController(BaseController):
    @api.get("/")
    def feed(
        self,
        page: Annotated[int, Query(ge=1)] = 1,
        limit: Annotated[int, Query(ge=1, le=200)] = 20,
        filter: str | None = None,
        q: str | None = None,
    ):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        posts, total = PostService.list_feed(page, limit, filter, q)
        data = [PostService.serialize_post(post, viewer.id if viewer else None) for post in posts]
        return paginated_response(data, page, limit, total)

    @api.post("/")
    def create(self, payload: CreatePostPayload, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        if not viewer:
            return error_response("UNAUTHORIZED", "Authentication required", 401)
        normalized_key = (idempotency_key or "").strip()
        if not normalized_key:
            return error_response("IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key header is required", 400)
        if len(normalized_key) > 128:
            return error_response("VALIDATION_ERROR", "Idempotency-Key must be 128 characters or fewer", 422)
        post = PostService.create_post(viewer.id, payload.content, normalized_key)
        return data_response(PostService.serialize_post(post, viewer.id), status_code=201)

    @api.get("/{post_id}")
    def show(self, post_id: str):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        post = PostService.get_post(uuid.UUID(post_id))
        if not post:
            return error_response("NOT_FOUND", "Post not found", 404)
        return data_response(PostService.serialize_post(post, viewer.id if viewer else None))

    @api.delete("/{post_id}")
    def destroy(self, post_id: str):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        if not viewer:
            return error_response("UNAUTHORIZED", "Authentication required", 401)
        post = PostService.get_post(uuid.UUID(post_id))
        if not post:
            return error_response("NOT_FOUND", "Post not found", 404)
        if post.user_id != viewer.id:
            return error_response("FORBIDDEN", "You cannot delete this post", 403)
        PostService.delete_post(post)
        return no_content_response()

    @api.post("/{post_id}/like")
    def like(self, post_id: str):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        if not viewer:
            return error_response("UNAUTHORIZED", "Authentication required", 401)
        post = PostService.get_post(uuid.UUID(post_id))
        if not post:
            return error_response("NOT_FOUND", "Post not found", 404)
        if post.user_id == viewer.id:
            return error_response("FORBIDDEN", "You cannot like your own post", 403)
        PostService.like_post(viewer.id, post.id)
        return data_response(PostService.serialize_post(post, viewer.id))

    @api.delete("/{post_id}/like")
    def unlike(self, post_id: str):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        if not viewer:
            return error_response("UNAUTHORIZED", "Authentication required", 401)
        post = PostService.get_post(uuid.UUID(post_id))
        if not post:
            return error_response("NOT_FOUND", "Post not found", 404)
        PostService.unlike_post(viewer.id, post.id)
        return data_response(PostService.serialize_post(post, viewer.id))

    @api.post("/{post_id}/repost")
    def repost(self, post_id: str):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        if not viewer:
            return error_response("UNAUTHORIZED", "Authentication required", 401)
        post = PostService.get_post(uuid.UUID(post_id))
        if not post:
            return error_response("NOT_FOUND", "Post not found", 404)
        if post.user_id == viewer.id:
            return error_response("FORBIDDEN", "You cannot repost your own post", 403)
        PostService.repost_post(viewer.id, post.id)
        return data_response(PostService.serialize_post(post, viewer.id))

    @api.delete("/{post_id}/repost")
    def unrepost(self, post_id: str):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        if not viewer:
            return error_response("UNAUTHORIZED", "Authentication required", 401)
        post = PostService.get_post(uuid.UUID(post_id))
        if not post:
            return error_response("NOT_FOUND", "Post not found", 404)
        PostService.unrepost_post(viewer.id, post.id)
        return data_response(PostService.serialize_post(post, viewer.id))

    @api.get("/{post_id}/comments")
    def comments(
        self,
        post_id: str,
        page: Annotated[int, Query(ge=1)] = 1,
        limit: Annotated[int, Query(ge=1, le=50)] = 20,
    ):
        post = PostService.get_post(uuid.UUID(post_id))
        if not post:
            return error_response("NOT_FOUND", "Post not found", 404)
        comments, total = PostService.list_comments(post.id, page, limit)
        data = [PostService.serialize_comment(comment) for comment in comments]
        return paginated_response(data, page, limit, total)

    @api.post("/{post_id}/comments")
    def create_comment(self, post_id: str, payload: CreateCommentPayload):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        if not viewer:
            return error_response("UNAUTHORIZED", "Authentication required", 401)
        post = PostService.get_post(uuid.UUID(post_id))
        if not post:
            return error_response("NOT_FOUND", "Post not found", 404)
        comment = PostService.create_comment(viewer.id, post.id, payload.content)
        return data_response(PostService.serialize_comment(comment), status_code=201)

    @api.delete("/{post_id}/comments/{comment_id}")
    def delete_comment(self, post_id: str, comment_id: str):
        session = Service.session()
        viewer = get_current_user(self.request, session)
        if not viewer:
            return error_response("UNAUTHORIZED", "Authentication required", 401)
        post = PostService.get_post(uuid.UUID(post_id))
        if not post:
            return error_response("NOT_FOUND", "Post not found", 404)
        comment = PostService.get_comment(uuid.UUID(comment_id))
        if not comment or comment.post_id != post.id:
            return error_response("NOT_FOUND", "Comment not found", 404)
        if comment.user_id != viewer.id:
            return error_response("FORBIDDEN", "You cannot delete this comment", 403)
        PostService.delete_comment(comment)
        return no_content_response()
