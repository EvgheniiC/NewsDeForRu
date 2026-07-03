"""Request/response payloads for in-app user feedback."""

from __future__ import annotations

from enum import StrEnum

from pydantic import AliasChoices, BaseModel, Field, field_validator


class FeedbackCategory(StrEnum):
    bug = "bug"
    suggestion = "suggestion"
    content = "content"
    other = "other"


_CATEGORY_LABELS_RU: dict[FeedbackCategory, str] = {
    FeedbackCategory.bug: "Ошибка / проблема",
    FeedbackCategory.suggestion: "Предложение",
    FeedbackCategory.content: "Вопрос по новости",
    FeedbackCategory.other: "Другое",
}


def feedback_category_label_ru(category: FeedbackCategory) -> str:
    return _CATEGORY_LABELS_RU[category]


class FeedbackSubmitRequest(BaseModel):
    category: FeedbackCategory
    message: str = Field(..., min_length=10, max_length=4000)
    contact_email: str | None = Field(None, max_length=254)
    page_url: str | None = Field(None, max_length=2048)
    platform: str | None = Field(None, max_length=64)
    app_version: str | None = Field(None, max_length=32)
    website: str | None = Field(
        None,
        max_length=256,
        description="Honeypot field; must stay empty for legitimate submissions.",
    )

    model_config = {"extra": "forbid"}

    @field_validator("contact_email")
    @classmethod
    def normalize_contact_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized: str = value.strip().lower()
        return normalized if normalized else None


class FeedbackSubmitResponse(BaseModel):
    detail: str = Field(
        ...,
        validation_alias=AliasChoices("detail", "message"),
    )

    model_config = {"populate_by_name": True}
