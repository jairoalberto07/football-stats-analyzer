import sys
from gestor_datos import CATALOGO_COMPETICIONES, cargar_datos_competicion
from motor_poisson import AnalizadorPoisson

def mostrar_competiciones():
    print("\n" + "=" * 68)
    print("   ANALIZADOR ESTADÍSTICO DE FÚTBOL - MODELO POISSON & xG")
    print("=" * 68)
    print("  EUROPA:")
    for k in ["1", "2", "3", "4", "5"]:
        print(f"    [{k}] {CATALOGO_COMPETICIONES[k]['nombre']}")
    print("\n  SUDAMÉRICA E INTERNACIONAL:")
    for k in ["6", "7", "8", "9"]:
        print(f"    [{k}] {CATALOGO_COMPETICIONES[k]['nombre']}")
    print("\n    [0] Salir")
    print("=" * 68)

def seleccionar_equipo(equipos: list, rol: str) -> str:
    print(f"\nEquipos disponibles ({rol}):")
    for idx, eq in enumerate(equipos, start=1):
        print(f"  {idx:2d}. {eq}", end="\t" if idx % 3 != 0 else "\n")
    print()

    while True:
        entrada = input(f"Seleccione el número del equipo {rol}: ").strip()
        if entrada.isdigit() and 1 <= int(entrada) <= len(equipos):
            return equipos[int(entrada) - 1]
        print("[!] Selección inválida. Ingrese un número de la lista.")

def imprimir_reporte_partido(nombre_liga: str, res: dict):
    print("\n" + "=" * 68)
    print(f"  INFORME PROBABILÍSTICO | {nombre_liga.upper()}")
    print(f"  ENCUENTRO: {res['local']} (Local) vs. {res['visitante']} (Visitante)")
    print("=" * 68)

    fl = res["fuerzas_local"]
    fv = res["fuerzas_visita"]
    print(f"\n[+] Índices de Rendimiento Relativo (1.00 = Promedio de la Liga):")
    print(f"    - {res['local']} (Casa): Ataque = {fl['ataque_local']} | Defensa = {fl['defensa_local']} (PJ: {fl['pj_local']})")
    print(f"    - {res['visitante']} (Fuera): Ataque = {fv['ataque_visita']} | Defensa = {fv['defensa_visita']} (PJ: {fv['pj_visita']})")

    print(f"\n[+] Goles Esperados (xG Estadístico Poisson):")
    print(f"    - {res['local']}: {res['xg_local']} goles")
    print(f"    - {res['visitante']}: {res['xg_visita']} goles")

    p1x2 = res["probabilidades_1x2"]
    print(f"\n[+] Probabilidades Resultado Final (1X2):")
    print(f"    - Victoria {res['local']} (1): {p1x2['victoria_local']}%")
    print(f"    - Empate (X):                {p1x2['empate']}%")
    print(f"    - Victoria {res['visitante']} (2): {p1x2['victoria_visita']}%")

    m = res["mercados"]
    print(f"\n[+] Mercados de Goles:")
    print(f"    - Más de 2.5 Goles (Over 2.5):   {m['over_2_5']}%")
    print(f"    - Menos de 2.5 Goles (Under 2.5): {m['under_2_5']}%")
    print(f"    - Ambos Equipos Marcan (BTTS):   {m['ambos_marcan_si']}%")

    print(f"\n[+] Marcadores Exactos Más Probables:")
    for marcador, prob in res["top_marcadores"]:
        print(f"    - {res['local']} {marcador} {res['visitante']} -> {prob}%")
    print("=" * 68)

def main():
    while True:
        mostrar_competiciones()
        opcion = input("\nSeleccione una competición [0-9]: ").strip()

        if opcion == "0":
            print("\nCerrando Analizador Estadístico Deportivo. ¡Éxitos en tus análisis!")
            sys.exit(0)

        if opcion not in CATALOGO_COMPETICIONES:
            print("[!] Opción no válida.")
            continue

        actualizar = input("¿Desea forzar descarga de datos frescos de internet? (s/n): ").strip().lower() == "s"

        try:
            nombre_liga, df = cargar_datos_competicion(opcion, forzar_actualizacion=actualizar)
        except Exception as e:
            print(f"[ERROR] {e}")
            continue

        motor = AnalizadorPoisson(df)
        equipos = motor.obtener_equipos()

        local = seleccionar_equipo(equipos, "LOCAL")
        visitante = seleccionar_equipo(equipos, "VISITANTE")

        if local == visitante:
            print("\n[!] Un equipo no puede enfrentarse a sí mismo. Intente de nuevo.")
            continue

        resultado = motor.predecir_partido(local, visitante)
        imprimir_reporte_partido(nombre_liga, resultado)

        input("\nPresione ENTER para analizar otro partido...")

if __name__ == "__main__":
    main()