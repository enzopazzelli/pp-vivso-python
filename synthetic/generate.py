"""
Genera datos sintéticos representativos del programa de viviendas sociales
de Santiago del Estero y los carga en la base de datos local.

La distribución geográfica, los estados y las clasificaciones siguen
proporciones basadas en los datos reales del ministerio.

Uso:
    python -m synthetic.generate          # genera 1500 viviendas (default)
    python -m synthetic.generate --n 500  # cantidad personalizada
"""
import argparse
import os
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import create_engine
from tqdm import tqdm

load_dotenv()

fake = Faker("es_AR")
random.seed(42)
np.random.seed(42)

DB_PATH = os.getenv("DB_PATH", "db/vivso_local.db")

# ---------------------------------------------------------------------------
# Distribución geográfica real de Santiago del Estero
# Los pesos reflejan la concentración poblacional de cada departamento
# ---------------------------------------------------------------------------
LOCALIDADES = [
    {"departamento": "Capital",         "localidad": "Santiago del Estero", "lat": -27.795, "lng": -64.261, "peso": 0.22},
    {"departamento": "Banda",           "localidad": "La Banda",            "lat": -27.735, "lng": -64.240, "peso": 0.16},
    {"departamento": "Robles",          "localidad": "Fernández",           "lat": -27.927, "lng": -63.887, "peso": 0.07},
    {"departamento": "Silípica",        "localidad": "Clodomira",           "lat": -27.571, "lng": -64.133, "peso": 0.06},
    {"departamento": "Choya",           "localidad": "Frías",               "lat": -28.648, "lng": -65.137, "peso": 0.06},
    {"departamento": "Moreno",          "localidad": "Quimilí",             "lat": -27.638, "lng": -62.413, "peso": 0.05},
    {"departamento": "Jiménez",         "localidad": "Añatuya",             "lat": -28.460, "lng": -62.841, "peso": 0.05},
    {"departamento": "Figueroa",        "localidad": "Suncho Corral",       "lat": -28.558, "lng": -63.443, "peso": 0.04},
    {"departamento": "Mitre",           "localidad": "Bandera",             "lat": -29.274, "lng": -62.268, "peso": 0.04},
    {"departamento": "General Taboada", "localidad": "Añatuya",             "lat": -28.471, "lng": -62.829, "peso": 0.04},
    {"departamento": "Copo",            "localidad": "Monte Quemado",       "lat": -25.800, "lng": -62.831, "peso": 0.03},
    {"departamento": "Ojo de Agua",     "localidad": "Ojo de Agua",         "lat": -29.509, "lng": -63.697, "peso": 0.03},
    {"departamento": "Salavina",        "localidad": "Los Telares",         "lat": -29.221, "lng": -63.520, "peso": 0.03},
    {"departamento": "Atamisqui",       "localidad": "Villa Atamisqui",     "lat": -28.481, "lng": -63.821, "peso": 0.03},
    {"departamento": "Aguirre",         "localidad": "Nueva Esperanza",     "lat": -27.652, "lng": -62.418, "peso": 0.03},
    {"departamento": "Guasayán",        "localidad": "El Charco",           "lat": -28.064, "lng": -65.023, "peso": 0.02},
    {"departamento": "Rivadavia",       "localidad": "Pinto",               "lat": -29.153, "lng": -61.897, "peso": 0.02},
    {"departamento": "Pellegrini",      "localidad": "Tintina",             "lat": -27.034, "lng": -62.716, "peso": 0.02},
]

BARRIOS = [
    "Belgrano", "Centro", "San Martín", "Rivadavia", "FONAVI", "Villa del Parque",
    "Los Aromos", "Palermo", "25 de Mayo", "Villa Hogar", "La Reducción", "Catamarca",
    "Villa Luján", "San Jorge", "4 de Junio", "Norte", "Sur", "Autonomía",
    "Villa Jardín", "Los Ejidos", "Malvinas", "Santa Rosa", "Centenario", None,
]

CUITS_ONG = [
    "30-71782995-2",
    "30-68902314-5",
    "30-59804127-3",
]

# ---------------------------------------------------------------------------
# Plazo contractual de la etapa de construcción, en días. FUENTE ÚNICA DE VERDAD:
# define el modelo de riesgo (una obra que lo supera y no avanza está en riesgo)
# y el cronograma de referencia. Si el plazo cambia, se cambia solo acá.
# ---------------------------------------------------------------------------
PLAZO_CONSTRUCCION_DIAS = 90

# Probabilidades basadas en el programa real
ESTADOS_PROB = {"Iniciada": 0.35, "Avanzada": 0.25, "Finalizada": 0.25, "Adjudicada": 0.15}
TIPO_PROB    = {"Urbana": 0.55, "Rural": 0.38, "Económica": 0.07}
DORM_PROB    = {2: 0.60, 3: 0.25, 1: 0.15}

# Sistema completo de clasificaciones del programa (sistema legacy VISOC — docs/tipos.jpeg)
# criterio: Inclusion = apta para el programa | Exclusion = rechazada | Otro = caso especial
CLASIFICACIONES = {
    '1a': ('Inclusion',  'Vivienda Rancho'),
    '2a': ('Inclusion',  'Vivienda Precaria'),
    '2b': ('Inclusion',  'Vivienda c/ riesgo de derrumbe'),
    '3a': ('Inclusion',  'Vivienda c/ integrantes discapacitados'),
    '4a': ('Otro',       'Viviendas Mixtas (rancho y hab. c/ material)'),
    '4b': ('Otro',       'Unidad de Material c/ Techo de Chapa/Losa'),
    '4c': ('Otro',       'Vivienda de Material con techo de chapa/losa'),
    '5a': ('Exclusion',  'Viviendas Abandonadas'),
    '5b': ('Exclusion',  'Viviendas precarias sin antigüedad'),
    '5c': ('Exclusion',  'Viviendas precarias con conflicto de titularidad'),
    '5d': ('Exclusion',  'Asentamientos espontáneos'),
    '5e': ('Exclusion',  'Rancho ya posee vivienda del gobierno'),
    '5f': ('Otro',       'No posee Vivienda / tiene terreno para la vivienda'),
    '5g': ('Exclusion',  'Vivienda Rechazada'),
    'OT': ('Otro',       'Otro'),
}

# Distribución de frecuencia por código (refleja la realidad del programa)
CLASIF_PROB = {
    '1a': 0.18, '2a': 0.24, '2b': 0.12, '3a': 0.06,
    '4a': 0.05, '4b': 0.08, '4c': 0.05, '5f': 0.05, 'OT': 0.03,
    '5a': 0.02, '5b': 0.04, '5c': 0.03, '5d': 0.02, '5e': 0.02, '5g': 0.01,
}

# Rubros del AFO con su peso porcentual (suma = 100) — docs/afo.jpeg
RUBROS_DEF = [
    {"id": 1,  "peso": 3},
    {"id": 2,  "peso": 5},
    {"id": 3,  "peso": 10},
    {"id": 4,  "peso": 10},
    {"id": 5,  "peso": 5},
    {"id": 6,  "peso": 10},
    {"id": 7,  "peso": 8},
    {"id": 8,  "peso": 5},
    {"id": 9,  "peso": 4},
    {"id": 10, "peso": 10},
    {"id": 11, "peso": 7},
    {"id": 12, "peso": 8},
    {"id": 13, "peso": 7},
    {"id": 14, "peso": 5},
    {"id": 15, "peso": 3},
]


def _avance_coherente(estado: str) -> int:
    rangos = {
        "Iniciada":   (0,  35),
        "Avanzada":   (36, 79),
        "Finalizada": (80, 100),
        "Adjudicada": (100, 100),
    }
    lo, hi = rangos[estado]
    return random.randint(lo, hi)


def _fecha_inicio(estado: str) -> date:
    # Nota: faker interpreta 'd' como días e 'y' como años (NO usar 'm' = minutos).
    if estado in ("Finalizada", "Adjudicada"):
        return fake.date_between(start_date="-3y", end_date="-90d")
    # Activas: mezcla realista respecto del plazo de 90 días.
    # ~35% arrancaron hace poco (dentro de plazo); ~65% ya lo superaron (atraso crónico).
    if random.random() < 0.35:
        return fake.date_between(start_date="-90d", end_date="-5d")    # dentro de plazo
    return fake.date_between(start_date="-600d", end_date="-100d")     # pasada de plazo


def _dias_activa(fecha_inic: date, fecha_fin: date | None) -> int:
    fin = fecha_fin or date.today()
    return (fin - fecha_inic).days


def _fijar_dias_activa(df: pd.DataFrame, idx, lo: int, hi: int, rng) -> None:
    """
    Para obras ACTIVAS: fija fecha_inic = hoy - duración (en [lo, hi)) y limpia fecha_fin.
    Mantiene las fechas como única fuente de verdad — dias_activa y riesgo se derivan
    de ellas al final, así nunca quedan desincronizados.
    """
    hoy = date.today()
    for i in np.atleast_1d(np.asarray(idx)):
        d = int(rng.integers(lo, hi))
        df.at[i, "fecha_inic"] = (hoy - timedelta(days=d)).strftime("%d-%m-%Y")
        df.at[i, "fecha_fin"]  = None


def generar_viviendas(n: int) -> pd.DataFrame:
    pesos_loc = [l["peso"] for l in LOCALIDADES]
    registros = []

    for i in tqdm(range(1, n + 1), desc="Generando viviendas"):
        loc    = random.choices(LOCALIDADES, weights=pesos_loc)[0]
        estado = random.choices(list(ESTADOS_PROB), weights=list(ESTADOS_PROB.values()))[0]
        clasif = random.choices(list(CLASIF_PROB),  weights=list(CLASIF_PROB.values()))[0]
        tipo   = random.choices(list(TIPO_PROB),    weights=list(TIPO_PROB.values()))[0]
        dorm   = random.choices(list(DORM_PROB),    weights=list(DORM_PROB.values()))[0]

        f_ini = _fecha_inicio(estado)
        f_fin = None
        if estado in ("Finalizada", "Adjudicada"):
            # Duración de construcción: el plazo es 90 días, en la práctica se estira (60–300).
            f_fin = f_ini + timedelta(days=random.randint(60, 300))

        # Ruido gaussiano en coordenadas (~2 km de dispersión)
        lat = round(loc["lat"] + np.random.normal(0, 0.018), 6)
        lng = round(loc["lng"] + np.random.normal(0, 0.018), 6)

        avance    = _avance_coherente(estado)
        dias_act  = _dias_activa(f_ini, f_fin)
        cuit_org  = random.choice(CUITS_ONG) if random.random() > 0.20 else None
        criterio  = CLASIFICACIONES[clasif][0]

        # nivel_riesgo y dias_activa se recalculan al final en recalcular_derivados(),
        # tomando las fechas como única fuente de verdad. Acá va un valor inicial.
        nivel_riesgo = "bajo"

        registros.append({
            "num_exp":         f"SIM-{f_ini.year}-{i:04d}",
            "departamento":    loc["departamento"],
            "localidad":       loc["localidad"],
            "barrio":          random.choice(BARRIOS),
            "direccion":       fake.street_address(),
            "superficie":      max(30, round(np.random.normal(44, 7))),
            "fecha_inic":      f_ini.strftime("%d-%m-%Y"),
            "fecha_fin":       f_fin.strftime("%d-%m-%Y") if f_fin else None,
            "estado":          estado,
            "lat":             lat,
            "lng":             lng,
            "avance_obra":     avance,
            "clasificacion":   clasif,
            "criterio":        criterio,
            "tipo_vivienda":   tipo,
            "cant_dormitorios":dorm,
            "observacion":     None,
            "id_familia":      i,
            "representante":   f"{fake.last_name()}, {fake.first_name()}",
            "cuit_org":        cuit_org,
            "nivel_riesgo":    nivel_riesgo,
            "cluster":         None,   # se calcula en el notebook de minería
            "dias_activa":     dias_act,
        })

    return pd.DataFrame(registros)


def garantizar_casos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Da un perfil diferenciado a cada ONG para que los gráficos muestren
    contrastes claros entre organizaciones que funcionan bien y mal.

    Perfiles asignados:
    - COOP SAN ANTONIO (30-71782995-2): ONG eficiente — obras con buen avance,
      pocos días activa, casi sin riesgo. Caso "referencia positiva".

    - CONSTRUIR JUNTOS (30-68902314-5): ONG con problemas — obras estancadas,
      muchos días sin avanzar, alto porcentaje en riesgo. Caso "alerta".

    - MUTUAL PROGRESO (30-59804127-3): FINALIZADA — todas sus obras terminadas.
      Sirve de contraste histórico.

    También garantiza diversidad en clasificaciones, estados y casos sin ONG.
    """
    df = df.copy()
    rng = np.random.default_rng(42)

    # Nota: estos perfiles fijan avance, estado y FECHAS (vía _fijar_dias_activa).
    # El nivel_riesgo NO se asigna a mano — lo deriva recalcular_derivados() a partir
    # del plazo de 90 días, así el contraste entre ONGs surge solo de los datos.

    # ── ONG eficiente: COOP SAN ANTONIO ─────────────────────────────────────
    # Obras dentro de plazo con buen avance → la regla las marcará "bajo"
    cuit_buena = "30-71782995-2"
    idx_buena  = df[df['cuit_org'] == cuit_buena].index

    n_buenas = int(len(idx_buena) * 0.70)
    idx_ok   = rng.choice(idx_buena, size=n_buenas, replace=False)
    df.loc[idx_ok, 'avance_obra'] = rng.integers(55, 100, size=n_buenas)
    _fijar_dias_activa(df, idx_ok, 20, 88, rng)        # dentro del plazo de 90
    for i in idx_ok:
        av = df.at[i, 'avance_obra']
        df.at[i, 'estado'] = 'Finalizada' if av == 100 else ('Avanzada' if av >= 36 else 'Iniciada')

    # Solo 2 obras vencidas y estancadas (para que aparezca riesgo pero no domine)
    idx_riesgo_buena = rng.choice(
        df[(df['cuit_org'] == cuit_buena) & df['estado'].isin(['Iniciada','Avanzada'])].index,
        size=min(2, len(df[df['cuit_org'] == cuit_buena])),
        replace=False
    )
    df.loc[idx_riesgo_buena, 'avance_obra'] = rng.integers(8, 18, size=len(idx_riesgo_buena))
    df.loc[idx_riesgo_buena, 'estado']      = 'Iniciada'
    _fijar_dias_activa(df, idx_riesgo_buena, 150, 320, rng)   # muy pasadas de plazo

    # ── ONG con problemas: CONSTRUIR JUNTOS ──────────────────────────────────
    # Obras vencidas y estancadas → la regla las marcará "alto"/"medio"
    cuit_mala = "30-68902314-5"
    idx_mala  = df[df['cuit_org'] == cuit_mala].index

    # 55% vencidas con muy bajo avance → riesgo alto por regla
    n_alto   = int(len(idx_mala) * 0.55)
    idx_alto = rng.choice(idx_mala, size=n_alto, replace=False)
    df.loc[idx_alto, 'avance_obra'] = rng.integers(3, 20, size=n_alto)
    df.loc[idx_alto, 'estado']      = 'Iniciada'
    _fijar_dias_activa(df, idx_alto, 200, 520, rng)

    # 20% vencidas con avance moderado → riesgo medio por regla
    resto_mala = idx_mala.difference(idx_alto)
    n_medio    = int(len(idx_mala) * 0.20)
    idx_medio  = rng.choice(resto_mala, size=min(n_medio, len(resto_mala)), replace=False)
    df.loc[idx_medio, 'avance_obra'] = rng.integers(32, 55, size=len(idx_medio))
    df.loc[idx_medio, 'estado']      = 'Avanzada'
    _fijar_dias_activa(df, idx_medio, 120, 260, rng)

    # El 25% restante conserva sus fechas generadas; su riesgo lo define la regla.

    # ── MUTUAL PROGRESO: todas finalizadas/adjudicadas ───────────────────────
    cuit_fin = "30-59804127-3"
    idx_fin  = df[df['cuit_org'] == cuit_fin].index
    df.loc[idx_fin, 'estado']      = rng.choice(['Finalizada','Adjudicada'],
                                                 size=len(idx_fin), p=[0.5, 0.5])
    df.loc[idx_fin, 'avance_obra'] = 100
    # Fechas coherentes de obra terminada (construcción 60–220 días).
    # modelar_actas reescribe luego las 'Finalizada'; las 'Adjudicada' quedan así.
    hoy = date.today()
    for i in idx_fin:
        dur = int(rng.integers(60, 220))
        f_fin = hoy - timedelta(days=int(rng.integers(15, 400)))
        df.at[i, 'fecha_fin']  = f_fin.strftime("%d-%m-%Y")
        df.at[i, 'fecha_inic'] = (f_fin - timedelta(days=dur)).strftime("%d-%m-%Y")

    # ── Clasificaciones — mínimo por tipo ───────────────────────────────────
    # Inclusión y Otro: mínimo 10 | Exclusión: mínimo 5 (son casos rechazados)
    for clasif, (criterio, _) in CLASIFICACIONES.items():
        min_count = 5 if criterio == 'Exclusion' else 10
        n_actual  = (df['clasificacion'] == clasif).sum()
        if n_actual < min_count:
            faltan = min_count - n_actual
            idx_reemplazo = df[df['clasificacion'] == '2a'].sample(faltan, random_state=0).index
            df.loc[idx_reemplazo, 'clasificacion'] = clasif
            df.loc[idx_reemplazo, 'criterio']      = criterio

    # ── Estados — mínimo 15 de cada uno (sobre viviendas sin ONG) ───────────
    sin_org = df[df['cuit_org'].isna()]
    for estado, av_lo, av_hi in [('Iniciada', 0, 35), ('Avanzada', 36, 79),
                                   ('Finalizada', 80, 100), ('Adjudicada', 100, 100)]:
        n_actual = (df['estado'] == estado).sum()
        if n_actual < 15:
            faltan = 15 - n_actual
            pool   = sin_org.sample(min(faltan, len(sin_org)), random_state=3).index
            df.loc[pool, 'estado']     = estado
            df.loc[pool, 'avance_obra'] = rng.integers(av_lo, av_hi + 1, size=len(pool))

    # ── Mínimo 15 obras sin ONG asignada ────────────────────────────────────
    if (df['cuit_org'].isna()).sum() < 15:
        faltan = 15 - (df['cuit_org'].isna()).sum()
        idx    = df[df['cuit_org'].notna()].sample(faltan, random_state=4).index
        df.loc[idx, 'cuit_org'] = None

    return df


def generar_organizaciones() -> pd.DataFrame:
    tipos = ["Cooperativa de Trabajo", "Asociación Civil", "Mutual"]
    return pd.DataFrame([
        {
            "cuit": "30-71782995-2", "nombre": "COOP DE TRABAJO SAN ANTONIO MN 65.044",
            "tipo": "Cooperativa de Trabajo", "dom_legal": "Ruta Prov 204, San Antonio, Jimenez",
            "contacto": "3815999141", "cpe": "58.265",
            "presidente": "Diaz Raul Omar", "dni_presidente": "16468394", "estado": "ACTIVA",
        },
        {
            "cuit": "30-68902314-5", "nombre": "ASOC. CIVIL CONSTRUIR JUNTOS MN 48.231",
            "tipo": "Asociación Civil", "dom_legal": "Av. Belgrano 456, La Banda",
            "contacto": "3856102920", "cpe": "52.140",
            "presidente": "Gomez Ana Maria", "dni_presidente": "22345678", "estado": "ACTIVA",
        },
        {
            "cuit": "30-59804127-3", "nombre": "MUTUAL PROGRESO FAMILIAR MN 31.088",
            "tipo": "Mutual", "dom_legal": "Calle Rivadavia 230, Frías",
            "contacto": "3858441230", "cpe": "44.988",
            "presidente": "Romero Hector Daniel", "dni_presidente": "18904231", "estado": "FINALIZADA",
        },
    ])


def generar_tecnicos() -> pd.DataFrame:
    """
    Genera técnicos con perfiles diferenciados para que los gráficos
    de rendimiento muestren contrastes claros.

    Perfiles:
    - Técnico eficiente: muchas visitas, carga equilibrada
    - Técnico sobrecargado: muchas viviendas, pocas visitas realizadas
    - Técnico nuevo: poca carga, pocos registros
    """
    tecnicos = [
        # id, nombre, apellido, dni, email, telefono, departamentos, activo
        (1, "Rodrigo",  "Peralta",   "28901234", "rperalta@vivso.gob.ar",   "3854001122", "Capital,Banda,Silípica",      1),
        (2, "Valeria",  "Sosa",      "31456789", "vsosa@vivso.gob.ar",      "3854003344", "Robles,Figueroa,Copo",        1),
        (3, "Marcos",   "Ibáñez",    "25678901", "mibanez@vivso.gob.ar",    "3854005566", "Choya,Jiménez,Ojo de Agua",   1),
        (4, "Carolina", "Medina",    "33012345", "cmedina@vivso.gob.ar",    "3854007788", "Moreno,Salavina,Aguirre",     1),
        (5, "Hernán",   "Villafuerte","29345678", "hvillafuerte@vivso.gob.ar","3854009900","Mitre,Rivadavia,Atamisqui",  1),
        (6, "Luciana",  "Ávalos",    "36789012", "lavalos@vivso.gob.ar",    "3854001234", "General Taboada,Guasayán",    1),
    ]
    cols = ["id","nombre","apellido","dni","email","telefono","departamentos","activo"]
    return pd.DataFrame(tecnicos, columns=cols)


def generar_asignaciones(df_viviendas: pd.DataFrame, df_tecnicos: pd.DataFrame) -> pd.DataFrame:
    """
    Asigna viviendas activas a técnicos según el departamento que cubren.
    Cada vivienda activa queda asignada a exactamente un técnico.
    """
    registros = []
    activas = df_viviendas[df_viviendas["estado"].isin(["Iniciada", "Avanzada"])].copy()

    for _, row in activas.iterrows():
        # Buscar técnico cuyo departamento incluya el de esta vivienda
        match = df_tecnicos[
            df_tecnicos["departamentos"].str.contains(row["departamento"], na=False)
        ]
        if match.empty:
            # Si no hay match exacto, asignar al técnico con menos carga
            cargas = {t["id"]: sum(1 for r in registros if r["tecnico_id"] == t["id"])
                      for _, t in df_tecnicos.iterrows()}
            tec_id = min(cargas, key=cargas.get)
        else:
            tec_id = match.iloc[0]["id"]

        f_asig = fake.date_between(start_date="-6m", end_date="today")
        registros.append({
            "tecnico_id":       tec_id,
            "vivienda_id":      row["num_exp"],
            "fecha_asignacion": f_asig.strftime("%d-%m-%Y"),
        })

    return pd.DataFrame(registros)


def generar_visitas(
    df_asignaciones: pd.DataFrame,
    df_viviendas: pd.DataFrame,
    df_tecnicos: pd.DataFrame,
) -> pd.DataFrame:
    """
    Genera visitas respetando la regla de negocio: máximo 2 visitas por obra.

    Perfiles diferenciados por técnico:
    - Técnico 1 (Peralta):  eficiente — visita casi todo, pocos pendientes
    - Técnico 2 (Sosa):     regular — 70% de cobertura
    - Técnico 3 (Ibáñez):  sobrecargado — solo 40% de sus obras visitadas
    - Técnico 4 (Medina):   eficiente — similar a Peralta
    - Técnico 5 (Villafuerte): nuevo — 50% cobertura, todas primeras visitas
    - Técnico 6 (Ávalos):   eficiente — alta cobertura
    """
    cobertura_por_tecnico = {1: 0.90, 2: 0.70, 3: 0.40, 4: 0.85, 5: 0.50, 6: 0.88}
    segunda_visita_prob   = {1: 0.60, 2: 0.45, 3: 0.15, 4: 0.55, 5: 0.00, 6: 0.65}

    avance_map = dict(zip(df_viviendas["num_exp"], df_viviendas["avance_obra"]))
    registros  = []

    for _, asig in df_asignaciones.iterrows():
        tec_id    = asig["tecnico_id"]
        viv_id    = asig["vivienda_id"]
        cobertura = cobertura_por_tecnico.get(tec_id, 0.6)

        if random.random() > cobertura:
            continue  # esta obra no fue visitada aún

        # Primera visita
        avance_real     = avance_map.get(viv_id, 0)
        # El técnico verifica un avance que puede diferir del reportado por la ONG
        # diferencia_ong > 0 → ONG sobreestimó; < 0 → ONG subestimó
        diferencia      = random.randint(-8, 15)
        avance_verif    = max(0, min(100, avance_real - diferencia))
        f_primera       = fake.date_between(start_date="-5m", end_date="-1m")

        registros.append({
            "vivienda_id":       viv_id,
            "tecnico_id":        tec_id,
            "fecha":             f_primera.strftime("%d-%m-%Y"),
            "tipo":              "primera",
            "avance_verificado": avance_verif,
            "estado_relevado":   _estado_por_avance(avance_verif),
            "observacion":       _observacion_aleatoria(avance_verif),
            "diferencia_ong":    diferencia,
        })

        # Segunda visita (probabilidad por técnico)
        if random.random() < segunda_visita_prob.get(tec_id, 0.3):
            diferencia2   = random.randint(-5, 10)
            avance_verif2 = max(avance_verif, min(100, avance_real - diferencia2))
            f_segunda     = fake.date_between(start_date=f_primera, end_date="today")
            registros.append({
                "vivienda_id":       viv_id,
                "tecnico_id":        tec_id,
                "fecha":             f_segunda.strftime("%d-%m-%Y"),
                "tipo":              "segunda",
                "avance_verificado": avance_verif2,
                "estado_relevado":   _estado_por_avance(avance_verif2),
                "observacion":       _observacion_aleatoria(avance_verif2),
                "diferencia_ong":    diferencia2,
            })

    return pd.DataFrame(registros)


def _estado_por_avance(avance: int) -> str:
    if avance == 100: return "Finalizada"
    if avance >= 36:  return "Avanzada"
    return "Iniciada"


def _observacion_aleatoria(avance: int) -> str | None:
    if random.random() > 0.5:
        return None
    obs_bajo = [
        "Obra paralizada por falta de materiales.",
        "Equipo de trabajo reducido.",
        "Terreno con problemas de acceso.",
        "Sin actividad registrada en visita.",
    ]
    obs_medio = [
        "Obra en progreso normal.",
        "Se verificó avance conforme al cronograma.",
        "Materiales en obra, trabajo activo.",
    ]
    obs_alto = [
        "Obra próxima a finalizar.",
        "Terminaciones en curso, sin observaciones.",
        "Calidad de construcción satisfactoria.",
    ]
    if avance < 30:
        return random.choice(obs_bajo)
    if avance < 70:
        return random.choice(obs_medio)
    return random.choice(obs_alto)


def _avance_por_rubro(avance_total: int, nivel_riesgo: str, rng) -> list[int]:
    """
    Distribuye avance_total entre los rubros respetando la secuencia constructiva:
    el rubro N solo puede iniciarse cuando el N-1 está finalizado (restricción del programa).

    Patrones realistas incorporados por nivel de riesgo:
    - bajo:  obra fluida; rubro activo entre 50-95% completado dentro de la etapa.
    - medio: demora moderada; rubro activo entre 20-70%, más variabilidad.
    - alto:  obra paralizada; bloqueada al inicio de etapas estructurales (3-5),
             con avance mínimo dentro del rubro (3-25%).

    Rubros completados se registran como 97-100% para reflejar pequeñas
    imprecisiones habituales en el registro de campo (formularios en papel).
    """
    # Etapas estructurales: alta complejidad, más propensas a bloqueos en riesgo alto
    ETAPAS_ESTRUCTURALES = {3, 4, 5}       # mampostería y encadenado — dependen de cuadrilla y material
    ETAPAS_TERMINACIONES = {6, 7, 8, 9}    # revoques y cielorrasos — requieren mano de obra especializada
    ETAPAS_INSTALACIONES = {10, 11, 12, 13} # carpintería e instalaciones — dependen de aprobación municipal

    resultado = []
    restante  = float(avance_total)
    etapa_activa_encontrada = False

    for rubro in RUBROS_DEF:
        peso = rubro["peso"]
        rid  = rubro["id"]

        if restante >= peso:
            # Rubro completado. Un 7% refleja imprecisiones menores de registro (99%, 98%).
            # Mínimo 98 para que el detector de etapa activa (umbral < 98) no los confunda.
            resultado.append(100 if rng.random() > 0.07 else int(rng.integers(98, 100)))
            restante -= peso

        elif restante > 0 and not etapa_activa_encontrada:
            etapa_activa_encontrada = True
            base = int(restante / peso * 100)  # avance teórico proporcional al AFO restante

            if nivel_riesgo == 'alto':
                # Obra paralizada al comienzo de la etapa — avance muy bajo dentro del rubro.
                if rid in ETAPAS_ESTRUCTURALES:
                    av = int(rng.integers(1, 9))     # cuadrilla ausente o falta de materiales
                elif rid in ETAPAS_TERMINACIONES:
                    av = int(rng.integers(2, 12))    # espera de mano de obra especializada
                elif rid in ETAPAS_INSTALACIONES:
                    av = int(rng.integers(0, 7))     # bloqueada por aprobación municipal
                else:
                    av = max(1, base + int(rng.integers(-20, 1)))
            elif nivel_riesgo == 'medio':
                # Demorada pero en movimiento: avance moderado dentro de la etapa
                av = max(18, min(65, base + int(rng.integers(-6, 14))))
            else:
                # Obra sin riesgo: avance alto dentro de la etapa activa.
                # Cap en 97 (no 99): el detector de etapa usa umbral < 98, así que el
                # rubro activo debe quedarse por debajo para ser correctamente identificado.
                av = max(70, min(97, base + int(rng.integers(26, 46))))

            resultado.append(max(0, min(99, av)))
            restante = 0.0

        else:
            if nivel_riesgo == 'bajo' and not etapa_activa_encontrada:
                # AFO coincide exactamente con el peso acumulado de los rubros previos:
                # la obra acaba de habilitar esta etapa y ya tiene momentum.
                # En obras sin riesgo no hay pausa entre etapas — se arranca de inmediato.
                etapa_activa_encontrada = True
                resultado.append(int(rng.integers(70, 98)))  # máx 97, cap para detección correcta
            else:
                resultado.append(0)

    return resultado


def generar_avance_rubros(df_viviendas: pd.DataFrame) -> pd.DataFrame:
    """
    Genera el avance por rubro para cada vivienda.
    La suma ponderada de los rubros aproxima el avance_obra total.
    El patrón dentro del rubro activo varía según el nivel de riesgo de la obra.
    """
    rng = np.random.default_rng(99)
    hoy = date.today().strftime("%d-%m-%Y")
    registros = []

    for _, viv in tqdm(df_viviendas.iterrows(), total=len(df_viviendas),
                       desc="Generando rubros AFO"):
        avances = _avance_por_rubro(int(viv["avance_obra"]), viv["nivel_riesgo"], rng)
        for rubro_def, av in zip(RUBROS_DEF, avances):
            registros.append({
                "vivienda_id":         viv["num_exp"],
                "rubro_id":            rubro_def["id"],
                "avance_pct":          av,
                "fecha_actualizacion": hoy,
            })

    return pd.DataFrame(registros)


def modelar_actas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Modela el cuello de botella administrativo del programa.

    Una obra física terminada queda en estado 'Finalizada' esperando que se tramite
    el acta de finalización para poder pasar a 'Adjudicada' (entregada a la familia).
    Ese trámite a veces se demora por falta de seguimiento — los técnicos deben hacer
    actas de viviendas finalizadas hace tiempo.

    Para las obras 'Finalizada' se reasigna fecha_fin de forma controlada:
    - ~45% atascadas: acta demorada (finalizadas hace 6-18 meses, sin seguimiento)
    - ~55% en trámite normal (finalizadas hace 0-5 meses)
    fecha_inic se ajusta para mantener coherencia (inic < fin).
    'Adjudicada' no se toca: ya completó el ciclo administrativo.
    """
    df = df.copy()
    rng = np.random.default_rng(7)
    hoy = date.today()

    idx_fin   = df[df["estado"] == "Finalizada"].index
    atascadas = set(rng.choice(idx_fin, size=int(len(idx_fin) * 0.45), replace=False))

    for i in idx_fin:
        dur    = int(rng.integers(60, 300))                        # duración de la construcción
        espera = int(rng.integers(190, 560)) if i in atascadas \
                 else int(rng.integers(10, 150))                   # días esperando el acta
        f_fin = hoy - timedelta(days=espera)
        f_ini = f_fin - timedelta(days=dur)
        df.at[i, "fecha_fin"]   = f_fin.strftime("%d-%m-%Y")
        df.at[i, "fecha_inic"]  = f_ini.strftime("%d-%m-%Y")
        # dias_activa se recalcula en recalcular_derivados() desde estas fechas

    return df


def recalcular_derivados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fuente única de verdad de las columnas derivadas, calculada al final del pipeline
    (después de garantizar_casos y modelar_actas) a partir de las FECHAS.

    - dias_activa: días entre inicio y fin (o hoy si la obra sigue activa).
    - nivel_riesgo (Opción A, plazo = PLAZO_CONSTRUCCION_DIAS):
        · bajo  → obra en plazo, terminada, o vencida pero casi lista (avance ≥ 80)
        · medio → activa, pasó el plazo, avance 30–80% (atrasada pero avanza)
        · alto  → activa, pasó el plazo, avance < 30% (vencida y casi sin avance)
    """
    df = df.copy()
    hoy = pd.Timestamp(date.today())
    fi = pd.to_datetime(df["fecha_inic"], format="%d-%m-%Y", errors="coerce")
    ff = pd.to_datetime(df["fecha_fin"],  format="%d-%m-%Y", errors="coerce")
    df["dias_activa"] = (ff.fillna(hoy) - fi).dt.days

    vencida = (df["estado"].isin(["Iniciada", "Avanzada"])
               & (df["dias_activa"] > PLAZO_CONSTRUCCION_DIAS))
    df["nivel_riesgo"] = "bajo"
    df.loc[vencida & (df["avance_obra"] < 80), "nivel_riesgo"] = "medio"
    df.loc[vencida & (df["avance_obra"] < 30), "nivel_riesgo"] = "alto"
    return df


def cargar_en_db(
    df_viviendas:     pd.DataFrame,
    df_orgs:          pd.DataFrame,
    df_tecnicos:      pd.DataFrame,
    df_asignaciones:  pd.DataFrame,
    df_visitas:       pd.DataFrame,
    df_avance_rubros: pd.DataFrame,
) -> None:
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    df_orgs.to_sql("organizacion",         engine, if_exists="replace", index=False)
    df_viviendas.to_sql("vivienda",        engine, if_exists="replace", index=False)
    df_tecnicos.to_sql("tecnico",          engine, if_exists="replace", index=False)
    df_asignaciones.to_sql("asignacion_tecnico", engine, if_exists="replace", index=False)
    df_visitas.to_sql("visita",            engine, if_exists="replace", index=False)
    # avance_rubro usa append para no pisar el catálogo rubro_obra sembrado en setup.py
    df_avance_rubros.to_sql("avance_rubro", engine, if_exists="replace", index=False)
    print(f"\nCargado en {DB_PATH}:")
    print(f"  organizaciones  : {len(df_orgs)}")
    print(f"  viviendas       : {len(df_viviendas)}")
    print(f"  técnicos        : {len(df_tecnicos)}")
    print(f"  asignaciones    : {len(df_asignaciones)}")
    print(f"  visitas         : {len(df_visitas)}")
    print(f"  avance_rubros   : {len(df_avance_rubros)}")
    print(f"  riesgo alto     : {(df_viviendas['nivel_riesgo'] == 'alto').sum()}")
    print(f"  riesgo medio    : {(df_viviendas['nivel_riesgo'] == 'medio').sum()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=1500, help="Cantidad de viviendas a generar")
    args = parser.parse_args()

    print(f"Generando {args.n} viviendas sintéticas...")
    df_viviendas     = generar_viviendas(args.n)
    df_viviendas     = garantizar_casos(df_viviendas)
    df_viviendas     = modelar_actas(df_viviendas)        # cuello de botella administrativo (actas)
    df_viviendas     = recalcular_derivados(df_viviendas) # dias_activa + nivel_riesgo (fuente única)
    df_orgs          = generar_organizaciones()
    df_tecnicos      = generar_tecnicos()
    df_asignaciones  = generar_asignaciones(df_viviendas, df_tecnicos)
    df_visitas       = generar_visitas(df_asignaciones, df_viviendas, df_tecnicos)
    df_avance_rubros = generar_avance_rubros(df_viviendas)

    cargar_en_db(df_viviendas, df_orgs, df_tecnicos, df_asignaciones,
                 df_visitas, df_avance_rubros)

    # Exportar CSVs para notebooks y Colab
    df_viviendas.to_csv("data/viviendas_sinteticas.csv", index=False)
    df_orgs.to_csv("data/organizaciones.csv", index=False)
    df_tecnicos.to_csv("data/tecnicos.csv", index=False)
    df_asignaciones.to_csv("data/asignaciones.csv", index=False)
    df_visitas.to_csv("data/visitas.csv", index=False)
    df_avance_rubros.to_csv("data/avance_rubros.csv", index=False)
    print("CSVs exportados en data/")
