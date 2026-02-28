"""
Digital Products Agent — Orchestrator
Flow: Load products → Generate content → PDF → Cover → Approve → Upload to all 3 platforms
"""

import argparse
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")


def load_products(config_path: str = "config/products.yaml") -> list[dict]:
    with open(config_path) as f:
        return yaml.safe_load(f).get("products", [])


def run_product(product: dict, skip_upload: bool = False, dry_run: bool = False):
    """Full pipeline for a single product."""
    from src.product_gen import ProductGenerator
    from src.pdf_gen import generate_pdf
    from src.cover_gen import generate_cover
    from src.notifier import Notifier

    notifier = Notifier()
    key = product["key"]

    logger.info("=" * 60)
    logger.info(f"▶  {product['title']}")
    logger.info("=" * 60)

    # ── 1. Generate content ───────────────────────────────────────
    logger.info("[1/4] Generating content with Gemini...")
    gen = ProductGenerator()
    content = gen.generate(product)
    logger.info(f"Content ready — {len(str(content))} chars")

    if dry_run:
        logger.info("[DRY RUN] Skipping PDF, cover, upload")
        notifier.send(
            f"🧪 <b>Dry run complete</b>\n"
            f"📦 {product['title']}\n"
            f"💬 {content.get('tagline','')}"
        )
        return

    # ── 2. Generate cover ─────────────────────────────────────────
    logger.info("[2/4] Generating cover art...")
    cover_path = generate_cover(product, output_dir=OUTPUT_DIR)

    # ── 3. Generate PDF ───────────────────────────────────────────
    logger.info("[3/4] Generating PDF...")
    pdf_path = generate_pdf(product, content, cover_path, output_dir=OUTPUT_DIR)
    size_mb = Path(pdf_path).stat().st_size / (1024 * 1024)
    logger.info(f"PDF ready: {pdf_path} ({size_mb:.1f} MB)")

    # ── 4. Telegram approval ──────────────────────────────────────
    approved = notifier.ask_approval(product, content)
    if not approved:
        logger.info(f"Skipped by user: {product['title']}")
        return

    if skip_upload:
        logger.info("--skip-upload set — not publishing to platforms")
        notifier.send(f"📄 PDF ready (upload skipped): <b>{product['title']}</b>")
        return

    # ── 5. Upload to all platforms in parallel ────────────────────
    logger.info("[4/4] Uploading to Gumroad, Selar, Payhip...")
    results = _upload_all(product, content, pdf_path, cover_path)

    # ── 6. Notify ─────────────────────────────────────────────────
    lines = [f"🎉 <b>{product['title']}</b> is LIVE on {len(results)} platform(s)!\n"]
    for r in results:
        icon = {"gumroad": "🟢", "selar": "🇳🇬", "payhip": "📦"}.get(r["platform"], "🔗")
        lines.append(f"{icon} <b>{r['platform'].capitalize()}</b>: {r.get('url','—')}")
    lines.append(f"\n💰 Price: ${product['price_usd']}")
    notifier.send("\n".join(lines))
    logger.info("Pipeline complete ✅")


def _upload_all(product: dict, content: dict, pdf_path: str, cover_path: str | None) -> list[dict]:
    """Upload to all 3 platforms in parallel. Returns list of results."""
    from src.platforms.gumroad import GumroadUploader
    from src.platforms.selar import SelarUploader
    from src.platforms.payhip import PayhipUploader

    uploaders = []
    for Cls in [GumroadUploader, SelarUploader, PayhipUploader]:
        try:
            uploaders.append(Cls())
        except ValueError as e:
            logger.warning(f"Skipping {Cls.name}: {e}")

    description = (
        f"{content.get('description', product.get('description',''))}\n\n"
        f"{content.get('tagline','')}\n\n"
        + "\n".join(f"✓ {b}" for b in content.get("what_you_get", content.get("what_you_will_learn", [])))
    )
    tags = product.get("tags", [])

    results = []

    def _upload(uploader):
        try:
            return uploader.create_product(
                title=product["title"],
                description=description[:5000],
                price_usd=product["price_usd"],
                pdf_path=pdf_path,
                cover_path=cover_path,
                tags=tags,
            )
        except Exception as e:
            logger.error(f"[{uploader.name}] Upload failed: {e}")
            return {"platform": uploader.name, "url": None, "error": str(e)}

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(_upload, u): u for u in uploaders}
        for fut in as_completed(futures):
            result = fut.result()
            results.append(result)

    return results


def run_all(products: list[dict], dry_run: bool = False, skip_upload: bool = False):
    for product in products:
        try:
            run_product(product, skip_upload=skip_upload, dry_run=dry_run)
            time.sleep(5)
        except Exception as e:
            logger.error(f"Product failed [{product['key']}]: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Digital Products Agent")
    parser.add_argument("--product", default=None, help="Run a single product by key")
    parser.add_argument("--all", action="store_true", help="Run all products in config")
    parser.add_argument("--dry-run", action="store_true", help="Generate content only, no PDF or upload")
    parser.add_argument("--skip-upload", action="store_true", help="Generate PDF but skip platform upload")
    parser.add_argument("--config", default="config/products.yaml")
    args = parser.parse_args()

    products = load_products(args.config)

    if args.product:
        match = [p for p in products if p["key"] == args.product]
        if not match:
            logger.error(f"Product key '{args.product}' not found in config")
        else:
            run_product(match[0], skip_upload=args.skip_upload, dry_run=args.dry_run)
    elif args.all:
        run_all(products, dry_run=args.dry_run, skip_upload=args.skip_upload)
    else:
        logger.info("Available products:")
        for p in products:
            logger.info(f"  --product {p['key']}  →  {p['title']} (${p['price_usd']})")
        logger.info("\nRun with --all to generate all, or --product <key> for one.")
