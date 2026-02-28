"""
Cover art generator — uses HuggingFace FLUX or falls back to a styled fpdf2 cover.
"""

import io
import logging
import os
import time

import httpx
from PIL import Image

logger = logging.getLogger("cover_gen")


def generate_cover(product: dict, output_dir: str = "./output") -> str | None:
    """Generate a cover image. Returns the path, or None on failure."""
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{product['key']}_cover.png")

    hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
    if hf_token:
        path = _hf_cover(product, out_path, hf_token)
        if path:
            return path

    logger.warning("HuggingFace cover failed — using fallback plain cover")
    return None   # PDF cover page will render text-only


def _hf_cover(product: dict, out_path: str, token: str) -> str | None:
    style = product.get("cover_style", "professional digital product cover art")
    prompt = (
        f"Digital product book cover art: {product.get('title', '')}. "
        f"Style: {style}. "
        f"High quality, professional, modern design. No text overlays needed. "
        f"Aspect ratio 16:9 landscape for ebook cover."
    )

    api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": prompt, "parameters": {"width": 832, "height": 480}}

    for attempt in range(3):
        try:
            logger.info(f"Generating cover via HuggingFace (attempt {attempt + 1})...")
            resp = httpx.post(api_url, headers=headers, json=payload, timeout=90)
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                img.save(out_path, "PNG")
                logger.info(f"✅ Cover saved: {out_path}")
                return out_path
            elif resp.status_code == 503:
                logger.warning(f"Model loading... retrying in 15s")
                time.sleep(15)
            else:
                logger.warning(f"HF error {resp.status_code}: {resp.text[:200]}")
                return None
        except Exception as e:
            logger.warning(f"Cover gen attempt {attempt + 1} failed: {e}")
            time.sleep(5)
    return None
