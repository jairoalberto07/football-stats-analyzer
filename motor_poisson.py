import numpy as np
import pandas as pd
from scipy.stats import poisson

class AnalizadorPoisson:
    def __init__(self, df_partidos: pd.DataFrame):
        self.df = df_partidos.dropna(subset=['goles_local', 'goles_visitante']).copy()
        self.df['goles_local'] = self.df['goles_local'].astype(int)
        self.df['goles_visitante'] = self.df['goles_visitante'].astype(int)

        # Verificar si el dataset cuenta con estadísticas de tiros al arco
        self.tiene_tiros = (
            'tiros_arco_local' in self.df.columns and
            'tiros_arco_visita' in self.df.columns and
            self.df['tiros_arco_local'].notna().sum() > 10
        )
        if self.tiene_tiros:
            self.df['tiros_arco_local'] = pd.to_numeric(self.df['tiros_arco_local'], errors='coerce').fillna(0)
            self.df['tiros_arco_visita'] = pd.to_numeric(self.df['tiros_arco_visita'], errors='coerce').fillna(0)

        self._calcular_promedios_liga()

    def _calcular_promedios_liga(self):
        self.prom_goles_local = float(self.df['goles_local'].mean())
        self.prom_goles_visita = float(self.df['goles_visitante'].mean())

        if self.tiene_tiros:
            self.prom_tiros_local = float(self.df['tiros_arco_local'].mean())
            self.prom_tiros_visita = float(self.df['tiros_arco_visita'].mean())
        else:
            self.prom_tiros_local = 0.0
            self.prom_tiros_visita = 0.0

    def obtener_equipos(self):
        equipos = set(self.df['local'].unique()).union(set(self.df['visitante'].unique()))
        return sorted(list(equipos))

    def _promedio_ponderado_forma(self, serie: pd.Series, ventana: int = 5, peso_reciente: float = 0.65) -> float:
        """Combina el rendimiento reciente (últimos N partidos) con el global de la temporada."""
        if len(serie) == 0:
            return 0.0
        prom_global = float(serie.mean())
        if len(serie) <= ventana:
            return prom_global
        prom_reciente = float(serie.tail(ventana).mean())
        return (peso_reciente * prom_reciente) + ((1.0 - peso_reciente) * prom_global)

    def obtener_racha_reciente(self, equipo: str, ventana: int = 5) -> dict:
        """Extrae resultados de los últimos N partidos globales del equipo (G, E, P)."""
        partidos = self.df[(self.df['local'] == equipo) | (self.df['visitante'] == equipo)].tail(ventana)
        secuencia = []
        puntos = 0

        for _, fila in partidos.iterrows():
            if fila['local'] == equipo:
                gf, gc = fila['goles_local'], fila['goles_visitante']
            else:
                gf, gc = fila['goles_visitante'], fila['goles_local']

            if gf > gc:
                secuencia.append("G")
                puntos += 3
            elif gf == gc:
                secuencia.append("E")
                puntos += 1
            else:
                secuencia.append("P")

        return {
            "secuencia": secuencia,
            "puntos_obtenidos": puntos,
            "puntos_posibles": len(secuencia) * 3
        }

    def calcular_consistencia(self, equipo: str, es_local: bool) -> dict:
        """Calcula Porterías a Cero (Clean Sheets), Partidos Sin Anotar y Tiros al Arco."""
        sub = self.df[self.df['local'] == equipo] if es_local else self.df[self.df['visitante'] == equipo]
        if len(sub) == 0:
            sub = self.df[(self.df['local'] == equipo) | (self.df['visitante'] == equipo)]

        total = len(sub)
        if total == 0:
            return {"clean_sheets_pct": 0.0, "fail_to_score_pct": 0.0, "tiros_arco_prom": None}

        if es_local and len(self.df[self.df['local'] == equipo]) > 0:
            clean_sheets = int((sub['goles_visitante'] == 0).sum())
            fail_to_score = int((sub['goles_local'] == 0).sum())
            tiros_prom = round(float(sub['tiros_arco_local'].mean()), 2) if self.tiene_tiros else None
        else:
            clean_sheets = int((sub['goles_local'] == 0).sum())
            fail_to_score = int((sub['goles_visitante'] == 0).sum())
            tiros_prom = round(float(sub['tiros_arco_visita'].mean()), 2) if self.tiene_tiros else None

        return {
            "clean_sheets_pct": round((clean_sheets / total) * 100, 1),
            "fail_to_score_pct": round((fail_to_score / total) * 100, 1),
            "tiros_arco_prom": tiros_prom
        }

    def calcular_fuerzas_equipo(self, equipo: str):
        """
        Calcula índices relativos ponderados por forma reciente (65/35)
        e integrando tiros al arco (70% goles / 30% tiros a puerta) cuando están disponibles.
        """
        partidos_local = self.df[self.df['local'] == equipo]
        partidos_visita = self.df[self.df['visitante'] == equipo]

        # 1. Fuerza Local
        if len(partidos_local) > 0 and self.prom_goles_local > 0:
            gf_loc = self._promedio_ponderado_forma(partidos_local['goles_local'])
            gc_loc = self._promedio_ponderado_forma(partidos_local['goles_visitante'])
            ataque_goles_loc = gf_loc / self.prom_goles_local
            defensa_goles_loc = gc_loc / self.prom_goles_visita

            if self.tiene_tiros and self.prom_tiros_local > 0 and self.prom_tiros_visita > 0:
                tf_loc = self._promedio_ponderado_forma(partidos_local['tiros_arco_local'])
                tc_loc = self._promedio_ponderado_forma(partidos_local['tiros_arco_visita'])
                ataque_local = (0.70 * ataque_goles_loc) + (0.30 * (tf_loc / self.prom_tiros_local))
                defensa_local = (0.70 * defensa_goles_loc) + (0.30 * (tc_loc / self.prom_tiros_visita))
            else:
                ataque_local, defensa_local = ataque_goles_loc, defensa_goles_loc
        else:
            ataque_local, defensa_local = 1.0, 1.0

        # 2. Fuerza Visitante
        if len(partidos_visita) > 0 and self.prom_goles_visita > 0:
            gf_vis = self._promedio_ponderado_forma(partidos_visita['goles_visitante'])
            gc_vis = self._promedio_ponderado_forma(partidos_visita['goles_local'])
            ataque_goles_vis = gf_vis / self.prom_goles_visita
            defensa_goles_vis = gc_vis / self.prom_goles_local

            if self.tiene_tiros and self.prom_tiros_visita > 0 and self.prom_tiros_local > 0:
                tf_vis = self._promedio_ponderado_forma(partidos_visita['tiros_arco_visita'])
                tc_vis = self._promedio_ponderado_forma(partidos_visita['tiros_arco_local'])
                ataque_visita = (0.70 * ataque_goles_vis) + (0.30 * (tf_vis / self.prom_tiros_visita))
                defensa_visita = (0.70 * defensa_goles_vis) + (0.30 * (tc_vis / self.prom_tiros_local))
            else:
                ataque_visita, defensa_visita = ataque_goles_vis, defensa_goles_vis
        else:
            ataque_visita, defensa_visita = 1.0, 1.0

        return {
            "ataque_local": round(float(ataque_local), 3),
            "defensa_local": round(float(defensa_local), 3),
            "ataque_visita": round(float(ataque_visita), 3),
            "defensa_visita": round(float(defensa_visita), 3),
            "pj_local": int(len(partidos_local)),
            "pj_visita": int(len(partidos_visita))
        }

    def _aplicar_ajuste_dixon_coles(self, matriz: np.ndarray, lam_x: float, lam_y: float, rho: float = -0.07) -> np.ndarray:
        """Calibra las probabilidades de marcadores bajos (0-0, 1-0, 0-1, 1-1) para mayor realismo táctico."""
        m = matriz.copy()
        m[0, 0] *= max(0.0, 1.0 - (lam_x * lam_y * rho))
        m[1, 0] *= max(0.0, 1.0 + (lam_y * rho))
        m[0, 1] *= max(0.0, 1.0 + (lam_x * rho))
        m[1, 1] *= max(0.0, 1.0 - rho)
        suma = np.sum(m)
        return m / suma if suma > 0 else matriz

    def _generar_lectura_tactica(self, local: str, visita: str, p1x2: dict, mercados: dict, cons_l: dict, cons_v: dict) -> str:
        """Genera una interpretación estadística clara para apoyar la toma de decisiones."""
        fav_local = p1x2["victoria_local"]
        fav_visita = p1x2["victoria_visita"]

        if fav_local >= 60:
            base = f"Amplio favoritismo estadístico para {local} en casa ({fav_local}%), impulsado por su diferencial ofensivo y forma reciente."
        elif fav_visita >= 55:
            base = f"{visita} llega con ventaja probabilística a domicilio ({fav_visita}%), mostrando solidez fuera de casa."
        else:
            base = f"Duelo equilibrado sin dominio absoluto: la diferencia entre ambos es estrecha ({fav_local}% vs {fav_visita}%), con alta incidencia del empate ({p1x2['empate']}%)."

        if cons_l["clean_sheets_pct"] >= 45 and cons_v["clean_sheets_pct"] >= 40:
            extra = " Ambos equipos destacan por su orden defensivo (más del 40% de porterías a cero), favoreciendo un trámite cerrado."
        elif mercados["over_2_5"] >= 58:
            extra = f" Alta proyección ofensiva: existe un {mercados['over_2_5']}% de probabilidad de superar los 2.5 goles."
        else:
            extra = f" Mercado de goles moderado (Under 2.5 al {mercados['under_2_5']}%)."

        return base + extra

    def predecir_partido(self, equipo_local: str, equipo_visitante: str, max_goles: int = 7):
        f_local = self.calcular_fuerzas_equipo(equipo_local)
        f_visita = self.calcular_fuerzas_equipo(equipo_visitante)

        lambda_local = f_local['ataque_local'] * f_visita['defensa_visita'] * self.prom_goles_local
        lambda_visita = f_visita['ataque_visita'] * f_local['defensa_local'] * self.prom_goles_visita

        prob_local = [poisson.pmf(i, lambda_local) for i in range(max_goles + 1)]
        prob_visita = [poisson.pmf(j, lambda_visita) for j in range(max_goles + 1)]
        matriz_base = np.outer(prob_local, prob_visita)
        matriz = self._aplicar_ajuste_dixon_coles(matriz_base, lambda_local, lambda_visita)

        prob_gana_local = float(np.sum(np.tril(matriz, -1)) * 100)
        prob_empate = float(np.sum(np.diag(matriz)) * 100)
        prob_gana_visita = float(np.sum(np.triu(matriz, 1)) * 100)

        prob_over_25 = 0.0
        prob_btts = 0.0
        marcadores = []

        for i in range(max_goles + 1):
            for j in range(max_goles + 1):
                p = float(matriz[i, j] * 100)
                marcadores.append((f"{i} - {j}", p))
                if (i + j) > 2.5:
                    prob_over_25 += p
                if i > 0 and j > 0:
                    prob_btts += p

        top_marcadores = sorted(marcadores, key=lambda x: x[1], reverse=True)[:4]

        p1x2 = {
            "victoria_local": round(prob_gana_local, 2),
            "empate": round(prob_empate, 2),
            "victoria_visita": round(prob_gana_visita, 2)
        }
        mercados = {
            "over_2_5": round(prob_over_25, 2),
            "under_2_5": round(100 - prob_over_25, 2),
            "ambos_marcan_si": round(prob_btts, 2)
        }

        cons_local = self.calcular_consistencia(equipo_local, es_local=True)
        cons_visita = self.calcular_consistencia(equipo_visitante, es_local=False)
        racha_local = self.obtener_racha_reciente(equipo_local)
        racha_visita = self.obtener_racha_reciente(equipo_visitante)

        return {
            "local": equipo_local,
            "visitante": equipo_visitante,
            "modelo_activo": "Híbrido (Forma 65/35 + Tiros al Arco + Dixon-Coles)" if self.tiene_tiros else "Ponderado (Forma 65/35 + Dixon-Coles)",
            "tiene_tiros": self.tiene_tiros,
            "xg_local": round(float(lambda_local), 2),
            "xg_visita": round(float(lambda_visita), 2),
            "probabilidades_1x2": p1x2,
            "mercados": mercados,
            "top_marcadores": [(m, round(p, 2)) for m, p in top_marcadores],
            "fuerzas_local": f_local,
            "fuerzas_visita": f_visita,
            "consistencia_local": cons_local,
            "consistencia_visita": cons_visita,
            "racha_local": racha_local,
            "racha_visita": racha_visita,
            "lectura_tactica": self._generar_lectura_tactica(equipo_local, equipo_visitante, p1x2, mercados, cons_local, cons_visita)
        }