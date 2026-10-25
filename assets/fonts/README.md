# Fonts

All fonts used by statcard are distributed under the
[SIL Open Font License 1.1](https://openfontlicense.org/). The licence requires
the copyright notice and licence text to travel with the font files, so every
family ships with its own `OFL-*.txt` in this folder.

## Bundled (committed to git)

| File | Family | Coverage | Licence |
| --- | --- | --- | --- |
| `ChakraPetch-Bold.ttf` | Chakra Petch | Latin, Thai | `OFL-ChakraPetch.txt` |
| `ChakraPetch-SemiBold.ttf` | Chakra Petch | Latin, Thai | `OFL-ChakraPetch.txt` |
| `ChakraPetch-Regular.ttf` | Chakra Petch | Latin, Thai | `OFL-ChakraPetch.txt` |

Source: <https://github.com/google/fonts/tree/main/ofl/chakrapetch>

## Downloaded locally (git-ignored, ~40 MB total)

These are only needed to render player names written in non-Latin scripts
(Korean, Japanese, Chinese, Cyrillic). They are too heavy to commit, so they
are downloaded locally together with their licence texts:

```powershell
uv run python scripts/fetch_noto_fonts.py
```

| File | Family | Licence |
| --- | --- | --- |
| `NotoSansKR.ttf` | Noto Sans KR | `OFL-NotoSansKR.txt` |
| `NotoSansJP.ttf` | Noto Sans JP | `OFL-NotoSansJP.txt` |
| `NotoSansSC.ttf` | Noto Sans SC | `OFL-NotoSansSC.txt` |
| `NotoSans.ttf` | Noto Sans | `OFL-NotoSans.txt` |

Sources:

    Noto Sans KR: https://github.com/google/fonts/tree/main/ofl/notosanskr
    Noto Sans JP: https://github.com/google/fonts/tree/main/ofl/notosansjp
    Noto Sans SC: https://github.com/google/fonts/tree/main/ofl/notosanssc
    Noto Sans:    https://github.com/google/fonts/tree/main/ofl/notosans

If a fallback font is missing, rendering degrades gracefully to Chakra Petch
(non-Latin characters may show as placeholder boxes, but no crash).

> The OFL applies to the font files only. The statcard source code stays under
> the PolyForm Noncommercial licence (see the repository `LICENSE`).
