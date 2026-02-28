# 💰 Digital Products Agent

Automated pipeline that generates, designs, and publishes digital products to **Gumroad**, **Selar**, and **Payhip** simultaneously — using Gemini AI + Python.

## Pipeline

```
products.yaml → Gemini (content) → FPDF2 (PDF) → HuggingFace (cover)
     → Telegram approval → Gumroad + Selar + Payhip (parallel upload)
```

## Products (current catalog)

| Key | Title | Price |
|---|---|---|
| `ai_prompts_side_hustles` | 500 AI Prompts for Side Hustles | $19 |
| `youtube_automation_blueprint` | YouTube Automation Blueprint | $49 |
| `crypto_trading_prompts` | ChatGPT Prompts for Crypto Traders | $14 |
| `african_creator_guide` | African Creator's Guide to Making Money Online | $29 |
| `ai_tools_cheatsheet` | AI Tools Cheat Sheet 2026 | $9 |

## Usage

```bash
# Generate + upload one product
python -m src.main --product ai_prompts_side_hustles

# Generate + upload all products
python -m src.main --all

# Dry run (content only, no PDF/upload)
python -m src.main --all --dry-run

# Generate PDF but don't upload yet
python -m src.main --product youtube_automation_blueprint --skip-upload
```

## Environment Variables

Copy `.env.example` → `.env` and fill in:
- `GEMINI_API_KEY`
- `HUGGINGFACE_API_TOKEN`
- `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`
- `GUMROAD_EMAIL` + `GUMROAD_PASSWORD`
- `SELAR_EMAIL` + `SELAR_PASSWORD`
- `PAYHIP_EMAIL` + `PAYHIP_PASSWORD`

## Adding a New Product

Edit `config/products.yaml` — add a new entry with `key`, `title`, `price_usd`, `type`, `niche`, etc. No code changes needed.

## Product Types

- `prompt_pack` — numbered prompt collections by category
- `guide` — full ebook with chapters, key takeaways, action steps
- `cheatsheet` — curated reference lists with links and pricing
