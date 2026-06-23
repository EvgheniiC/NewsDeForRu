"""Schemas for unified app authentication."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email_login(cls, value: str) -> str:
        return value.strip().lower()


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=2048)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=2048)


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    email: str
    role: str
    can_moderate: bool
    can_run_pipeline: bool


class ForgotPasswordRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class ForgotPasswordResponse(BaseModel):
    detail: str
    dev_reset_link: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10, max_length=2048)
    new_password: str = Field(min_length=8, max_length=256)


class ResetPasswordResponse(BaseModel):
    detail: str


class RegisterResponse(BaseModel):
    detail: str
    dev_verification_link: str | None = None


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=10, max_length=2048)


class ResendVerificationRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()
