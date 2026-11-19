import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from gestor_datos import CATALOGO_COMPETICIONES, cargar_datos_competicion
from motor_poisson import AnalizadorPoisson

app = FastAPI(
    title="Football Statistical Analyzer API",
    description="API de analítica deportiva y predicción probabilística basada en Distribución de Poisson y xG",
    version="1.0.0"
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

class SolicitudPrediccion(BaseModel):
    competicion_id: str
    local: str
    visitante: str

def sanitizar_json(obj):
    """Convierte tipos escalares de NumPy a tipos nativos de Python."""
    if isinstance(obj, dict):
        return {k: sanitizar_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitizar_json(i) for i in obj]
    if hasattr(obj, "item"):
        return obj.item()
    return obj

@app.get("/")
def servir_portal():
    return FileResponse("static/index.html")

@app.get("/api/competiciones")
def listar_competiciones():
    lista = []
    for k, v in CATALOGO_COMPETICIONES.items():
        region = "Europa" if k in ["1", "2", "3", "4", "5"] else "Sudamérica e Internacional"
        lista.append({
            "id": k,
            "nombre": v["nombre"],
            "codigo": v["codigo"],
            "region": region
        })
    return lista

@app.get("/api/equipos/{competicion_id}")
def listar_equipos(competicion_id: str, actualizar: bool = False):
    if competicion_id not in CATALOGO_COMPETICIONES:
        raise HTTPException(status_code=404, detail="Competición no encontrada.")

    try:
        nombre_liga, df = cargar_datos_competicion(competicion_id, forzar_actualizacion=actualizar)
        motor = AnalizadorPoisson(df)
        return {
            "competicion": nombre_liga,
            "total_partidos": len(df),
            "equipos": motor.obtener_equipos()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predecir")
def predecir_encuentro(solicitud: SolicitudPrediccion):
    if solicitud.competicion_id not in CATALOGO_COMPETICIONES:
        raise HTTPException(status_code=404, detail="Competición no válida.")

    if solicitud.local == solicitud.visitante:
        raise HTTPException(status_code=400, detail="El equipo local y visitante deben ser diferentes.")

    try:
        nombre_liga, df = cargar_datos_competicion(solicitud.competicion_id, forzar_actualizacion=False)
        motor = AnalizadorPoisson(df)
        resultado = motor.predecir_partido(solicitud.local, solicitud.visitante)
        resultado["competicion"] = nombre_liga
        return sanitizar_json(resultado)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
