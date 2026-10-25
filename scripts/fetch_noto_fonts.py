"""Download the git-ignored Noto fallback fonts (SIL OFL) into assets/fonts/.

The renderer degrades gracefully when a fallback is missing (names in that
script render as boxes), so a failed download must never break a build: every
error is logged and skipped. The OFL licence text is downloaded next to each
font so redistribution stays compliant.
"""

import urllib.request
from pathlib import Path

FONTS_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"

# Variable-font builds from the official google/fonts repository (SIL OFL).
FONTS = {
    "NotoSansKR.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"
    ),
    "NotoSansJP.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf"
    ),
    "NotoSansSC.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"
    ),
    "NotoSans.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans%5Bwdth,wght%5D.ttf"
    ),
}

# OFL licence text shipped with every font family.
LICENSES = {
    "OFL-NotoSansKR.txt": "https://github.com/google/fonts/raw/main/ofl/notosanskr/OFL.txt",
    "OFL-NotoSansJP.txt": "https://github.com/google/fonts/raw/main/ofl/notosansjp/OFL.txt",
    "OFL-NotoSansSC.txt": "https://github.com/google/fonts/raw/main/ofl/notosanssc/OFL.txt",
    "OFL-NotoSans.txt": "https://github.com/google/fonts/raw/main/ofl/notosans/OFL.txt",
}


def _download(filename: str, url: str, label: str) -> None:
    """Download one file unless it is already present and non-empty."""
    target = FONTS_DIR / filename
    if target.exists() and target.stat().st_size > 0:
        print(f"skip  {filename} (already present)")
        return
    try:
        print(f"get   {filename} ...")
        urllib.request.urlretrieve(url, target)
        print(f"ok    {filename} ({target.stat().st_size // 1024} KB)")
    except Exception as exc:
        print(f"warn  {filename} failed ({exc}); {label}")


def main() -> None:
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in FONTS.items():
        _download(filename, url, "renderer will degrade for that script")
    for filename, url in LICENSES.items():
        _download(filename, url, "OFL text missing (redistribution note)")


if __name__ == "__main__":
    main()
