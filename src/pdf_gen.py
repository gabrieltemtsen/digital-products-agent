"""
PDF Generator — renders product content into a professional PDF using fpdf2.
"""

import logging
import os
from pathlib import Path

from fpdf import FPDF, XPos, YPos

logger = logging.getLogger("pdf_gen")

# Brand colours
CLR_PRIMARY   = (30, 30, 60)      # deep navy
CLR_ACCENT    = (99, 102, 241)    # indigo
CLR_GOLD      = (234, 179, 8)     # gold
CLR_TEXT      = (30, 30, 30)      # near-black
CLR_MUTED     = (100, 100, 120)   # grey
CLR_BG_LIGHT  = (245, 245, 255)   # near-white tint
CLR_WHITE     = (255, 255, 255)


class ProductPDF(FPDF):
    def __init__(self, product_meta: dict):
        super().__init__()
        self.meta = product_meta
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 20, 20)

    # ── Header / Footer ──────────────────────────────────────────
    def header(self):
        if self.page_no() <= 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*CLR_MUTED)
        self.cell(0, 8, self.meta.get("title", ""), align="L")
        self.ln(4)

    def footer(self):
        if self.page_no() <= 1:
            return
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*CLR_MUTED)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")

    # ── Cover Page ───────────────────────────────────────────────
    def add_cover(self, cover_image_path: str | None = None):
        self.add_page()

        # Background
        self.set_fill_color(*CLR_PRIMARY)
        self.rect(0, 0, 210, 297, "F")

        # Accent bar
        self.set_fill_color(*CLR_ACCENT)
        self.rect(0, 0, 8, 297, "F")

        # Cover image (top half if provided)
        if cover_image_path and Path(cover_image_path).exists():
            try:
                self.image(cover_image_path, x=20, y=20, w=170, h=90, keep_aspect_ratio=True)
                y_start = 120
            except Exception:
                y_start = 60
        else:
            y_start = 60

        # Title
        self.set_xy(20, y_start)
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(*CLR_WHITE)
        self.multi_cell(170, 12, self.meta.get("title", ""), align="L")

        # Subtitle
        self.set_x(20)
        self.set_font("Helvetica", "", 14)
        self.set_text_color(*CLR_GOLD)
        self.multi_cell(170, 8, self.meta.get("subtitle", ""), align="L")

        # Tagline
        if self.meta.get("tagline"):
            self.ln(4)
            self.set_x(20)
            self.set_font("Helvetica", "I", 11)
            self.set_text_color(200, 200, 220)
            self.multi_cell(170, 7, self.meta["tagline"], align="L")

        # Bottom strip
        self.set_fill_color(*CLR_ACCENT)
        self.rect(0, 270, 210, 27, "F")
        self.set_xy(20, 275)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*CLR_WHITE)
        self.cell(0, 8, "© 2026 StrategicArchives  |  strategicarchives.com", align="C")

    # ── TOC Page ─────────────────────────────────────────────────
    def add_toc(self, sections: list[dict]):
        self.add_page()
        self._section_heading("Table of Contents")
        self.ln(4)
        for i, s in enumerate(sections, 1):
            self.set_font("Helvetica", "", 11)
            self.set_text_color(*CLR_TEXT)
            label = s.get("title") or s.get("category", f"Section {i}")
            self.cell(160, 8, f"{i}.  {label}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_draw_color(*CLR_ACCENT)
            self.line(20, self.get_y(), 190, self.get_y())
            self.ln(1)

    # ── Helpers ───────────────────────────────────────────────────
    def _section_heading(self, text: str):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*CLR_ACCENT)
        self.cell(0, 12, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # underline
        self.set_draw_color(*CLR_GOLD)
        self.set_line_width(0.8)
        self.line(20, self.get_y(), 80, self.get_y())
        self.set_line_width(0.2)
        self.ln(6)

    def _sub_heading(self, text: str):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*CLR_PRIMARY)
        self.cell(0, 9, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def _body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*CLR_TEXT)
        self.multi_cell(0, 6, text.strip())
        self.ln(3)

    def _bullet(self, text: str, indent: int = 6):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*CLR_TEXT)
        self.set_x(20 + indent)
        self.cell(4, 6, "•")
        self.multi_cell(0, 6, text.strip())

    def _callout_box(self, text: str):
        self.set_fill_color(*CLR_BG_LIGHT)
        self.set_draw_color(*CLR_ACCENT)
        self.set_line_width(0.5)
        self.set_font("Helvetica", "I", 10)
        self.set_text_color(*CLR_ACCENT)
        self.multi_cell(0, 7, f"  💡 {text.strip()}", border=1, fill=True)
        self.ln(3)

    def _prompt_box(self, number: int, title: str, prompt_text: str):
        self.set_fill_color(240, 240, 255)
        self.set_draw_color(*CLR_ACCENT)
        # Header row
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*CLR_ACCENT)
        self.set_fill_color(220, 220, 245)
        self.cell(0, 7, f"  #{number} — {title}", border=1, fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Prompt text
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*CLR_TEXT)
        self.set_fill_color(248, 248, 255)
        self.multi_cell(0, 6, f"  {prompt_text.strip()}", border=1, fill=True)
        self.ln(3)


# ── Renderers by product type ─────────────────────────────────────────────────

def _render_prompt_pack(pdf: ProductPDF, content: dict):
    # What you get
    if content.get("what_you_get"):
        pdf.add_page()
        pdf._section_heading("What You Get")
        for item in content["what_you_get"]:
            pdf._bullet(item)
        pdf.ln(4)

    # TOC
    sections = content.get("sections", [])
    pdf.add_toc([{"title": s["category"]} for s in sections])

    # Prompts
    for section in sections:
        pdf.add_page()
        pdf._section_heading(section.get("category", ""))
        if section.get("intro"):
            pdf._body_text(section["intro"])
        for p in section.get("prompts", []):
            pdf._prompt_box(p["number"], p.get("title", ""), p.get("prompt", ""))

    # Bonus tips
    if content.get("bonus_tips"):
        pdf.add_page()
        pdf._section_heading("Bonus Tips")
        for tip in content["bonus_tips"]:
            pdf._bullet(tip)


def _render_guide(pdf: ProductPDF, content: dict):
    # What you'll learn
    if content.get("what_you_will_learn"):
        pdf.add_page()
        pdf._section_heading("What You Will Learn")
        for item in content["what_you_will_learn"]:
            pdf._bullet(item)
        pdf.ln(4)

    # TOC
    chapters = content.get("chapters", [])
    pdf.add_toc([{"title": f"Chapter {c['number']}: {c['title']}"} for c in chapters])

    # Chapters
    for chapter in chapters:
        pdf.add_page()
        pdf._section_heading(f"Chapter {chapter['number']}: {chapter.get('title','')}")
        if chapter.get("intro"):
            pdf._body_text(chapter["intro"])

        for sec in chapter.get("sections", []):
            pdf._sub_heading(sec.get("heading", ""))
            pdf._body_text(sec.get("content", ""))

        if chapter.get("key_takeaways"):
            pdf._sub_heading("Key Takeaways")
            for t in chapter["key_takeaways"]:
                pdf._bullet(t)
            pdf.ln(2)

        if chapter.get("action_steps"):
            pdf._sub_heading("Action Steps")
            for i, step in enumerate(chapter["action_steps"], 1):
                pdf._bullet(f"Step {i}: {step}")
            pdf.ln(2)

    # Conclusion
    if content.get("conclusion"):
        pdf.add_page()
        pdf._section_heading("Conclusion")
        pdf._body_text(content["conclusion"])

    # Resources
    if content.get("resources"):
        pdf._sub_heading("Recommended Resources")
        for r in content["resources"]:
            pdf._bullet(r)


def _render_cheatsheet(pdf: ProductPDF, content: dict):
    if content.get("how_to_use"):
        pdf.add_page()
        pdf._section_heading("How to Use This Cheatsheet")
        pdf._body_text(content["how_to_use"])

    sections = content.get("sections", [])
    pdf.add_toc([{"title": s["category"]} for s in sections])

    for section in sections:
        pdf.add_page()
        pdf._section_heading(section.get("category", ""))
        if section.get("description"):
            pdf._body_text(section["description"])
        for item in section.get("items", []):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*CLR_PRIMARY)
            pdf.cell(0, 7, item.get("name", ""), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*CLR_TEXT)
            pdf.multi_cell(0, 5, f"  {item.get('description','')}  |  Best for: {item.get('best_for','')}  |  {item.get('pricing','')}  |  {item.get('url','')}")
            pdf.ln(2)

    if content.get("pro_tips"):
        pdf.add_page()
        pdf._section_heading("Pro Tips")
        for tip in content["pro_tips"]:
            pdf._bullet(tip)


# ── Main entry point ─────────────────────────────────────────────────────────

RENDERERS = {
    "prompt_pack": _render_prompt_pack,
    "guide": _render_guide,
    "cheatsheet": _render_cheatsheet,
}


def generate_pdf(product: dict, content: dict, cover_image_path: str | None, output_dir: str = "./output") -> str:
    """Generate a PDF for the product. Returns the path to the PDF."""
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{product['key']}.pdf")

    pdf = ProductPDF(product_meta=content)
    pdf.add_cover(cover_image_path)

    product_type = product.get("type", "guide")
    renderer = RENDERERS.get(product_type, _render_guide)
    renderer(pdf, content)

    pdf.output(out_path)
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    logger.info(f"✅ PDF generated: {out_path} ({size_mb:.1f} MB, {pdf.page_no()} pages)")
    return out_path
