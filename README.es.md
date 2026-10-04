
---

## `README.es.md`

```markdown
# 🎴 StatCard

> Genera tarjetas visuales con tus estadísticas de tus juegos FPS favoritos.

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Dual%20%28PolyForm%20NC%20%2B%20Commercial%29-lightgrey.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**Idioma:** [English](README.md) | **Español**

---

`statcard` obtiene tus estadísticas de **Valorant**, las unifica en un formato común y las renderiza en una tarjeta PNG lista para compartir en Discord, redes sociales o tu perfil de GitHub.

> 🌐 **Demo en vivo:** [statcard.pages.dev](https://statcard.pages.dev) — genera tu tarjeta sin instalar nada.

> ⚠️ **Estado del proyecto:** la v1 (CLI de Valorant) y la v2 (aplicación web pública) están publicadas y en producción. La v2.1 (pulido estético UI/UX) está en progreso. Ver [Hoja de ruta](#-hoja-de-ruta).

---

## ✨ Características

- 🎮 **Soporte para Valorant** mediante la [HenrikDev API](https://docs.henrikdev.xyz)
- 🎨 **Tema oscuro** con una paleta limpia y moderna
- 🔤 **Fuentes según alfabeto**: latín (Chakra Petch), coreano (Noto Sans KR), japonés (Noto Sans JP), chino (Noto Sans SC), cirílico (Noto Sans) — los nombres se renderizan correctamente sea cual sea el alfabeto
- 💾 **Caché en disco inteligente** (TTL de 10 min) para respetar los límites de las APIs
- ⚡ **Diseño CLI-first**: un comando, una tarjeta
- 🧪 **Suite de tests offline** usando respuestas guardadas
- 🌐 **Interfaz web** *(planificada para la v2)*: genera tu tarjeta sin instalar nada

## 🖼️ Ejemplo

| Valorant |
| :---: |
| ![Tarjeta Valorant de ejemplo](examples/valorant_card.png) |

## 🛠️ Stack Tecnológico

| Componente | Herramienta |
| --- | --- |
| Lenguaje | Python 3.12+ |
| Cliente HTTP | `httpx` |
| Validación de datos | `pydantic` |
| Renderizado de imágenes | `Pillow` |
| Gestión de entorno | `uv` |
| Testing | `pytest` |
| Linting y formateo | `ruff` |
| Chequeo de tipos | `pyrefly` |

## 🗺️ Hoja de ruta

### v1 — CLI de Valorant (publicada ✅)

- Provider HenrikDev con K/D de temporada (fallback SEASON/RECENT)
- Fuentes multialfabeto (latín, tailandés, CJK, cirílico)
- Caché en disco (TTL 10 min), CLI con argparse, suite de tests offline
- Licencia dual (PolyForm NC + comercial bajo autorización)

### v2 — Aplicación web pública (publicada ✅)

- Backend FastAPI (`src/statcard/web/`): `/healthz`, `/api/valorant/{riot_id}` (PNG), `/api/valorant/{riot_id}/json`
- Rate limit con ventana deslizante (3/min por IP + 20/min global) + caché compartida en disco (TTL 1 h)
- Frontend HTML/JS/CSS vanilla (`frontend/`), sin build step
- Producción: backend en Render free tier (pinger keep-awake) + frontend en Cloudflare Pages → [statcard.pages.dev](https://statcard.pages.dev)
- Documento de diseño: [`docs/INFRASTRUCTURE.md`](docs/INFRASTRUCTURE.md)

### v2.1 — Calidad web, pulido y selector de juego (publicada ✅)

- **Selector de juego** con los logos oficiales: Valorant activo, CS2 deshabilitado con badge "v3"
- **SEO e identidad**: title único, meta description, canonical, favicon SVG, `robots.txt`, `sitemap.xml`, `404.html` temática
- **Compartir en redes**: Open Graph + `twitter:card = summary_large_image` con preview de 1200×630 generada por nuestro propio pipeline de Pillow
- **Rendimiento**: fuentes WOFF2 auto-alojadas (sin CDNs), imágenes lazy con dimensiones explícitas, cero dependencias JS
- **Accesibilidad**: contraste ≥ 4.5:1, enlace "saltar al contenido", foco visible con teclado, labels en cada campo, textos `alt`, respeto por `prefers-reduced-motion`
- **Seguridad**: `_headers` con CSP, `X-Content-Type-Options`, `Referrer-Policy`; caché inmutable para fuentes; la clave de API nunca sale del servidor
- **Pulido UX**: glow en el hero, showcase de tarjetas de ejemplo, skeleton de carga, animación de entrada de la tarjeta, pills de región, cuenta atrás visual en 429
- **Confianza**: nota de privacidad (el Riot ID se envía a HenrikDev, se cachea ≤ 1 h, sin cookies), avisos de marcas, enlaces de contacto


### v3 — Más juegos e integraciones (planificado 📋)

- Provider CS2 (FACEIT Data API vs Leetify — fuente por decidir)
- Bot de Discord (`/stats`) reutilizando providers
- Paginación de partidas para K/D exacto de temporada completa
- Auto-detección de región (probar `eu`/`na`/`ap`/`kr` hasta obtener datos)

> **Sobre CS2:** Valve no expone una API pública para las estadísticas competitivas de CS2. Las alternativas o requieren verificación de identidad (FACEIT Data API) o dependen de que el jugador use un servicio de análisis de terceros (Leetify). El soporte de CS2 llegará en la v3, una vez elegida la fuente de datos.


## 🚀 Primeros pasos

### Requisitos previos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recomendado) o `pip` + `venv`
- Una clave de HenrikDev: [consíguela aquí](https://dashboard.henrikdev.xyz/)

### Instalación

```bash
# 1. Clona el repositorio
git clone https://github.com/angelclassasir/statcard.git
cd statcard

# 2. Instala las dependencias
uv sync

# 3. Configura tu clave de API
cp .env.example .env
# Edita .env y añade tu HENRIKDEV_API_KEY
```

### Uso

```bash
# Genera tu tarjeta de Valorant
python -m statcard valorant "TuNombre#TuTag"

# Fuerza una consulta fresca (sin usar caché)
python -m statcard valorant "TuNombre#TuTag" --no-cache

# Especifica una región distinta
python -m statcard valorant "TuNombre#TuTag" --region na
```
Las imágenes de salida se guardan en output/.

### Ejecutar la aplicación web localmente
Abre dos terminales en la raíz del repositorio:

```bash
# Terminal 1: arranca el backend FastAPI
uv run uvicorn statcard.web.app:app --port 8000

# Terminal 2: sirve el frontend estático
cd frontend
uv run python -m http.server 8080
```

Luego abre http://127.0.0.1:8080 en tu navegador. El frontend consultará al backend local en http://127.0.0.1:8000.

💡 FastAPI también sirve una Swagger UI auto-generada en http://127.0.0.1:8000/docs.

## Fuentes
El proyecto usa fuentes bajo la licencia SIL Open Font License:

    Chakra Petch (latín + tailandés) — incluida en el repo.
    Noto Sans KR / JP / SC + Noto Sans (respaldos CJK + cirílico) — pesadas (~40 MB en total), por lo que se descargan localmente y se ignoran en git. Ver assets/fonts/README.md para los comandos de descarga.


## 📁 Estructura del Proyecto
```text
statcard/
├── src/statcard/
│   ├── __init__.py
│   ├── __main__.py            # Punto de entrada del CLI (argparse)
│   ├── models.py              # Formato común de estadísticas (pydantic)
│   ├── cache.py               # Caché en disco con caducidad
│   ├── render.py              # Renderizado de tarjetas (Pillow)
│   ├── providers/
│   │   ├── __init__.py
│   │   └── valorant.py        # HenrikDev -> formato común
│   ├── themes/
│   │   ├── __init__.py
│   │   └── dark.py            # Colores, fuentes, tamaños
│   └── web/                   # Backend FastAPI (v2)
│       ├── app.py             # Fábrica de app + CORS + /healthz
│       ├── api.py             # Rutas /api/valorant (PNG + JSON)
│       ├── ratelimit.py       # Limitador con ventana deslizante (por IP + global)
│       └── settings.py        # Configuración por variables de entorno
├── frontend/                  # Web app estática (v2/v2.1) → Cloudflare Pages
│   ├── index.html             # Selector de juego, formulario, preview, showcase
│   ├── app.js                 # Fetch, validación, skeleton, cuenta atrás 429
│   ├── config.js              # URL del backend (Render)
│   ├── styles.css             # WOFF2 auto-alojadas, glow, animaciones, a11y
│   ├── 404.html               # Página "PLAYER NOT FOUND" temática
│   ├── _headers               # CSP, nosniff, Referrer-Policy, reglas de caché
│   ├── robots.txt             # Reglas de rastreo + referencia al sitemap
│   ├── sitemap.xml            # Sitemap de una página
│   ├── favicon.svg            # Marca de statcard
│   └── assets/
│       ├── fonts/             # Chakra Petch WOFF2 (auto-alojadas)
│       ├── logo-valorant.png  # Icono del selector (marca de terceros)
│       ├── logo-cs2.png       # Icono del selector (marca de terceros, v3)
│       ├── og-1200x630.png    # Preview social (scripts/render_social.py)
│       ├── showcase-1.png     # Tarjeta de ejemplo: Horcus
│       └── showcase-2.png     # Tarjeta de ejemplo: Mabi
├── assets/
│   └── fonts/                 # Fuentes SIL OFL en TTF (ver assets/fonts/README.md)
├── tests/
│   ├── fixtures/              # Respuestas guardadas de las APIs para tests offline
│   ├── test_valorant.py
│   ├── test_cache.py
│   ├── test_cli.py
│   └── test_web.py            # Tests de FastAPI con TestClient (offline)
├── scripts/
│   ├── smoke_valorant.py      # Verificación manual contra API real (Horcus#1995)
│   └── render_social.py       # Genera frontend/assets/og-1200x630.png
├── docs/
│   └── INFRASTRUCTURE.md      # Documento de diseño de la v2
├── examples/                  # Tarjetas de ejemplo para este README
├── output/                    # Tarjetas generadas (ignorado por git)
├── .env.example               # Plantilla para las claves de API
└── pyproject.toml
```

El principio de diseño clave es: cada juego tiene su propio provider que siempre devuelve el mismo formato común. El renderizador nunca sabe de dónde provienen los datos. Añadir un nuevo juego es simplemente escribir un módulo provider más.

## ⚖️ Avisos legales
Este es un proyecto educativo hecho por fans, sin ánimo de lucro.

    No está afiliado, respaldado ni patrocinado por Riot Games.
    Los datos de Valorant se obtienen a través de la API no oficial HenrikDev.

    Valorant y sus marcas comerciales son propiedad de Riot Games, Inc.
    Assets: todos los recursos visuales (fondos, iconos, fuentes) son originales, creados por el autor, o provienen de licencias libres/abiertas (SIL OFL).

## 📄 Licencia

Este proyecto usa una **licencia dual**:

- **Uso no comercial** (personal, educativo, hobby): gratuito bajo la [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0).
- **Uso comercial**: requiere autorización expresa y por escrito del autor. ¿Quieres usar statcard con fines comerciales? [Abre un issue](https://github.com/angelclassasir/statcard/issues) o contáctame para negociar una licencia comercial.

Consulta el archivo [LICENSE](LICENSE) para los términos completos.
