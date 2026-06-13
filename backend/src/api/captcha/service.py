import base64
import io
import logging
import random
import secrets
import string
import uuid
from typing import cast

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


def _jigsaw_cutout_path(w: int, h: int, tab_side: str = "right") -> list[tuple[int, int]]:
    """Generate a puzzle-piece cutout polygon path."""
    tw, th = 10, 10  # tab size
    points: list[tuple[int, int]] = []
    # Top-left corner
    points.append((0, 0))
    # Top edge: go right with optional tab
    mid_top = w // 2
    if tab_side in ("top", "both"):
        points.append((mid_top - tw, 0))
        points.append((mid_top - tw // 2, -th))
        points.append((mid_top + tw // 2, -th))
        points.append((mid_top + tw, 0))
    # Top-right corner
    points.append((w, 0))
    # Right edge: go down
    points.append((w, h))
    # Bottom edge: go left
    points.append((0, h))
    # Left edge: go up
    points.append((0, 0))
    return points


def _draw_puzzle_bg(
    width: int, height: int, gap_x: int, gap_y: int, slider_w: int, slider_h: int
) -> Image.Image:
    """Draw a visually appealing puzzle background with a cutout."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Sky gradient (top half)
    for i in range(height // 2):
        r = 180 + i * 40 // (height // 2)
        g = 200 + i * 30 // (height // 2)
        b = 240 - i * 30 // (height // 2)
        draw.line([(0, i), (width, i)], fill=(r, g, b, 255))

    # Ground / landscape
    ground_y = height // 2 + 10
    for i in range(ground_y, height):
        r = 140 + (i - ground_y) * 20 // (height - ground_y)
        g = 180 + (i - ground_y) * 20 // (height - ground_y)
        b = 140 + (i - ground_y) * 30 // (height - ground_y)
        draw.line([(0, i), (width, i)], fill=(r, g, b, 255))

    # Mountains / hills
    hill_color = (100, 150, 100, 255)
    hill_points = [
        (0, ground_y),
        (60, ground_y - 45),
        (130, ground_y - 20),
        (200, ground_y - 55),
        (260, ground_y - 25),
        (width, ground_y - 35),
        (width, ground_y),
    ]
    draw.polygon(hill_points, fill=hill_color)
    hill_color2 = (80, 140, 80, 255)
    hill_points2 = [
        (0, ground_y + 5),
        (50, ground_y - 30),
        (100, ground_y - 10),
        (170, ground_y - 45),
        (230, ground_y - 15),
        (width, ground_y - 20),
        (width, ground_y + 5),
    ]
    draw.polygon(hill_points2, fill=hill_color2)

    # Sun
    sun_cx, sun_cy, sun_r = 230, 50, 22
    draw.ellipse(
        [sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r],
        fill=(255, 240, 180, 255),
    )

    # Clouds
    for cx, cy, cw in [(50, 35, 35), (150, 25, 28), (100, 55, 22)]:
        for dx in range(-cw, cw + 1, 8):
            for dy in range(-8, 9, 8):
                dr = (dx * dx + dy * dy) ** 0.5
                if dr < cw:
                    px, py = cx + dx, cy + dy
                    if 0 <= px < width and 0 <= py < height:
                        alpha = max(0, int(180 * (1 - dr / cw)))
                        if alpha > 0:
                            r, g, b, _a = cast(tuple[int, int, int, int], img.getpixel((px, py)))
                            blend_r = int(r + (255 - r) * alpha / 255 * 0.6)
                            blend_g = int(g + (255 - g) * alpha / 255 * 0.6)
                            blend_b = int(b + (255 - b) * alpha / 255 * 0.6)
                            draw.point((px, py), fill=(blend_r, blend_g, blend_b, 255))

    # Cutout — draw the missing piece area in dark overlay
    cutout_pts = [
        (gap_x, gap_y),
        (gap_x + slider_w, gap_y),
        (gap_x + slider_w, gap_y + slider_h),
        (gap_x, gap_y + slider_h),
    ]
    # Slightly darker overlay to indicate where the piece belongs
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [gap_x, gap_y, gap_x + slider_w, gap_y + slider_h],
        fill=(0, 0, 0, 90),
    )
    # White dashed border around the cutout
    dash_len = 4
    for side in range(4):
        if side == 0:  # top
            x1, y1, x2, y2 = gap_x, gap_y, gap_x + slider_w, gap_y
        elif side == 1:  # right
            x1, y1, x2, y2 = gap_x + slider_w, gap_y, gap_x + slider_w, gap_y + slider_h
        elif side == 2:  # bottom
            x1, y1, x2, y2 = gap_x + slider_w, gap_y + slider_h, gap_x, gap_y + slider_h
        else:  # left
            x1, y1, x2, y2 = gap_x, gap_y + slider_h, gap_x, gap_y

        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        steps = int(length / dash_len / 2)
        if steps < 1:
            steps = 1
        for s in range(steps):
            if s % 2 == 0:
                t0 = s / steps
                t1 = (s + 1) / steps
                sx1 = int(x1 + (x2 - x1) * t0)
                sy1 = int(y1 + (y2 - y1) * t0)
                sx2 = int(x1 + (x2 - x1) * t1)
                sy2 = int(y1 + (y2 - y1) * t1)
                overlay_draw.line([(sx1, sy1), (sx2, sy2)], fill=(255, 255, 255, 150), width=1)

    img = Image.alpha_composite(img, overlay)
    return img


def _draw_slider_piece(width: int, height: int) -> Image.Image:
    """Draw the puzzle slider piece matching the cutout style."""
    piece = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(piece)

    # Base fill — sky-to-ground gradient matching position
    for i in range(height):
        r = 180 + i * 40 // height
        g = 200 + i * 30 // height
        b = 240 - i * 30 // height
        draw.line([(0, i), (width, i)], fill=(r, g, b, 255))

    # Add some hill detail matching
    for i in range(max(0, height - 30), height):
        r, g_val, b_val = 140, 180, 140
        draw.line([(0, i), (width, i)], fill=(r, g_val, b_val, 255))

    # White border
    draw.rectangle([0, 0, width - 1, height - 1], outline=(255, 255, 255, 200), width=2)

    # Subtle inner shadow at top
    for i in range(4):
        alpha = 40 - i * 10
        draw.line([(1, i), (width - 2, i)], fill=(255, 255, 255, alpha))

    # Directional arrow
    cx, cy = width // 2, height // 2
    arrow_color = (255, 255, 255, 220)
    draw.polygon(
        [(cx - 8, cy), (cx + 8, cy), (cx, cy - 8)],
        fill=arrow_color,
    )
    draw.polygon(
        [(cx - 8, cy), (cx + 8, cy), (cx, cy + 8)],
        fill=arrow_color,
    )

    return piece


async def generate_slide_puzzle(session_id: str, store: KeyValueStore) -> SlidePuzzleData:
    width, height = 300, 160
    slider_w, slider_h = 50, 40
    y = random.randint(25, height - slider_h - 25)
    gap_x = random.randint(50, width - slider_w - 50)

    bg = _draw_puzzle_bg(width, height, gap_x, y, slider_w, slider_h)
    slider = _draw_slider_piece(slider_w, slider_h)

    bg_b64 = _img_to_base64(bg)
    slider_b64 = _img_to_base64(slider)

    await store.set(f"captcha:slide:{session_id}", f"{gap_x}:{y}", ttl=settings.CAPTCHA_EXPIRE)

    logger.info("Slide captcha for %s: x=%d, y=%d (dev mode)", session_id[:8], gap_x, y)
    return SlidePuzzleData(bgImage=bg_b64, slideImage=slider_b64, y=y, sessionId=session_id)


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
