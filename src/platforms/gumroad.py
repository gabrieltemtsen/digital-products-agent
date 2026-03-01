"""
Gumroad uploader — uses Playwright browser automation to create & publish a product.
"""

import logging
import os
import time

from .base import BasePlatformUploader

logger = logging.getLogger("platform.gumroad")


class GumroadUploader(BasePlatformUploader):
    name = "gumroad"

    def __init__(self):
        self.email = os.getenv("GUMROAD_EMAIL")
        self.password = os.getenv("GUMROAD_PASSWORD")
        if not self.email or not self.password:
            raise ValueError("GUMROAD_EMAIL and GUMROAD_PASSWORD must be set")

    def create_product(self, title, description, price_usd, pdf_path, cover_path=None, tags=None):
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

        logger.info(f"[Gumroad] Uploading: {title}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            page = ctx.new_page()

            try:
                # ── Login ──────────────────────────────────────────────
                page.goto("https://app.gumroad.com/login", wait_until="domcontentloaded")
                page.locator('input[type="email"], input[name="email"], #email').first.fill(self.email, timeout=60000)
                page.locator('input[type="password"], input[name="password"], #password').first.fill(self.password)
                page.locator('button[type="submit"], button:has-text("Login")').first.click()
                page.wait_for_url("**/dashboard**", timeout=45000)
                logger.info("[Gumroad] Logged in ✓")

                # ── New product ────────────────────────────────────────
                page.goto("https://app.gumroad.com/products/new", wait_until="domcontentloaded")
                time.sleep(2)

                # Fill product name
                name_input = page.locator('input[placeholder*="name" i], input[name*="name" i]').first
                name_input.fill(title)

                # Select "digital product" type if prompted
                try:
                    digital_btn = page.locator('button:has-text("Digital product"), label:has-text("Digital")').first
                    if digital_btn.is_visible(timeout=3000):
                        digital_btn.click()
                except PWTimeout:
                    pass

                # Click Continue / Next
                try:
                    page.locator('button:has-text("Next"), button:has-text("Continue"), button[type="submit"]').first.click()
                    time.sleep(2)
                except PWTimeout:
                    pass

                # ── Upload PDF ─────────────────────────────────────────
                logger.info("[Gumroad] Uploading PDF file...")
                file_input = page.locator('input[type="file"]').first
                file_input.set_input_files(pdf_path)
                # Wait for upload to complete (progress bar disappears or success message)
                time.sleep(8)

                # ── Fill description ───────────────────────────────────
                try:
                    desc_area = page.locator('textarea[name*="desc" i], div[contenteditable="true"]').first
                    desc_area.fill(description[:2000])
                except Exception:
                    pass

                # ── Set price ──────────────────────────────────────────
                try:
                    price_input = page.locator('input[name*="price" i], input[placeholder*="price" i]').first
                    price_input.fill(str(int(price_usd * 100)))  # Gumroad uses cents
                except Exception:
                    try:
                        price_input = page.locator('input[type="number"]').first
                        price_input.fill(str(price_usd))
                    except Exception:
                        pass

                # ── Upload cover image ─────────────────────────────────
                if cover_path and os.path.exists(cover_path):
                    try:
                        cover_input = page.locator('input[type="file"][accept*="image"]').first
                        cover_input.set_input_files(cover_path)
                        time.sleep(4)
                    except Exception:
                        pass

                # ── Publish ────────────────────────────────────────────
                page.locator('button:has-text("Publish"), button:has-text("Save and continue"), button:has-text("Save")').first.click()
                time.sleep(4)

                # Grab the product URL
                product_url = page.url
                # Try to extract the short Gumroad link
                try:
                    link_el = page.locator('a[href*="gum.co"], a[href*="gumroad.com/l/"]').first
                    if link_el.is_visible(timeout=3000):
                        product_url = link_el.get_attribute("href")
                except PWTimeout:
                    pass

                logger.info(f"[Gumroad] ✅ Published: {product_url}")
                return {"url": product_url, "platform": self.name}

            except Exception as e:
                screenshot = f"./output/gumroad_error.png"
                page.screenshot(path=screenshot)
                logger.error(f"[Gumroad] Failed: {e} — screenshot: {screenshot}")
                raise
            finally:
                browser.close()
