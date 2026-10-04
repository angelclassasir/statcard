"""Render the 1200x630 social preview image into frontend/assets/."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from statcard.providers.valorant import parse_stats
from statcard.themes import dark as theme

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
OUTPUT = ROOT / "frontend" / "assets" / "og-1200x630.png"


def load_fixtures() -> dict:
    return {
        name: json.loads((FIXTURES / f"valorant_{name}.json").read_text(encoding="utf-8"))
        for name in ("account", "mmr", "matches")
    }


def main() -> None:
    from statcard.render import render_card

    stats = parse_stats(load_fixtures(), "Horcus", "1995")
    card = render_card(stats)

    canvas = Image.new("RGB", (1200, 630), theme.BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    title_font = ImageFont.truetype(str(theme.FONT_TITLE), 52)
    sub_font = ImageFont.truetype(str(theme.FONT_BODY), 26)
    draw.text((60, 52), "statcard", font=title_font, fill=theme.TEXT_PRIMARY)
    draw.text((60, 122), "Your Valorant stats, one PNG away.", font=sub_font, fill=theme.TEXT_SECONDARY)

    canvas.paste(card, (100, 190))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()