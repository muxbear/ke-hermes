from pydantic import BaseModel, Field


class SlidePuzzleData(BaseModel):
    bgImage: str
    slideImage: str
    y: int
    sessionId: str


class SlideVerifyRequest(BaseModel):
    sessionId: str
    distance: int
    track: list[int] = Field(default_factory=list)
    ticket: str | None = None


class SlideVerifyResponse(BaseModel):
    success: bool
    ticket: str | None = None
    randstr: str | None = None


class ImageCaptchaData(BaseModel):
    image: str
    key: str


class ImageVerifyRequest(BaseModel):
    key: str
    code: str
