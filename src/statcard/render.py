"""Card rendering with Pillow: PlayerStats -> PNG image."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from statcard.models import PlayerStats
from statcard.themes import dark as theme

# Output folder for generated cards (repo root / output)
OUTPUT_DIR = theme.ASSETS_DIR.parent / "output"

# Vertical layout stops (pixels from the top of the card)
_HEADER_Y = 30
_STATS_Y = 150
_STRIP_Y = 246
_BOX_HEIGHT = 92
_FOOTER_Y = 378

# Accent color and data source attribution per game
_GAME_ACCENT = {
    "valorant": theme.ACCENT,
    "cs2_faceit": theme.ACCENT_CS2,
    "cs2_premier": theme.ACCENT_CS2,
}
_DATA_SOURCES = {
    "valorant": "HenrikDev API",
    "cs2_faceit": "FACEIT API",
    "cs2_premier": "Leetify",
}

# Loaded fonts are cached: reloading a TTF per drawn box is wasteful
_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def _font(path: Path, size: int, variant: str | None = None) -> ImageFont.FreeTypeFont:
    """Load a TTF font, optionally switching a variable font to a named instance."""
    key = (str(path), size)
    if key not in _FONT_CACHE:
        font = ImageFont.truetype(str(path), size)
        if variant is not None:
            try:
                font.set_variation_by_name(variant)
            except (OSError, AttributeError, KeyError):
                pass  # static font or unknown variant: keep the default instance
        _FONT_CACHE[key] = font
    return _FONT_CACHE[key]


def _detect_script(text: str) -> str:
    """Detect the dominant non-Latin script used in a player name."""
    codepoints = [ord(ch) for ch in text]
    # Hangul syllables and jamo (Korean)
    if any(0xAC00 <= cp <= 0xD7AF or 0x1100 <= cp <= 0x11FF or 0x3130 <= cp <= 0x318F for cp in codepoints):
        return "kr"
    # Hiragana and katakana (Japanese)
    if any(0x3040 <= cp <= 0x30FF for cp in codepoints):
        return "jp"
    # CJK unified ideographs (Chinese, and kanji without kana)
    if any(0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0xF900 <= cp <= 0xFAFF for cp in codepoints):
        return "cjk"
    # Cyrillic (Russian and friends)
    if any(0x0400 <= cp <= 0x4FF for cp in codepoints):
        return "cyrillic"
    return "latin"

def _title_font(text: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Pick the best font for a player name, degrading gracefully if files are missing."""
    script = _detect_script(text)
    candidates = [theme.FONT_FALLBACKS.get(script, theme.FONT_TITLE), theme.FONT_TITLE]
    for path in candidates:
        try:
            return _font(path, size, variant="Bold")
        except OSError:
            continue  # font file not downloaded: try the next candidate
    # Last resort: Pillow's bundled font (Latin only, but never crashes)
    return ImageFont.load_default(size)


def _draw_header(draw: ImageDraw.ImageDraw, stats: PlayerStats) -> None:
    """Draw the game tag, player name and rank line."""
    x = theme.PADDING
    accent = _GAME_ACCENT.get(stats.game, theme.ACCENT)

    label_font = _font(theme.FONT_SUBTITLE, theme.SIZE_STAT_LABEL)
    draw.text((x, _HEADER_Y), stats.game.upper(), font=label_font, fill=accent)

    name_font = _title_font(stats.player_name, theme.SIZE_TITLE)
    draw.text((x, _HEADER_Y + 22), stats.player_name, font=name_font, fill=theme.TEXT_PRIMARY)

    rank_font = _font(theme.FONT_BODY, 20)
    rank_text = f"{stats.current_rank}  •  peak {stats.peak_rank}  •  Lv {stats.level}"
    draw.text((x, _HEADER_Y + 80), rank_text, font=rank_font, fill=theme.TEXT_SECONDARY)

    # Separator between header and stats
    draw.line(
        [(theme.PADDING, 140), (theme.CARD_WIDTH - theme.PADDING, 140)],
        fill=theme.PANEL_EDGE,
        width=1,
    )

def _draw_stats_row(draw: ImageDraw.ImageDraw, stats: PlayerStats) -> None:
    """Draw the three big stat blocks separated by vertical lines."""
    losses = max(stats.total_matches - stats.wins, 0)
    blocks = [
        (stats.get_kd_display(), "K/D RATIO (RECENT)"),
        (stats.get_win_rate_display(), "WIN RATE"),
        (f"{stats.wins}W - {losses}L", "SEASON RECORD"),
    ]

    value_font = _font(theme.FONT_SUBTITLE, theme.SIZE_STAT_VALUE)
    label_font = _font(theme.FONT_BODY, theme.SIZE_STAT_LABEL)
    block_width = (theme.CARD_WIDTH - 2 * theme.PADDING) // 3

    for i, (value, label) in enumerate(blocks):
        x = theme.PADDING + i * block_width
        if i:
            draw.line(
                [(x - 24, _STATS_Y), (x - 24, _STATS_Y + 60)],
                fill=theme.PANEL_EDGE,
                width=1,
            )
        draw.text((x, _STATS_Y), value, font=value_font, fill=theme.TEXT_PRIMARY)
        draw.text((x, _STATS_Y + 46), label, font=label_font, fill=theme.TEXT_SECONDARY)


def _draw_matches_strip(draw: ImageDraw.ImageDraw, stats: PlayerStats) -> None:
    """Draw one small result box per recent match."""
    matches = stats.recent_matches[:5]
    if not matches:
        return

    gap = 12
    box_w = (theme.CARD_WIDTH - 2 * theme.PADDING - gap * (len(matches) - 1)) // len(matches)
    x = theme.PADDING

    map_font = _font(theme.FONT_SUBTITLE, 18)
    score_font = _font(theme.FONT_BODY, theme.SIZE_STAT_LABEL - 2)
    letter_font = _font(theme.FONT_TITLE, 26)

    for match in matches:
        won = match.get("won")
        edge = theme.WIN if won else theme.LOSS if won is False else theme.PANEL_EDGE
        letter = "W" if won else "L" if won is False else "-"

        draw.rounded_rectangle(
            [x, _STRIP_Y, x + box_w, _STRIP_Y + _BOX_HEIGHT],
            radius=12,
            fill=theme.BACKGROUND,
            outline=theme.PANEL_EDGE,
        )
        # Result edge bar on the left of the box
        draw.rounded_rectangle(
            [x, _STRIP_Y, x + 6, _STRIP_Y + _BOX_HEIGHT],
            radius=3,
            fill=edge,
        )
        draw.text(
            (x + 16, _STRIP_Y + 12),
            str(match.get("map", "?")),
            font=map_font,
            fill=theme.TEXT_PRIMARY,
        )
        score = (
            f"{match.get('rounds_won', '?')}-{match.get('rounds_lost', '?')}"
            f"  •  {match.get('kills', 0)}K/{match.get('deaths', 0)}D"
        )
        draw.text((x + 16, _STRIP_Y + 38), score, font=score_font, fill=theme.TEXT_SECONDARY)
        draw.text(
            (x + 16, _STRIP_Y + 62),
            str(match.get("agent", "")),
            font=score_font,
            fill=theme.TEXT_SECONDARY,
        )
        draw.text(
            (x + box_w - 12, _STRIP_Y + 12),
            letter,
            font=letter_font,
            fill=edge,
            anchor="ra",
        )
        x += box_w + gap


def _draw_footer(draw: ImageDraw.ImageDraw, stats: PlayerStats) -> None:
    """Draw the attribution footer at the bottom of the card."""
    footer_font = _font(theme.FONT_BODY, theme.SIZE_FOOTER)
    source = _DATA_SOURCES.get(stats.game, "the game API")
    right = f"stats via {source} • {stats.last_updated:%Y-%m-%d %H:%M}"
    draw.text(
        (theme.PADDING, _FOOTER_Y),
        "statcard",
        font=footer_font,
        fill=theme.TEXT_SECONDARY,
        anchor="ls",
    )
    draw.text(
        (theme.CARD_WIDTH - theme.PADDING, _FOOTER_Y),
        right,
        font=footer_font,
        fill=theme.TEXT_SECONDARY,
        anchor="rs",
    )


def render_card(stats: PlayerStats) -> Image.Image:
    """Draw the full stat card and return it as a PIL image."""
    img = Image.new("RGB", (theme.CARD_WIDTH, theme.CARD_HEIGHT), theme.BACKGROUND)
    draw = ImageDraw.Draw(img)

    # Rounded background panel
    draw.rounded_rectangle(
        [0, 0, theme.CARD_WIDTH - 1, theme.CARD_HEIGHT - 1],
        radius=theme.CORNER_RADIUS,
        fill=theme.PANEL,
        outline=theme.PANEL_EDGE,
        width=2,
    )

    _draw_header(draw, stats)
    _draw_stats_row(draw, stats)
    _draw_matches_strip(draw, stats)
    _draw_footer(draw, stats)
    return img


def save_card(stats: PlayerStats, filename: str | None = None) -> Path:
    """Render the card and save it as a PNG inside output/."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / (filename or f"{stats.game}_card.png")
    render_card(stats).save(path)
    return path