   **Language:** [English](README.md) | [Español](README.es.md)

# 🎴 StatCard

> Genera tarjetas visuales con tus estadísticas de tus juegos FPS favoritos.

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**Idioma:** [English](README.md) | **Español**

---

`statcard` obtiene tus estadísticas de **Valorant**, **CS2 (FACEIT)** y **CS2 (Premier/MM)**, las unifica en un formato común y las renderiza en una tarjeta PNG lista para compartir en Discord, redes sociales o tu perfil de GitHub.

> ⚠️ **Estado del proyecto:** En desarrollo activo (Fase 1). Construyendo la base del backend y las integraciones con las APIs.

---

## ✨ Características

- 🎮 **Soporte multi-juego**
  - **Valorant** mediante [HenrikDev API](https://docs.henrikdev.xyz)
  - **CS2 (FACEIT)** mediante la API oficial de FACEIT
  - **CS2 (Premier/MM)** mediante Leetify
- 🎨 **Tema oscuro unificado** en todas las tarjetas
- 🖼️ **Fondos dinámicos** seleccionados según tus estadísticas (agentes, mapas, rangos)
- 💾 **Caché inteligente en disco** para respetar los límites de peticiones de las APIs
- ⚡ **Diseño CLI-first**: un comando, una tarjeta
- 🌐 **Interfaz web** *(planificada)*: genera tu tarjeta sin instalar nada

## 🖼️ Ejemplos

> Las tarjetas aparecerán aquí cuando se complete la Fase 2.

| Valorant | CS2 (FACEIT) | CS2 (Premier) |
| :---: | :---: | :---: |
| *Próximamente* | *Próximamente* | *Próximamente* |

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
| Futura API web | FastAPI + Cloudflare Pages |

## 🗺️ Hoja de ruta

| Fase | Descripción | Estado |
| :---: | --- | :---: |
| 0 | Configuración del repositorio y estructura inicial | ✅ Hecho |
| 1 | Integración con la API de Valorant (HenrikDev) + modelos de datos | 🚧 En curso |
| 2 | Primer renderizado de tarjeta con Pillow + tema oscuro | ⬜ |
| 3 | Caché en disco + gestión de errores | ⬜ |
| 4 | Integración con CS2 (FACEIT) | ⬜ |
| 5 | Integración con CS2 (Premier/MM) vía Leetify | ⬜ |
| 6 | Pulido del CLI, tests y CI | ⬜ |
| 7 | Presentación: README, ejemplos, avisos legales | ⬜ |
| 8 | *(Futuro)* Backend FastAPI + frontend web | ⬜ |
| 9 | *(Opcional)* Bot de Discord con comando `/stats` | ⬜ |

## 🚀 Primeros pasos

### Requisitos previos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recomendado) o `pip` + `venv`
- Claves de API:
  - **Valorant:** [Panel de HenrikDev](https://dashboard.henrikdev.xyz/)
  - **CS2 (FACEIT):** [FACEIT Developers](https://developers.faceit.com/)
  - **CS2 (Premier/MM):** Leetify API

### Instalación

```bash
# 1. Clona el repositorio
git clone https://github.com/angelclassasir/statcard.git
cd statcard

# 2. Instala las dependencias
uv sync

# 3. Configura tus claves de API
cp .env.example .env
# Edita .env y añade tus claves
```

### Uso

```bash
# Valorant
python -m statcard valorant "NombreJugador#TAG"

# CS2 via FACEIT
python -m statcard faceit "tu_nickname_faceit"

# CS2 Premier/MM via Leetify
python -m statcard cs2 "tu_steamid"
```
Las imágenes de salida se guardan en output/.

### 📁 Estructura del Proyecto
statcard/
├── src/statcard/
│   ├── __main__.py       # Punto de entrada CLI
│   ├── models.py         # Formato común de estadísticas (pydantic)
│   ├── cache.py          # Caché en disco con expiración
│   ├── render.py         # Renderizado de tarjetas (Pillow)
│   ├── providers/
│   │   ├── valorant.py   # HenrikDev → formato común
│   │   ├── faceit.py     # FACEIT → formato común
│   │   └── cs2.py        # Leetify → formato común
│   └── themes/
│       └── dark.py       # Colores, fuentes, tamaños
├── assets/               # Fuentes, iconos, fondos (licencias gratuitas)
├── tests/
│   ├── fixtures/         # Respuestas API guardadas para testing offline
│   └── test_*.py
├── examples/             # Tarjetas de ejemplo para este README
├── output/               # Tarjetas generadas (ignorado por git)
├── .env.example          # Plantilla para claves de API
└── pyproject.toml

El principio de diseño clave es: cada juego tiene su propio provider que siempre devuelve el mismo formato común. El renderizador nunca sabe de dónde provienen los datos. Añadir un nuevo juego es simplemente escribir un módulo provider más.

### ⚖️ Avisos Legales
Este es un proyecto educativo de fans, sin fines comerciales.

    No está afiliado, respaldado ni patrocinado por Riot Games, Valve Corporation, FACEIT o Leetify.
    Los datos de Valorant se obtienen a través de la API no oficial de HenrikDev.
    Los datos de CS2 se obtienen a través de la API oficial de FACEIT y/o Leetify, con el debido reconocimiento.
    Assets: Todos los recursos visuales (fondos, iconos, fuentes) son originales, creados por mí o con licencias gratuitas/open-source. Las marcas registradas de los juegos pertenecen a sus respectivos dueños.

### 📄 Licencia
Este proyecto está licenciado bajo la Licencia MIT.
