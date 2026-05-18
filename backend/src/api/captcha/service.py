import base64
import io
import logging
import random
import secrets
import string
import uuid

from fastapi import HTTPException
from PIL import Image, ImageDraw, ImageFont

from agent.config import settings
from api.captcha.schemas import (
    ImageCaptchaData,
    SlidePuzzleData,
    SlideVerifyRequest,
    SlideVerifyResponse,
)
from core.store import KeyValueStore

logger = logging.getLogger(__name__)


def _img_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


async def generate_slide_puzzle(session_id: str, store: KeyValueStore) -> SlidePuzzleData:
    width, height = 300, 160
    slider_w, slider_h = 50, 40
    y = random.randint(20, height - slider_h - 20)
    gap_x = random.randint(50, width - slider_w - 50)

    bg = Image.new("RGBA", (width, height), (60, 70, 90, 255))
    draw = ImageDraw.Draw(bg)
    draw.rectangle([gap_x, y, gap_x + slider_w, y + slider_h], fill=(45, 55, 72, 255))
    for _ in range(40):
        rx = random.randint(0, width - 1)
        ry = random.randint(0, height - 1)
        draw.point((rx, ry), fill=(80, 90, 110, 255))

    slider = Image.new("RGBA", (slider_w, slider_h), (90, 130, 200, 255))
    slider_draw = ImageDraw.Draw(slider)
    for i in range(3):
        slider_draw.line([(5, 8 + i * 10), (slider_w - 5, 8 + i * 10)], fill=(60, 80, 140, 255))

    bg_b64 = _img_to_base64(bg)
    slider_b64 = _img_to_base64(slider)

    await store.set(f"captcha:slide:{session_id}", f"{gap_x}:{y}", ttl=settings.CAPTCHA_EXPIRE)

    logger.info("Slide captcha for %s: x=%d, y=%d (dev mode)", session_id[:8], gap_x, y)
    return SlidePuzzleData(bgImage=bg_b64, slideImage=slider_b64, y=y)


async def verify_slide(req: SlideVerifyRequest, session_id: str, store: KeyValueStore) -> SlideVerifyResponse:
    data = await store.get(f"captcha:slide:{session_id}")
    if not data:
        raise HTTPException(status_code=400, detail="Captcha expired, please retry")

    try:
        correct_x_str, _ = data.split(":", 1)
        correct_x = int(correct_x_str)
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid captcha session")

    await store.delete(f"captcha:slide:{session_id}")

    if abs(req.distance - correct_x) <= settings.SLIDE_THRESHOLD:
        ticket = str(uuid.uuid4())
        randstr = secrets.token_hex(4)
        await store.set(f"captcha:ticket:{ticket}", randstr, ttl=settings.CAPTCHA_EXPIRE)
        return SlideVerifyResponse(success=True, ticket=ticket, randstr=randstr)
    else:
        return SlideVerifyResponse(success=False)


async def generate_image_captcha(store: KeyValueStore) -> ImageCaptchaData:
    width, height = 160, 60
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    key = str(uuid.uuid4())

    img = Image.new("RGB", (width, height), (240, 242, 245))
    draw = ImageDraw.Draw(img)

    for _ in range(30):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(random.randint(0, 150), random.randint(0, 150), random.randint(0, 150)))

    for _ in range(3):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(100, 120, 160), width=1)

    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except OSError:
        font = ImageFont.load_default()

    for i, ch in enumerate(code):
        x = 15 + i * 35 + random.randint(-3, 3)
        y = random.randint(5, 15)
        color = (random.randint(0, 80), random.randint(0, 80), random.randint(0, 140))
        draw.text((x, y), ch, fill=color, font=font)

    await store.set(f"captcha:image:{key}", code.lower(), ttl=settings.CAPTCHA_EXPIRE)

    logger.info("Image captcha code for key %s: %s (dev mode)", key, code)
    return ImageCaptchaData(image=_img_to_base64(img), key=key)


async def verify_image(key: str, code: str, store: KeyValueStore) -> bool:
    stored = await store.get(f"captcha:image:{key}")
    if not stored:
        return False
    if stored != code.strip().lower():
        return False
    await store.delete(f"captcha:image:{key}")
    return True
