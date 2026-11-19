import os
import io
import requests
import pandas as pd

CARPETA_DATOS = "datos"

# Catálogo de ligas con fuentes reales abiertas (Football-Data.co.uk) y soporte Sudamérica/Internacional
CATALOGO_COMPETICIONES = {
    "1": {
        "nombre": "Premier League (Inglaterra)",
        "codigo": "E0",
        "url": "https://www.football-data.co.uk/mmz4281/2526/E0.csv",
        "tipo": "csv_eu"
    },
    "2": {
        "nombre": "LaLiga EA Sports (España)",
        "codigo": "SP1",
        "url": "https://www.football-data.co.uk/mmz4281/2526/SP1.csv",
        "tipo": "csv_eu"
    },
    "3": {
        "nombre": "Serie A (Italia)",
        "codigo": "I1",
        "url": "https://www.football-data.co.uk/mmz4281/2526/I1.csv",
        "tipo": "csv_eu"
    },
    "4": {
        "nombre": "Bundesliga (Alemania)",
        "codigo": "D1",
        "url": "https://www.football-data.co.uk/mmz4281/2526/D1.csv",
        "tipo": "csv_eu"
    },
    "5": {
        "nombre": "Ligue 1 (Francia)",
        "codigo": "F1",
        "url": "https://www.football-data.co.uk/mmz4281/2526/F1.csv",
        "tipo": "csv_eu"
    },
    "6": {
        "nombre": "Brasileirão Série A (Brasil)",
        "codigo": "BRA",
        "url": "https://www.football-data.co.uk/new/BRA.csv",
        "tipo": "csv_extra"
    },
    "7": {
        "nombre": "Liga Profesional (Argentina)",
        "codigo": "ARG",
        "url": "https://www.football-data.co.uk/new/ARG.csv",
        "tipo": "csv_extra"
    },
    "8": {
        "nombre": "Liga BetPlay Dimayor (Colombia)",
        "codigo": "COL",
        "url": None,
        "tipo": "local_seed"
    },
    "9": {
        "nombre": "UEFA Champions League & Torneos Internacionales",
        "codigo": "UCL_INT",
        "url": None,
        "tipo": "local_seed"
    }
}

def _generar_dataset_base(codigo: str) -> pd.DataFrame:
    """Genera/carga datasets estructurados para ligas sin CSV abierto directo (Colombia / Torneos)."""
    if codigo == "COL":
        partidos = [
            ("Atletico Nacional", "Millonarios", 2, 1), ("America de Cali", "Junior", 2, 0),
            ("Independiente Medellin", "Deportes Tolima", 1, 1), ("Santa Fe", "Once Caldas", 2, 1),
            ("Millonarios", "America de Cali", 1, 0), ("Junior", "Atletico Nacional", 2, 2),
            ("Deportes Tolima", "Santa Fe", 2, 0), ("Once Caldas", "Independiente Medellin", 1, 0),
            ("Atletico Nacional", "America de Cali", 3, 1), ("Millonarios", "Junior", 2, 1),
            ("Santa Fe", "Atletico Nacional", 1, 1), ("America de Cali", "Deportes Tolima", 2, 1),
            ("Junior", "Once Caldas", 3, 1), ("Independiente Medellin", "Millonarios", 1, 2),
            ("Deportes Tolima", "Atletico Nacional", 1, 2), ("Once Caldas", "Santa Fe", 0, 1),
            ("Millonarios", "Deportes Tolima", 1, 0), ("Atletico Nacional", "Once Caldas", 2, 0),
            ("America de Cali", "Santa Fe", 1, 1), ("Junior", "Independiente Medellin", 2, 1),
            ("Deportivo Cali", "America de Cali", 1, 2), ("Bucaramanga", "Millonarios", 1, 1),
            ("Atletico Nacional", "Bucaramanga", 2, 1), ("Deportivo Cali", "Junior", 0, 2)
        ]
    else:
        # UEFA Champions League & Selecciones Internacionales
        partidos = [
            ("Real Madrid", "Manchester City", 3, 2), ("Bayern Munich", "Arsenal", 2, 1),
            ("Barcelona", "PSG", 3, 1), ("Inter Milan", "Atletico Madrid", 2, 0),
            ("Liverpool", "Real Madrid", 2, 1), ("Manchester City", "Bayern Munich", 2, 2),
            ("PSG", "Liverpool", 1, 2), ("Arsenal", "Inter Milan", 1, 0),
            ("Real Madrid", "Barcelona", 2, 1), ("Bayern Munich", "Inter Milan", 2, 1),
            ("Colombia", "Argentina", 2, 1), ("Brasil", "Uruguay", 1, 1),
            ("Argentina", "Brasil", 2, 0), ("Uruguay", "Colombia", 2, 2),
            ("España", "Francia", 2, 1), ("Alemania", "Inglaterra", 2, 2),
            ("Colombia", "Brasil", 2, 1), ("Argentina", "Colombia", 1, 0),
            ("Francia", "Inglaterra", 2, 1), ("España", "Alemania", 1, 1)
        ]
    return pd.DataFrame(partidos, columns=["local", "visitante", "goles_local", "goles_visitante"])

def cargar_datos_competicion(opcion: str, forzar_actualizacion: bool = False) -> tuple[str, pd.DataFrame]:
    """
    Descarga o carga desde caché local los resultados históricos de la liga seleccionada
    y los normaliza al formato estándar ['local', 'visitante', 'goles_local', 'goles_visitante'].
    """
    comp = CATALOGO_COMPETICIONES[opcion]
    os.makedirs(CARPETA_DATOS, exist_ok=True)
    ruta_local = os.path.join(CARPETA_DATOS, f"{comp['codigo']}.csv")

    if comp["tipo"] == "local_seed":
        if not os.path.exists(ruta_local) or forzar_actualizacion:
            df = _generar_dataset_base(comp["codigo"])
            df.to_csv(ruta_local, index=False)
        else:
            df = pd.read_csv(ruta_local)
        return comp["nombre"], df

    # Descarga desde fuente externa si no existe en caché o si el usuario pidió actualizar
    if not os.path.exists(ruta_local) or forzar_actualizacion:
        try:
            print(f"[INFO] Descargando datos actualizados de {comp['nombre']}...")
            resp = requests.get(comp["url"], timeout=15)
            resp.raise_for_status()
            raw_df = pd.read_csv(io.StringIO(resp.text))

            if comp["tipo"] == "csv_eu":
                df = raw_df[["HomeTeam", "AwayTeam", "FTHG", "FTAG"]].copy()
            else:
                # Ligas extra (Brasil, Argentina) toman las últimas 380 jornadas recientes
                df = raw_df[["Home", "Away", "HG", "AG"]].tail(380).copy()

            df.columns = ["local", "visitante", "goles_local", "goles_visitante"]
            df = df.dropna()
            df.to_csv(ruta_local, index=False)
            print(f"[OK] Dataset guardado en caché: {ruta_local} ({len(df)} partidos)")
            return comp["nombre"], df

        except Exception as e:
            print(f"[!] No se pudo conectar al servidor remoto ({e}).")
            if os.path.exists(ruta_local):
                print("[INFO] Cargando última copia disponible desde caché local...")
                return comp["nombre"], pd.read_csv(ruta_local)
            raise RuntimeError("No hay conexión a internet ni caché local disponible para esta liga.")

    df = pd.read_csv(ruta_local)
    return comp["nombre"], df