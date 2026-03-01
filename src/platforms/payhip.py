"""
Payhip uploader — Playwright browser automation for payhip.com
"""

import logging
import os
import time

from .base import BasePlatformUploader

logger = logging.getLogger("platform.payhip")


class PayhipUploader(BasePlatformUploader):
    name = "payhip"

    def __init__(self):
        self.email = os.getenv("PAYHIP_EMAIL")
        self.password = os.getenv("PAYHIP_PASSWORD")
        if not self.email or not self.password:
            raise ValueError("PAYHIP_EMAIL and PAYHIP_PASSWORD must be set")

    def create_product(self, title, description, price_usd, pdf_path, cover_path=None, tags=None):
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

        logger.info(f"[Payhip] Uploading: {title}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            page = ctx.new_page()

            try:
                # ── Login ──────────────────────────────────────────────
                page.goto("https://payhip.com/login", wait_until="domcontentloaded")
                time.sleep(2)
                page.locator('input[name="email"], input[type="email"]').first.fill(self.email, timeout=60000)
                page.locator('input[name="password"], input[type="password"]').first.fill(self.password)
                page.locator('button[type="submit"], input[type="submit"], button:has-text("Login")').first.click()
                page.wait_for_url("**/home**", timeout=30000)
                logger.info("[Payhip] Logged in ✓")

                # ── Add a digital download ─────────────────────────────
                page.goto("https://payhip.com/product/add", wait_until="domcontentloaded")
                time.sleep(2)

                # Select "Digital Download" if type picker appears
                try:
                    dl_btn = page.locator(
                        'button:has-text("Digital Download"), label:has-text("Digital"), '
                        'a:has-text("Digital Download")'
                    ).first
                    dl_btn.click()
                    time.sleep(1)
                except PWTimeout:
                    pass

                # Title
                page.fill(
                    'input[name="name"], input[placeholder*="name" i], input[placeholder*="title" i]',
                    title
                )

                # Description (Payhip uses a rich text editor)
                try:
                    desc_field = page.locator(
                        'textarea[name*="desc" i], div.ql-editor, div[contenteditable="true"]'
                    ).first
                    desc_field.fill(description[:3000])
                except Exception:
                    pass

                # Price
                try:
                    price_input = page.locator('input[name*="price" i], input[placeholder*="price" i]').first
                    price_input.fill(str(price_usd))
                except Exception:
                    pass

                # Upload PDF
                logger.info("[Payhip] Uploading PDF...")
                try:
                    file_input = page.locator('input[type="file"]').first
                    file_input.set_input_files(pdf_path)
                    # Wait for upload progress
                    time.sleep(12)
                except Exception as e:
                    logger.warning(f"[Payhip] PDF upload issue: {e}")

                # Upload cover / thumbnail
                if cover_path and os.path.exists(cover_path):
                    try:
                        img_input = page.locator(
                            'input[type="file"][accept*="image"], '
                            'input[name*="cover"], input[name*="image"]'
                        ).first
                        img_input.set_input_files(cover_path)
                        time.sleep(4)
                    except Exception:
                        pass

                # Save product
                page.locator(
                    'button:has-text("Save"), button:has-text("Publish"), '
                    'button:has-text("Add product"), button[type="submit"]'
                ).first.click()
                time.sleep(5)

                product_url = page.url
                try:
                    link_el = page.locator('a[href*="payhip.com/b/"]').first
                    if link_el.is_visible(timeout=3000):
                        product_url = link_el.get_attribute("href")
                except PWTimeout:
                    pass

                logger.info(f"[Payhip] ✅ Published: {product_url}")
                return {"url": product_url, "platform": self.name}

            except Exception as e:
                screenshot = "./output/payhip_error.png"
                page.screenshot(path=screenshot)
                logger.error(f"[Payhip] Failed: {e} — screenshot: {screenshot}")
                raise
            finally:
                browser.close()
