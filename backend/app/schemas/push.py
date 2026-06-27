from typing import Literal

from pydantic import BaseModel, Field


class PushSubscribeRequest(BaseModel):
    device_token: str = Field(min_length=20, max_length=512)
    platform: Literal["android"] = "android"


class PushUnsubscribeRequest(BaseModel):
    device_token: str = Field(min_length=20, max_length=512)


class PushSubscriptionResponse(BaseModel):
    subscribed: bool
    topic: str
