# Fonts

All fonts used by statcard are distributed under the
[SIL Open Font License 1.1](https://openfontlicense.org/).

## Bundled (committed to git)

| File | Family | Coverage |
| --- | --- | --- |
| `ChakraPetch-Bold.ttf` | Chakra Petch | Latin, Thai |
| `ChakraPetch-SemiBold.ttf` | Chakra Petch | Latin, Thai |
| `ChakraPetch-Regular.ttf` | Chakra Petch | Latin, Thai |

Source: <https://github.com/google/fonts/tree/main/ofl/chakrapetch>

## Downloaded locally (git-ignored, ~40 MB total)

These are only needed to render player names written in non-Latin scripts
(Korean, Japanese, Chinese, Cyrillic). They are too heavy to commit, so they
are downloaded locally:

```powershell
Invoke-WebRequest -Uri "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf" -OutFile "assets\fonts\NotoSansKR.ttf"
Invoke-WebRequest -Uri "https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf" -OutFile "assets\fonts\NotoSansJP.ttf"
Invoke-WebRequest -Uri "https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf" -OutFile "assets\fonts\NotoSansSC.ttf"
Invoke-WebRequest -Uri "https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans%5Bwdth%2Cwght%5D.ttf" -OutFile "assets\fonts\NotoSans.ttf"
```

Sources:

    Noto Sans KR: https://github.com/google/fonts/tree/main/ofl/notosanskr
    Noto Sans JP: https://github.com/google/fonts/tree/main/ofl/notosansjp
    Noto Sans SC: https://github.com/google/fonts/tree/main/ofl/notosanssc
    Noto Sans: https://github.com/google/fonts/tree/main/ofl/notosans

If a fallback font is missing, rendering degrades gracefully to Chakra Petch
(non-Latin characters may show as placeholder boxes, but no crash).