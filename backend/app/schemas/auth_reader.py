"""Schemas for reader (app user) authentication."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ReaderRegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class ReaderLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email_login(cls, value: str) -> str:
        return value.strip().lower()


class ReaderRefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=2048)


class ReaderLogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=2048)


class ReaderTokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ReaderMeResponse(BaseModel):
    id: int
    email: str
