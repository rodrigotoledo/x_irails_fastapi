from fastapi import File, Form, UploadFile
from pydantic import BaseModel, Field

from common.auth import blacklist_token, get_token_from_request
from common.responses import data_response, error_response
from common.uploads import save_avatar_upload
from irails import BaseController, api, route

from ..services import AuthenticationService


class SignInPayload(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class ForgotPasswordPayload(BaseModel):
    email: str = Field(min_length=5, max_length=255)


class ResetPasswordPayload(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


@route(path="/api/{controller}", auth="none")
class AuthController(BaseController):
    @api.post("/signup")
    def signup(
        self,
        name: str = Form(..., min_length=1, max_length=100),
        username: str = Form(..., min_length=3, max_length=50),
        email: str = Form(..., min_length=5, max_length=255),
        password: str = Form(..., min_length=8, max_length=128),
        bio: str = Form(..., min_length=1, max_length=160),
        phone: str = Form(..., min_length=1, max_length=32),
        instagram: str = Form(..., min_length=1, max_length=50),
        avatar: UploadFile = File(...),
    ):
        if "@" not in email:
            return error_response("VALIDATION_ERROR", "Invalid email address", 422)
        if AuthenticationService.get_user_by_email(email):
            return error_response("EMAIL_TAKEN", "Email is already in use", 409)
        if AuthenticationService.get_user_by_username(username):
            return error_response("USERNAME_TAKEN", "Username is already in use", 409)

        try:
            avatar_url = save_avatar_upload(avatar)
        except ValueError as exc:
            return error_response("VALIDATION_ERROR", str(exc), 422)

        user, token = AuthenticationService.create_user(
            name=name,
            username=username,
            email=email,
            password=password,
            avatar_url=avatar_url,
            bio=bio,
            phone=phone,
            instagram=instagram,
        )
        return data_response(
            {
                "token": token,
                "user": {
                    "id": str(user.id),
                    "name": user.name,
                    "username": user.username,
                    "email": user.email,
                    "avatar_url": user.avatar_url,
                    "bio": user.bio,
                    "phone": user.phone,
                    "instagram": user.instagram,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                },
            },
            status_code=201,
        )

    @api.post("/signin")
    def signin(self, payload: SignInPayload):
        if "@" not in payload.email:
            return error_response("VALIDATION_ERROR", "Invalid email address", 422)
        user, token = AuthenticationService.authenticate_user(payload.email, payload.password)
        if not user or not token:
            return error_response("UNAUTHORIZED", "Invalid credentials", 401)

        return data_response(
            {
                "token": token,
                "user": {
                    "id": str(user.id),
                    "name": user.name,
                    "username": user.username,
                    "email": user.email,
                    "avatar_url": user.avatar_url,
                    "bio": user.bio,
                    "phone": user.phone,
                    "instagram": user.instagram,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                },
            }
        )

    @api.post("/signout")
    def signout(self):
        token = get_token_from_request(self.request)
        if not token:
            return error_response("UNAUTHORIZED", "Authentication required", 401)
        blacklist_token(token)
        return data_response({"message": "Signed out successfully"})

    @api.post("/forgot-password")
    def forgot_password(self, payload: ForgotPasswordPayload):
        if "@" not in payload.email:
            return error_response("VALIDATION_ERROR", "Invalid email address", 422)
        reset_token = AuthenticationService.create_reset_token(payload.email)
        data = {"message": "If the email exists, a reset link has been generated"}
        if reset_token:
            data["reset_token"] = reset_token
        return data_response(data)

    @api.post("/reset-password")
    def reset_password(self, payload: ResetPasswordPayload):
        if not AuthenticationService.reset_password(payload.token, payload.password):
            return error_response("VALIDATION_ERROR", "Invalid or expired reset token", 422)
        return data_response({"message": "Password reset successfully"})
