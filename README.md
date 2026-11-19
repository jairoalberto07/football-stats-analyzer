cat << 'EOF' > README.md
# Football Statistical Analyzer (Web & API)

Plataforma web y motor de analítica deportiva multi-liga que calcula probabilidades de resultados, goles esperados ($xG$), marcadores exactos y métricas de consistencia utilizando **Distribución de Poisson con ajuste de Dixon-Coles**.

## Características Principales

- **Motor Probabilístico Híbrido (`motor_poisson.py`):**
  - **Ponderación por Forma Reciente (65/35):** Combina el rendimiento de los últimos 5 partidos (65%) con el global de la temporada (35%) y genera la secuencia visual (`G/E/P`).
  - **$xG$ Híbrido con Tiros al Arco:** Integra efectividad de gol (70%) y volumen de remates a puerta (`HST`/`AST`, 30%) en ligas europeas para reducir el ruido estadístico.
  - **Ajuste Dixon-Coles:** Calibra marcadores bajos (`0-0`, `1-0`, `0-1`, `1-1`) para mayor precisión en duelos cerrados.
  - **Consistencia & Lectura Táctica:** Evalúa porterías a cero (*Clean Sheets*), partidos sin anotar y genera una interpretación táctica automática.
- **Conector Multi-Liga (`gestor_datos.py`):** Sincronización y caché local para Premier League, LaLiga, Serie A, Bundesliga, Ligue 1, Brasileirão, Liga Argentina, Liga BetPlay y torneos internacionales.
- **Backend & Dashboard Interactivo (`app.py` + `static/index.html`):** API REST desarrollada con **FastAPI** y panel analítico con **Tailwind CSS** y **Chart.js**.

## Instalación y Ejecución Local

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt