import numpy as np
import pandas as pd
from scipy.stats import poisson

class AnalizadorPoisson:
    def __init__(self, df_partidos: pd.DataFrame):
        """
        Inicializa el modelo con un DataFrame que contiene columnas:
        ['local', 'visitante', 'goles_local', 'goles_visitante']
        """
        self.df = df_partidos.dropna(subset=['goles_local', 'goles_visitante']).copy()
        self.df['goles_local'] = self.df['goles_local'].astype(int)
        self.df['goles_visitante'] = self.df['goles_visitante'].astype(int)
        self._calcular_promedios_liga()

    def _calcular_promedios_liga(self):
        """Calcula los promedios globales de goles en casa y fuera en la competición."""
        self.prom_goles_local = self.df['goles_local'].mean()
        self.prom_goles_visita = self.df['goles_visitante'].mean()

    def obtener_equipos(self):
        """Retorna la lista ordenada de equipos disponibles en el dataset."""
        equipos = set(self.df['local'].unique()).union(set(self.df['visitante'].unique()))
        return sorted(list(equipos))

    def calcular_fuerzas_equipo(self, equipo: str):
        """
        Calcula índices relativos de ataque y defensa como local y como visitante.
        Un índice > 1.0 en ataque indica rendimiento superior al promedio de la liga.
        Un índice < 1.0 en defensa indica mayor solidez defensiva que el promedio.
        """
        partidos_local = self.df[self.df['local'] == equipo]
        partidos_visita = self.df[self.df['visitante'] == equipo]

        # Fuerza como local
        if len(partidos_local) > 0 and self.prom_goles_local > 0:
            ataque_local = partidos_local['goles_local'].mean() / self.prom_goles_local
            defensa_local = partidos_local['goles_visitante'].mean() / self.prom_goles_visita
        else:
            ataque_local, defensa_local = 1.0, 1.0

        # Fuerza como visitante
        if len(partidos_visita) > 0 and self.prom_goles_visita > 0:
            ataque_visita = partidos_visita['goles_visitante'].mean() / self.prom_goles_visita
            defensa_visita = partidos_visita['goles_local'].mean() / self.prom_goles_local
        else:
            ataque_visita, defensa_visita = 1.0, 1.0

        return {
            "ataque_local": round(ataque_local, 3),
            "defensa_local": round(defensa_local, 3),
            "ataque_visita": round(ataque_visita, 3),
            "defensa_visita": round(defensa_visita, 3),
            "pj_local": len(partidos_local),
            "pj_visita": len(partidos_visita)
        }

    def predecir_partido(self, equipo_local: str, equipo_visitante: str, max_goles: int = 7):
        """
        Calcula goles esperados (Lambda/xG) y matriz de probabilidades (0-0 hasta max_goles).
        """
        f_local = self.calcular_fuerzas_equipo(equipo_local)
        f_visita = self.calcular_fuerzas_equipo(equipo_visitante)

        # Lambda (Goles esperados para cada equipo)
        lambda_local = f_local['ataque_local'] * f_visita['defensa_visita'] * self.prom_goles_local
        lambda_visita = f_visita['ataque_visita'] * f_local['defensa_local'] * self.prom_goles_visita

        # Matriz de probabilidades de marcadores exactos
        prob_local = [poisson.pmf(i, lambda_local) for i in range(max_goles + 1)]
        prob_visita = [poisson.pmf(j, lambda_visita) for j in range(max_goles + 1)]
        matriz = np.outer(prob_local, prob_visita)

        # Probabilidades 1X2
        prob_gana_local = np.sum(np.tril(matriz, -1)) * 100
        prob_empate = np.sum(np.diag(matriz)) * 100
        prob_gana_visita = np.sum(np.triu(matriz, 1)) * 100

        # Mercados adicionales: Over/Under 2.5 y Ambos Marcan (BTTS)
        prob_over_25 = 0.0
        prob_btts = 0.0
        marcadores = []

        for i in range(max_goles + 1):
            for j in range(max_goles + 1):
                p = matriz[i, j] * 100
                marcadores.append((f"{i} - {j}", p))
                if (i + j) > 2.5:
                    prob_over_25 += p
                if i > 0 and j > 0:
                    prob_btts += p

        # Ordenar marcadores exactos más probables
        top_marcadores = sorted(marcadores, key=lambda x: x[1], reverse=True)[:4]

        return {
            "local": equipo_local,
            "visitante": equipo_visitante,
            "xg_local": round(lambda_local, 2),
            "xg_visita": round(lambda_visita, 2),
            "probabilidades_1x2": {
                "victoria_local": round(prob_gana_local, 2),
                "empate": round(prob_empate, 2),
                "victoria_visita": round(prob_gana_visita, 2)
            },
            "mercados": {
                "over_2_5": round(prob_over_25, 2),
                "under_2_5": round(100 - prob_over_25, 2),
                "ambos_marcan_si": round(prob_btts, 2)
            },
            "top_marcadores": [(m, round(p, 2)) for m, p in top_marcadores],
            "fuerzas_local": f_local,
            "fuerzas_visita": f_visita
        }