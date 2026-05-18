from pydantic import BaseModel, Field


class OAuthCallbackRequest(BaseModel):
    provider: str = Field(min_length=1)
    code: str = Field(min_length=1)
    state: str = Field(min_length=1)
