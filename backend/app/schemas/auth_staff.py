"""Pydantic models for operator auth APIs."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=2048)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=2048)


class StaffTokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class StaffMeResponse(BaseModel):
    id: int
    email: str
    can_moderate: bool
    can_run_pipeline: bool
