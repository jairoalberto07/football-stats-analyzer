# ⚽ Football Statistical Analyzer (Poisson & xG Engine)

Motor de analítica deportiva y modelado probabilístico desarrollado en **Python** para evaluar el rendimiento histórico de clubes y selecciones en ligas de Europa, Sudamérica y torneos internacionales, estimando goles esperados ($xG$) y probabilidades de resultados mediante la **Distribución de Poisson Bivariada**.

## 🚀 Características Principales

- **Cobertura Multi-Competición (`gestor_datos.py`):** Conector híbrido con caché local automática para analizar ligas europeas (Premier League, LaLiga, Serie A, Bundesliga, Ligue 1), sudamericanas (Brasileirão Série A, Liga Profesional Argentina, Liga BetPlay Dimayor) y torneos internacionales (UEFA Champions League, Selecciones).
- **Índices Relativos de Fuerza (`motor_poisson.py`):** Calcula factores ponderados de eficiencia ofensiva (ataque) y solidez defensiva en condición de local y visitante respecto al promedio global de cada competición.
- **Modelado Probabilístico de Poisson:** Construye matrices de probabilidad conjunta para estimar goles esperados ($\lambda$), probabilidades de resultado final (**1X2**), mercados de goles (**Over/Under 2.5**, **BTTS**) y el *Top 4* de marcadores exactos más probables.

## 🛠️ Tecnologías Utilizadas

- **Lenguaje:** Python 3.x
- **Ciencia de Datos y Estadística:** `pandas`, `numpy`, `scipy` (`scipy.stats.poisson`)
- **Integración HTTP:** `requests`

## 📂 Arquitectura del Proyecto

```text
football-stats-analyzer/
├── main.py                 # Interfaz interactiva CLI y presentación de informes
├── motor_poisson.py        # Algoritmo de fuerza ofensiva/defensiva y matrices de Poisson
├── gestor_datos.py         # Descarga, normalización y caché local de datasets por liga
├── requirements.txt        # Dependencias del proyecto
├── .gitignore              # Exclusión de cachés locales
└── datos/                  # Almacenamiento local de historiales CSV