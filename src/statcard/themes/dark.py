"""Dark theme: palette, fonts and geometry shared by all cards."""

from pathlib import Path

# Assets live at the repository root, next to src/
ASSETS_DIR = Path(__file__).resolve().parents[3] / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"

# --- Palette (RGB tuples) ---
BACKGROUND = (16, 17, 23)         # near-black canvas
PANEL = (28, 30, 40)              # raised panels
PANEL_EDGE = (45, 48, 62)         # panel borders and separators
ACCENT = (255, 70, 85)            # Valorant accent (red)
ACCENT_CS2 = (255, 165, 0)        # CS2 accent (orange)
TEXT_PRIMARY = (242, 243, 248)    # headings and key stats
TEXT_SECONDARY = (150, 154, 170)  # labels and secondary text
WIN = (86, 197, 127)              # win green
LOSS = (227, 84, 95)              # loss red

# --- Card geometry (pixels) ---
CARD_WIDTH = 1000
CARD_HEIGHT = 400
PADDING = 32
CORNER_RADIUS = 24

# --- Fonts (SIL OFL, see assets/fonts) ---
FONT_TITLE = FONTS_DIR / "ChakraPetch-Bold.ttf"
FONT_SUBTITLE = FONTS_DIR / "ChakraPetch-SemiBold.ttf"
FONT_BODY = FONTS_DIR / "ChakraPetch-Regular.ttf"

# Fallback fonts for non-Latin player names (downloaded locally, git-ignored)
FONT_FALLBACKS = {
    "kr": FONTS_DIR / "NotoSansKR.ttf",        # Hangul (Korean)
    "jp": FONTS_DIR / "NotoSansJP.ttf",        # Kana + kanji (Japanese)
    "cjk": FONTS_DIR / "NotoSansSC.ttf",       # Hanzi (Chinese)
    "cyrillic": FONTS_DIR / "NotoSans.ttf",    # Russian, Ukrainian, etc.
}

# --- Font sizes (pixels) ---
SIZE_TITLE = 44
SIZE_SUBTITLE = 26
SIZE_STAT_VALUE = 40
SIZE_STAT_LABEL = 16
SIZE_FOOTER = 14