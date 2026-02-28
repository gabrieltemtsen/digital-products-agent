"""
Selar uploader — Playwright browser automation for selar.co
"""

import logging
import os
import time

from .base import BasePlatformUploader

logger = logging.getLogger("platform.selar")


class SelarUploader(BasePlatformUploader):
    name = "selar"

    def __init__(self):
        self.email = os.getenv("SELAR_EMAIL")
        self.password = os.getenv("SELAR_PASSWORD")
        if not self.email or not self.password:
            raise ValueError("SELAR_EMAIL and SELAR_PASSWORD must be set")

    def create_product(self, title, description, price_usd, pdf_path, cover_path=None, tags=None):
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

        logger.info(f"[Selar] Uploading: {title}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            page = ctx.new_page()

            try:
                # ── Login ──────────────────────────────────────────────
                page.goto("https://selar.co/login", wait_until="domcontentloaded")
                time.sleep(2)
                page.fill('input[type="email"], input[name="email"]', self.email)
                page.fill('input[type="password"], input[name="password"]', self.password)
                page.click('button[type="submit"]')
                page.wait_for_url("**/dashboard**", timeout=20000)
                logger.info("[Selar] Logged in ✓")

                # ── Create new product ─────────────────────────────────
                page.goto("https://selar.co/store/products/create", wait_until="domcontentloaded")
                time.sleep(3)

                # Select "Digital Download" / "Ebook" type
                try:
                    ebook_btn = page.locator(
                        'div:has-text("Ebook"), button:has-text("Ebook"), '
                        'label:has-text("Ebook"), div:has-text("Digital Download")'
                    ).first
                    ebook_btn.click()
                    time.sleep(1)
                except PWTimeout:
                    pass

                # Product title
                page.fill('input[placeholder*="title" i], input[name*="title" i]', title)

                # Description
                try:
                    desc = page.locator('textarea[placeholder*="description" i], div[contenteditable="true"]').first
                    desc.fill(description[:3000])
                except Exception:
                    pass

                # Price (Selar uses USD or NGN)
                try:
                    price_field = page.locator('input[placeholder*="price" i], input[name*="price" i]').first
                    price_field.fill(str(price_usd))
                except Exception:
                    pass

                # Upload PDF
                logger.info("[Selar] Uploading PDF...")
                try:
                    file_input = page.locator('input[type="file"]').first
                    file_input.set_input_files(pdf_path)
                    time.sleep(10)  # Selar upload can be slow
                except Exception as e:
                    logger.warning(f"[Selar] PDF upload issue: {e}")

                # Upload cover
                if cover_path and os.path.exists(cover_path):
                    try:
                        img_inputs = page.locator('input[type="file"][accept*="image"]')
                        if img_inputs.count() > 0:
                            img_inputs.first.set_input_files(cover_path)
                            time.sleep(4)
                    except Exception:
                        pass

                # Save / Publish
                page.locator(
                    'button:has-text("Publish"), button:has-text("Save"), '
                    'button:has-text("Create"), button[type="submit"]'
                ).first.click()
                time.sleep(5)

                product_url = page.url
                try:
                    link_el = page.locator('a[href*="selar.co/"]').first
                    if link_el.is_visible(timeout=3000):
                        product_url = link_el.get_attribute("href")
                except PWTimeout:
                    pass

                logger.info(f"[Selar] ✅ Published: {product_url}")
                return {"url": product_url, "platform": self.name}

            except Exception as e:
                screenshot = "./output/selar_error.png"
                page.screenshot(path=screenshot)
                logger.error(f"[Selar] Failed: {e} — screenshot: {screenshot}")
                raise
            finally:
                browser.close()
