"""
Product content generator — uses Gemini 2.5 Flash to generate full product content
based on product definition from products.yaml.
"""

import json
import logging
import os
import time

from google import genai
from google.genai import types

logger = logging.getLogger("product_gen")

PROMPTS = {
    "prompt_pack": """
You are a professional digital product creator. Generate a complete, high-quality prompt pack.

Product: {title}
Subtitle: {subtitle}
Niche: {niche}
Target audience: {target_audience}
Description: {description}

Create a comprehensive prompt pack with 10 categories, each containing 20–25 prompts (aim for 200+ total).
Each prompt must be actionable, specific, and immediately usable.

Return ONLY valid JSON:
{{
  "title": "{title}",
  "subtitle": "{subtitle}",
  "tagline": "one punchy sentence about the value",
  "description": "{description}",
  "what_you_get": ["bullet 1", "bullet 2", "bullet 3", "bullet 4", "bullet 5"],
  "sections": [
    {{
      "category": "Category Name",
      "intro": "One sentence about this category",
      "prompts": [
        {{"number": 1, "title": "Prompt Title", "prompt": "Full prompt text here. Be specific and detailed. Use [placeholders] where customization is needed."}}
      ]
    }}
  ],
  "bonus_tips": ["tip 1", "tip 2", "tip 3"],
  "tags": ["tag1", "tag2"]
}}
""",

    "guide": """
You are a professional ebook author and business consultant. Write a comprehensive, actionable guide.

Product: {title}
Subtitle: {subtitle}
Niche: {niche}
Target audience: {target_audience}
Description: {description}

Create a full guide with 8–10 chapters, each packed with actionable content, examples, and steps.
Make it genuinely valuable — the kind of guide people refer back to repeatedly.

Return ONLY valid JSON:
{{
  "title": "{title}",
  "subtitle": "{subtitle}",
  "tagline": "one punchy sentence about the transformation",
  "description": "{description}",
  "what_you_will_learn": ["outcome 1", "outcome 2", "outcome 3", "outcome 4", "outcome 5"],
  "chapters": [
    {{
      "number": 1,
      "title": "Chapter Title",
      "intro": "Opening paragraph hooking the reader",
      "sections": [
        {{
          "heading": "Section Heading",
          "content": "Detailed, actionable content. Minimum 3–4 paragraphs. Include examples, numbers, and specific steps where possible."
        }}
      ],
      "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3"],
      "action_steps": ["step 1", "step 2", "step 3"]
    }}
  ],
  "conclusion": "Motivating closing section (2 paragraphs)",
  "resources": ["resource 1", "resource 2", "resource 3"],
  "tags": ["tag1", "tag2"]
}}
""",

    "cheatsheet": """
You are a professional researcher and content curator. Create a comprehensive cheatsheet/reference guide.

Product: {title}
Subtitle: {subtitle}
Niche: {niche}
Target audience: {target_audience}
Description: {description}

Create a definitive reference with 8–10 categories, each containing 10–15 curated items.
Every item must include name, description, use case, pricing tier, and URL.

Return ONLY valid JSON:
{{
  "title": "{title}",
  "subtitle": "{subtitle}",
  "tagline": "one punchy sentence",
  "description": "{description}",
  "how_to_use": "Brief instructions on how to use this cheatsheet",
  "sections": [
    {{
      "category": "Category Name",
      "description": "What this category covers",
      "items": [
        {{
          "name": "Tool/Resource Name",
          "description": "What it does in one sentence",
          "best_for": "Who/what it's best for",
          "pricing": "Free / Freemium / $X/mo / Paid",
          "url": "https://example.com"
        }}
      ]
    }}
  ],
  "pro_tips": ["tip 1", "tip 2", "tip 3"],
  "tags": ["tag1", "tag2"]
}}
"""
}


class ProductGenerator:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"

    def generate(self, product: dict) -> dict:
        product_type = product.get("type", "guide")
        prompt_template = PROMPTS.get(product_type, PROMPTS["guide"])

        prompt = prompt_template.format(
            title=product.get("title", ""),
            subtitle=product.get("subtitle", ""),
            niche=product.get("niche", ""),
            target_audience=product.get("target_audience", ""),
            description=product.get("description", ""),
        )

        logger.info(f"Generating content for: {product['title']} (type={product_type})")

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.8,
                        max_output_tokens=16384,
                        response_mime_type="application/json",
                    ),
                )
                raw = response.text.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                content = json.loads(raw)
                logger.info(f"✅ Content generated — {len(str(content))} chars")
                return content

            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(3)
                else:
                    raise RuntimeError(f"Failed to generate content after 3 attempts: {e}")
