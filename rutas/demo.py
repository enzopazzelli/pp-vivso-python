"""
Demo end-to-end del generador de rutas, sobre el dataset existente.

    python -m rutas.demo

Arma un viaje real para un técnico con backlog, compara "mezcla" contra "solo
urgentes" y "2 y 1" contra "3 y 2", y muestra cuánto se ahorra agrupando visitas
en un viaje en vez de ir una por una — la ganancia que motiva todo el módulo.
"""
import pandas as pd

from rutas.parametros import HORAS_JORNADA, MODO_MEZCLA, MODO_SOLO_URGENTES, VIAJE_CORTO, VIAJE_LARGO
from rutas.planificador import Viaje, armar_viaje, simular_proximos_viajes
from rutas.prioridad import clasificar_pendiente


def _titulo(t: str) -> None:
    print("\n" + "=" * 74 + f"\n{t}\n" + "=" * 74)


def cargar_tecnico(tecnico_id: int):
    df_viv  = pd.read_csv("data/viviendas_sinteticas.csv")
    df_tec  = pd.read_csv("data/tecnicos.csv")
    df_asig = pd.read_csv("data/asignaciones.csv")
    df_vis  = pd.read_csv("data/visitas.csv")

    tec = df_tec[df_tec["id"] == tecnico_id].iloc[0]
    mis_ids = df_asig[df_asig["tecnico_id"] == tecnico_id]["vivienda_id"]
    mis_viv = df_viv[df_viv["num_exp"].isin(mis_ids)].copy()

    vis_tec = df_vis[df_vis["tecnico_id"] == tecnico_id]
    vis_por_viv = vis_tec.groupby("vivienda_id").size()
    mis_viv["visitas"] = mis_viv["num_exp"].map(vis_por_viv).fillna(0).astype(int)
    mis_viv["estado_visita"] = mis_viv.apply(clasificar_pendiente, axis=1)

    nombre = f"{tec['apellido']}, {tec['nombre']}"
    return mis_viv, tec["departamentos"], nombre


def _mostrar_viaje(viaje: Viaje) -> None:
    print(f"Técnico       : {viaje.tecnico}")
    print(f"Plantilla     : {viaje.plantilla['nombre']}")
    print(f"Base          : {viaje.base.localidad} ({viaje.base.departamento})")
    print(f"Paradas       : {len(viaje.paradas)}  "
          f"({viaje.urgentes_cubiertas} urgentes, {viaje.no_urgentes_cubiertas} de paso)")
    print(f"Urgentes que no entraron en este viaje: {viaje.urgentes_pendientes_fuera}")
    print(f"Km totales    : {viaje.km_totales:.0f} km")
    print(f"Horas totales : {viaje.horas_totales:.1f} h "
          f"(visitando una por una serían {viaje.horas_individual:.1f} h "
          f"→ ahorro de {viaje.horas_ahorradas:.1f} h)")
    print()
    for dia in viaje.dias:
        pernocte = f"pernocta en {dia.pernocta_en.localidad}" if dia.pernocta_en else "vuelve a la base"
        print(f"  Día {dia.numero} ({dia.horas_usadas:.1f}/{dia.presupuesto:.1f} h) — {pernocte}")
        for p in dia.paradas:
            marca = "🔴 urgente" if p.urgente else "🟢 de paso"
            print(f"    {marca}  {p.num_exp:<14} {p.localidad:<20} riesgo={p.nivel_riesgo}")


def main() -> None:
    # Técnico 3 (Ibáñez) es el "sobrecargado" del dataset — el caso donde un
    # generador de rutas rinde más: mucho backlog, zona con 3 departamentos.
    TECNICO_ID = 3
    mis_viv, departamentos, nombre = cargar_tecnico(TECNICO_ID)

    _titulo(f"Backlog de {nombre} — zona: {departamentos}")
    print(mis_viv["estado_visita"].value_counts().to_string())

    _titulo("Viaje '2 y 1', modo mezcla")
    viaje = armar_viaje(mis_viv, departamentos, nombre, VIAJE_CORTO, MODO_MEZCLA)
    _mostrar_viaje(viaje)

    _titulo("Mismo viaje, modo solo urgentes (para comparar)")
    viaje_solo = armar_viaje(mis_viv, departamentos, nombre, VIAJE_CORTO, MODO_SOLO_URGENTES)
    print(f"Paradas: {len(viaje_solo.paradas)}  "
          f"({viaje_solo.urgentes_cubiertas} urgentes, {viaje_solo.no_urgentes_cubiertas} de paso)")
    print("→ Acá da IGUAL que la mezcla: este técnico tiene tantas urgentes "
          f"({viaje.urgentes_cubiertas + viaje.urgentes_pendientes_fuera}) que ya llenan "
          "el viaje solas. Es un hallazgo real del backlog, no una falla del modo mezcla — "
          "se ve más abajo, con un técnico de backlog más chico, dónde sí aparece la diferencia.")

    _titulo("Dónde SÍ se nota la mezcla: un técnico con menos backlog urgente")
    mis_viv6, deptos6, nombre6 = cargar_tecnico(6)
    viajes6 = simular_proximos_viajes(mis_viv6, deptos6, nombre6, VIAJE_CORTO, MODO_MEZCLA,
                                      max_viajes=2)
    print(f"{nombre6} — zona: {deptos6}")
    for i, v in enumerate(viajes6, start=1):
        print(f"  Viaje {i}: {len(v.paradas)} paradas "
              f"({v.urgentes_cubiertas} urgentes, {v.no_urgentes_cubiertas} de paso)")
    print("→ En el viaje 2 ya no alcanzan las urgentes para llenar el presupuesto, y ahí "
          "la mezcla suma pendientes no urgentes que quedan de paso — la ruta no vuelve "
          "vacía aunque las urgentes se hayan agotado.")

    _titulo("Viaje '3 y 2', modo mezcla — más días, más alcance")
    viaje_largo = armar_viaje(mis_viv, departamentos, nombre, VIAJE_LARGO, MODO_MEZCLA)
    _mostrar_viaje(viaje_largo)

    _titulo("Próximos viajes hasta vaciar el backlog actual (plantilla '2 y 1')")
    viajes = simular_proximos_viajes(mis_viv, departamentos, nombre, VIAJE_CORTO, MODO_MEZCLA,
                                     max_viajes=5)
    total_paradas = sum(len(v.paradas) for v in viajes)
    total_horas   = sum(v.horas_totales for v in viajes)
    total_ahorro  = sum(v.horas_ahorradas for v in viajes)
    for i, v in enumerate(viajes, start=1):
        print(f"  Viaje {i}: {len(v.paradas)} paradas "
              f"({v.urgentes_cubiertas} urgentes) · {v.horas_totales:.1f} h · "
              f"{v.km_totales:.0f} km")
    print(f"\nTotal: {len(viajes)} viajes cubren {total_paradas} obras en {total_horas:.1f} h.")
    print(f"Visitándolas una por una habría costado {total_horas + total_ahorro:.1f} h "
          f"→ {total_ahorro:.1f} h ahorradas "
          f"({total_ahorro/HORAS_JORNADA:.1f} jornadas de {HORAS_JORNADA:.0f}h).")


if __name__ == "__main__":
    main()
