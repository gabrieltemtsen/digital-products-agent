"""Telegram notifications for the digital products pipeline."""

import logging
import os
import httpx

logger = logging.getLogger("notifier")


class Notifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.token and self.chat_id)
        if not self.enabled:
            logger.warning("Telegram not configured — notifications disabled")

    def send(self, message: str):
        if not self.enabled:
            logger.info(f"[Notify] {message}")
            return
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            httpx.post(url, json={
                "chat_id": int(self.chat_id),
                "text": message,
                "parse_mode": "HTML",
            }, timeout=10)
        except Exception as e:
            logger.warning(f"Telegram notify failed: {e}")

    def ask_approval(self, product: dict, content: dict) -> bool:
        """
        Send a preview to Telegram and wait for approve/reject callback.
        Falls back to auto-approve after 60s if no response.
        """
        import time

        preview = (
            f"📦 <b>New Product Ready</b>\n\n"
            f"📌 <b>{content.get('title', product['title'])}</b>\n"
            f"💬 {content.get('tagline', '')}\n\n"
            f"💰 Price: <b>${product['price_usd']}</b>\n"
            f"🏷 Type: {product['type']}\n\n"
            f"Approve to publish to Gumroad + Selar + Payhip?\n"
            f"(auto-approving in 60s if no response)"
        )

        if not self.enabled:
            logger.info(f"[Approval] Auto-approving (Telegram not configured): {product['title']}")
            return True

        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            resp = httpx.post(url, json={
                "chat_id": int(self.chat_id),
                "text": preview,
                "parse_mode": "HTML",
                "reply_markup": {
                    "inline_keyboard": [[
                        {"text": "✅ Approve & Publish", "callback_data": f"approve_{product['key']}"},
                        {"text": "❌ Skip", "callback_data": f"skip_{product['key']}"},
                    ]]
                }
            }, timeout=10).json()

            message_id = resp.get("result", {}).get("message_id")
            logger.info(f"Approval message sent (id={message_id}). Waiting 60s...")

            deadline = time.time() + 60
            poll_url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            offset = None

            while time.time() < deadline:
                params = {"timeout": 5, "allowed_updates": ["callback_query"]}
                if offset:
                    params["offset"] = offset

                updates = httpx.get(poll_url, params=params, timeout=15).json()
                for update in updates.get("result", []):
                    offset = update["update_id"] + 1
                    cb = update.get("callback_query", {})
                    data = cb.get("data", "")
                    if data == f"approve_{product['key']}":
                        self.send(f"✅ Approved — publishing <b>{product['title']}</b>...")
                        return True
                    elif data == f"skip_{product['key']}":
                        self.send(f"⏭ Skipped: <b>{product['title']}</b>")
                        return False
                time.sleep(3)

            logger.info("No response — auto-approving")
            return True

        except Exception as e:
            logger.warning(f"Approval failed: {e} — auto-approving")
            return True
