"""
Dashboard interactivo — Clima y riesgo por comunas (Medellín y Área Metropolitana)
==================================================================================

Datos 100% SINTÉTICOS generados dentro de la propia app, pensados como apoyo
académico (EAFIT) para ejercitar analítica de datos orientada a la gestión de
riesgos climáticos a nivel de comuna / municipio del Valle de Aburrá.

Los datos, coordenadas y niveles de riesgo son simulados con fines
educativos. NO deben usarse como fuente para decisiones reales de gestión del
riesgo — para eso existen el SIATA y el DAGRAN.

Ejecutar con:
    streamlit run main_app.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================================
# CONFIGURACIÓN GENERAL DE LA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Clima y Riesgo — Medellín y Área Metropolitana",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

RIESGO_ORDEN = ["Bajo", "Medio", "Alto", "Crítico"]
COLOR_RIESGO = {
    "Bajo": "#2ECC71", "Medio": "#F1C40F", "Alto": "#E67E22", "Crítico": "#E74C3C",
}

# Presión atmosférica de referencia. Medellín está a ~1.495 m s. n. m.; la
# fórmula barométrica estándar da 1013.25 * (1 - 2.25577e-5 * h)^5.25588
# = 846.1 hPa. El valor anterior (855) correspondía a unos 1.400 m.
PRESION_BASE_HPA = 846.0
ALTITUD_M = 1495

# Pesos del índice de riesgo. Se exponen como constantes para que la
# ponderación sea explícita y auditable, no un número mágico enterrado.
PESO_TERRENO_DEFECTO = 0.45
LLUVIA_SATURACION_MM = 40.0  # mm a partir de los cuales la lluvia aporta el máximo

# 16 comunas urbanas de Medellín + 9 municipios del Área Metropolitana del
# Valle de Aburrá. Población y coordenadas son APROXIMADAS / ilustrativas.
ZONAS_INFO = {
    "Popular":            {"poblacion": 130000, "factor_terreno": 0.85, "ajuste_temp": -0.8, "lat": 6.2975, "lon": -75.5540},
    "Santa Cruz":         {"poblacion": 115000, "factor_terreno": 0.80, "ajuste_temp": -0.6, "lat": 6.2928, "lon": -75.5605},
    "Manrique":           {"poblacion": 160000, "factor_terreno": 0.75, "ajuste_temp": -0.4, "lat": 6.2758, "lon": -75.5563},
    "Aranjuez":           {"poblacion": 150000, "factor_terreno": 0.55, "ajuste_temp": -0.2, "lat": 6.2731, "lon": -75.5647},
    "Castilla":           {"poblacion": 155000, "factor_terreno": 0.50, "ajuste_temp": -0.1, "lat": 6.2870, "lon": -75.5745},
    "Doce de Octubre":    {"poblacion": 190000, "factor_terreno": 0.65, "ajuste_temp": -0.3, "lat": 6.2939, "lon": -75.5825},
    "Robledo":            {"poblacion": 170000, "factor_terreno": 0.60, "ajuste_temp": -0.2, "lat": 6.2820, "lon": -75.5920},
    "Villa Hermosa":      {"poblacion": 95000,  "factor_terreno": 0.80, "ajuste_temp": -0.5, "lat": 6.2545, "lon": -75.5528},
    "Buenos Aires":       {"poblacion": 135000, "factor_terreno": 0.70, "ajuste_temp": -0.3, "lat": 6.2450, "lon": -75.5580},
    "La Candelaria":      {"poblacion": 90000,  "factor_terreno": 0.40, "ajuste_temp": 0.2,  "lat": 6.2476, "lon": -75.5658},
    "Laureles-Estadio":   {"poblacion": 120000, "factor_terreno": 0.35, "ajuste_temp": -0.5, "lat": 6.2447, "lon": -75.5900},
    "La América":         {"poblacion": 95000,  "factor_terreno": 0.45, "ajuste_temp": -0.1, "lat": 6.2508, "lon": -75.5960},
    "San Javier":         {"poblacion": 130000, "factor_terreno": 0.75, "ajuste_temp": -0.3, "lat": 6.2565, "lon": -75.6100},
    "El Poblado":         {"poblacion": 135000, "factor_terreno": 0.45, "ajuste_temp": -1.0, "lat": 6.2085, "lon": -75.5680},
    "Guayabal":           {"poblacion": 95000,  "factor_terreno": 0.55, "ajuste_temp": 0.3,  "lat": 6.2210, "lon": -75.5860},
    "Belén":              {"poblacion": 195000, "factor_terreno": 0.50, "ajuste_temp": 0.0,  "lat": 6.2280, "lon": -75.6020},
    "Bello":              {"poblacion": 475000, "factor_terreno": 0.60, "ajuste_temp": 0.4,  "lat": 6.3373, "lon": -75.5581},
    "Itagüí":             {"poblacion": 280000, "factor_terreno": 0.65, "ajuste_temp": 0.5,  "lat": 6.1719, "lon": -75.6119},
    "Envigado":           {"poblacion": 230000, "factor_terreno": 0.40, "ajuste_temp": 0.3,  "lat": 6.1719, "lon": -75.5836},
    "Sabaneta":           {"poblacion": 55000,  "factor_terreno": 0.35, "ajuste_temp": 0.4,  "lat": 6.1509, "lon": -75.6167},
    "La Estrella":        {"poblacion": 75000,  "factor_terreno": 0.45, "ajuste_temp": 0.3,  "lat": 6.1522, "lon": -75.6438},
    "Copacabana":         {"poblacion": 70000,  "factor_terreno": 0.55, "ajuste_temp": 0.2,  "lat": 6.3489, "lon": -75.5093},
    "Girardota":          {"poblacion": 55000,  "factor_terreno": 0.50, "ajuste_temp": 0.3,  "lat": 6.3778, "lon": -75.4453},
    "Barbosa":            {"poblacion": 50000,  "factor_terreno": 0.45, "ajuste_temp": 0.5,  "lat": 6.4378, "lon": -75.3311},
    "Caldas":             {"poblacion": 80000,  "factor_terreno": 0.55, "ajuste_temp": 0.2,  "lat": 6.0912, "lon": -75.6353},
}
ZONAS = list(ZONAS_INFO.keys())

# Tabla de atributos por zona: permite unir con merge (vectorizado) en lugar
# de aplicar un lambda fila por fila.
ATRIBUTOS_ZONA = (
    pd.DataFrame.from_dict(ZONAS_INFO, orient="index")
    .rename_axis("zona")
    .reset_index()
)
FT_MIN = ATRIBUTOS_ZONA["factor_terreno"].min()
FT_MAX = ATRIBUTOS_ZONA["factor_terreno"].max()

COLUMNAS_NUMERICAS = [
    "temperatura_c", "humedad_relativa", "precipitacion_mm",
    "velocidad_viento_kmh", "presion_atmosferica_hpa", "poblacion",
]
COLUMNAS_CATEGORICAS = ["zona", "condicion_climatica", "nivel_riesgo"]


# ============================================================================
# GENERACIÓN DE DATOS SINTÉTICOS
# ============================================================================
@st.cache_data(show_spinner=False)
def generar_datos(dias: int, semilla: int, peso_terreno: float = PESO_TERRENO_DEFECTO) -> pd.DataFrame:
    """
    Simula registros meteorológicos diarios por comuna/municipio.

    10 columnas: fecha, zona, temperatura_c, humedad_relativa,
    precipitacion_mm, velocidad_viento_kmh, presion_atmosferica_hpa,
    poblacion, condicion_climatica, nivel_riesgo.

    Cada zona conserva una serie de tiempo continua de `dias` días. Las
    variables no se muestrean de forma independiente: se derivan unas de otras
    siguiendo relaciones físicas plausibles.
    """
    rng = np.random.default_rng(semilla)

    fecha_fin = pd.Timestamp.today().normalize()
    fecha_inicio = fecha_fin - pd.Timedelta(days=dias - 1)
    fechas = pd.date_range(fecha_inicio, fecha_fin, freq="D")

    base = pd.MultiIndex.from_product(
        [ZONAS, fechas], names=["zona", "fecha"]
    ).to_frame(index=False)

    # Unión vectorizada de los atributos fijos de cada zona.
    base = base.merge(ATRIBUTOS_ZONA, on="zona", how="left")
    n = len(base)

    factor_terreno = base["factor_terreno"].to_numpy()
    ajuste_temp = base["ajuste_temp"].to_numpy()

    # ── Ciclos anuales ──────────────────────────────────────────────────────
    # El período se ancla al día del año, NO al tamaño de la ventana. Antes,
    # np.sin(2*pi*dia_idx/dias) completaba un ciclo entero sin importar si la
    # serie tenía 10 o 60 días, produciendo una "estacionalidad" que era en
    # realidad un artefacto del slider.
    dia_anio = base["fecha"].dt.dayofyear.to_numpy()

    # Temperatura: un máximo anual desplazado hacia mitad de año.
    ciclo_temp = np.sin(2 * np.pi * (dia_anio - 15) / 365.25)

    # Lluvia: el Valle de Aburrá tiene régimen BIMODAL, con dos temporadas
    # húmedas (abril-mayo y septiembre-noviembre). De ahí el factor 4*pi:
    # dos picos por año en vez de uno.
    ciclo_lluvia = 0.5 * (1 + np.sin(4 * np.pi * (dia_anio - 80) / 365.25))

    # ── Temperatura y humedad ───────────────────────────────────────────────
    temperatura_c = 23 + ajuste_temp + 1.5 * ciclo_temp + rng.normal(0, 1.2, n)
    humedad_relativa = np.clip(
        75 - (temperatura_c - 23) * 3 + 8 * ciclo_lluvia + rng.normal(0, 6, n), 35, 98
    )

    # ── Precipitación ───────────────────────────────────────────────────────
    # Distribución gamma: asimétrica a la derecha, como la lluvia real (muchos
    # días secos, pocos aguaceros). Escalada por el terreno (las laderas
    # reciben más) y por la temporada del año.
    escala_lluvia = 7.0 * (0.6 + 0.8 * ciclo_lluvia)
    precipitacion_mm = np.clip(
        rng.gamma(shape=1.3, scale=escala_lluvia, size=n) * (0.7 + factor_terreno * 0.5) - 3,
        0, None,
    )

    # ── Viento y presión (reaccionan a los eventos de lluvia) ───────────────
    velocidad_viento_kmh = np.clip(8 + precipitacion_mm * 0.15 + rng.normal(0, 4, n), 0, 45)
    presion_atmosferica_hpa = np.clip(
        PRESION_BASE_HPA - precipitacion_mm * 0.05 + rng.normal(0, 2, n),
        PRESION_BASE_HPA - 9, PRESION_BASE_HPA + 9,
    )

    # ── Condición climática (categórica, derivada en cascada) ───────────────
    condiciones = [
        precipitacion_mm > 35,
        precipitacion_mm > 15,
        precipitacion_mm > 3,
        humedad_relativa > 85,
        temperatura_c > 26,
    ]
    etiquetas = ["Tormenta", "Lluvia Fuerte", "Lluvia Ligera", "Nublado", "Soleado"]
    condicion_climatica = np.select(condiciones, etiquetas, default="Parcialmente Nublado")

    # ── Índice de riesgo (categórica ordinal) ───────────────────────────────
    # Ambos componentes se normalizan a [0, 1] ANTES de ponderarlos, de modo
    # que `peso_terreno` signifique realmente lo que dice. En la versión
    # anterior el terreno entraba sin normalizar y terminaba dominando el
    # índice (corr ≈ 0.77 frente a 0.46 de la lluvia), dejando el riesgo casi
    # congelado como atributo fijo de cada zona.
    terreno_norm = (factor_terreno - FT_MIN) / max(FT_MAX - FT_MIN, 1e-9)
    lluvia_norm = np.clip(precipitacion_mm / LLUVIA_SATURACION_MM, 0, 1)

    riesgo_score = (
        peso_terreno * terreno_norm
        + (1 - peso_terreno) * lluvia_norm
        + rng.normal(0, 0.04, n)
    )

    # qcut sobre el RANGO, no sobre el valor bruto. Rankear garantiza bordes
    # de bin únicos, así que `ValueError: Bin edges must be unique` deja de ser
    # posible sea cual sea la semilla o la ventana.
    rangos = pd.Series(riesgo_score).rank(method="first")
    nivel_riesgo = pd.qcut(rangos, q=4, labels=RIESGO_ORDEN)

    df = pd.DataFrame({
        "fecha": base["fecha"],
        "zona": base["zona"],
        "temperatura_c": np.round(temperatura_c, 1),
        "humedad_relativa": np.round(humedad_relativa, 1),
        "precipitacion_mm": np.round(precipitacion_mm, 1),
        "velocidad_viento_kmh": np.round(velocidad_viento_kmh, 1),
        "presion_atmosferica_hpa": np.round(presion_atmosferica_hpa, 1),
        "poblacion": base["poblacion"].astype(int),
        "condicion_climatica": condicion_climatica,
        "nivel_riesgo": pd.Categorical(nivel_riesgo, categories=RIESGO_ORDEN, ordered=True),
    })

    return df.sort_values(["zona", "fecha"]).reset_index(drop=True)


# ============================================================================
# UTILIDADES
# ============================================================================
def mapa_scatter(df: pd.DataFrame, **kwargs):
    """
    Construye el mapa usando la API vigente de Plotly.

    px.scatter_mapbox quedó obsoleta en Plotly 6; px.scatter_map es su
    reemplazo. Se detecta cuál existe para que la app funcione en ambas
    versiones sin tocar el requirements.
    """
    if hasattr(px, "scatter_map"):
        return px.scatter_map(df, map_style="open-street-map", **kwargs)
    return px.scatter_mapbox(df, mapbox_style="open-street-map", **kwargs)


def slider_umbral(etiqueta: str, serie: pd.Series, percentil: float = 85.0):
    """
    Slider de umbral resistente a series degeneradas.

    st.slider lanza excepción si min_value == max_value, cosa que ocurre al
    filtrar hasta dejar un único registro o una variable constante.
    """
    serie = serie.dropna()
    if serie.empty:
        st.info("No hay datos suficientes para definir un umbral.")
        return None

    v_min, v_max = float(serie.min()), float(serie.max())
    if np.isclose(v_min, v_max):
        st.info(f"`{etiqueta}` es constante ({v_min:.1f}) en la selección actual; "
                "no hay rango sobre el cual fijar un umbral.")
        return None

    return st.slider(
        f"Valor de alerta para {etiqueta}",
        min_value=v_min, max_value=v_max,
        value=float(np.percentile(serie, percentil)),
    )


def render_banner():
    st.sidebar.markdown(
        """
        <div style="background-color:#00205B;padding:18px 14px;border-radius:12px;
                    text-align:center;margin-bottom:20px;border:1px solid #F2C94C;">
            <h3 style="color:white;margin:0;">🎓 EAFIT 2026</h3>
            <p style="color:#F2C94C;margin:6px 0 0 0;font-weight:700;letter-spacing:0.3px;">
                Ciencia de Datos
            </p>
            <p style="color:white;margin:10px 0 0 0;font-size:0.95rem;">
                Juan Alberto Rodríguez
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


render_banner()


# ============================================================================
# CONTROL DE ACCESO (OPCIONAL)
# ============================================================================
# La puerta de acceso solo se activa si existe un código en los secrets del
# despliegue. Por defecto la app es pública: un portafolio que pide contraseña
# pierde visitantes, y un código publicado en el README no protege nada.
#
# Para activarla, añade en Streamlit Cloud (Settings → Secrets):
#     CODIGO_ACCESO = "tu_codigo"
try:
    CODIGO_ACCESO = st.secrets.get("CODIGO_ACCESO", "")
except Exception:  # noqa: BLE001 — la ausencia de secrets.toml no es un error
    CODIGO_ACCESO = ""

if CODIGO_ACCESO:
    st.session_state.setdefault("autenticado", False)

    if not st.session_state.autenticado:
        st.title("Acceso al Dashboard")
        st.write("Este panel es un ejercicio académico. Ingresa el código de acceso.")
        with st.form("form_login"):
            codigo = st.text_input("Código de acceso", type="password", max_chars=32)
            enviado = st.form_submit_button("Ingresar", type="primary")
        if enviado:
            if codigo.strip() == CODIGO_ACCESO:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Código incorrecto. Intenta nuevamente.")
        st.stop()

    st.sidebar.button(
        "Cerrar sesión",
        on_click=lambda: st.session_state.update(autenticado=False),
    )
    st.sidebar.divider()


# ============================================================================
# BARRA LATERAL: CONFIGURACIÓN DE DATOS + FILTROS
# ============================================================================
st.sidebar.subheader("Generación de datos sintéticos")

dias_serie = st.sidebar.slider(
    "Días de la serie (por zona)", min_value=10, max_value=60, value=20,
    help="25 zonas × N días = total de registros. Con 20 días se obtienen 500.",
)
st.sidebar.caption(
    f"Registros a generar: **{dias_serie * len(ZONAS)}** "
    f"({len(ZONAS)} zonas × {dias_serie} días)"
)


def nueva_semilla() -> None:
    """
    Callback del botón de dado.

    Los callbacks de Streamlit se ejecutan ANTES de reejecutar el script, que
    es el único momento en que se puede reasignar el session_state de una
    clave ligada a un widget. La versión anterior escribía la semilla nueva
    después de instanciar el number_input y hacía st.rerun(): como los widgets
    con `key` ignoran el argumento `value` en runs posteriores, el input
    devolvía la semilla vieja y la sobrescribía. El botón no hacía nada.
    """
    st.session_state.semilla = int(np.random.default_rng().integers(0, 1_000_000))


st.session_state.setdefault("semilla", 42)

col_seed1, col_seed2 = st.sidebar.columns([2, 1])
with col_seed2:
    st.write("")
    st.write("")
    st.button("", help="Generar una semilla aleatoria nueva", on_click=nueva_semilla)
with col_seed1:
    # Una sola fuente de verdad: la clave del widget ES la clave del estado.
    st.number_input("Semilla aleatoria", min_value=0, max_value=999_999, step=1, key="semilla")

semilla = int(st.session_state.semilla)

peso_terreno = st.sidebar.slider(
    "Peso del terreno en el índice de riesgo", 0.0, 1.0, PESO_TERRENO_DEFECTO, 0.05,
    help="0 = el riesgo depende solo de la lluvia del día. "
         "1 = depende solo de la pendiente de la zona (riesgo estático).",
)

df = generar_datos(int(dias_serie), semilla, float(peso_terreno))

st.sidebar.caption(
    "Datos **100% sintéticos** con fines académicos. No constituyen fuente "
    "oficial para decisiones reales de gestión del riesgo."
)

st.sidebar.divider()
st.sidebar.subheader("Filtros")

fecha_min, fecha_max = df["fecha"].min().date(), df["fecha"].max().date()
rango_fechas = st.sidebar.date_input(
    "Rango de fechas", value=(fecha_min, fecha_max),
    min_value=fecha_min, max_value=fecha_max,
)

# date_input devuelve una tupla de 1 elemento mientras el usuario está a medio
# seleccionar el rango. Antes se descartaba en silencio y se volvía al rango
# completo; ahora se respeta la fecha elegida como día único.
if isinstance(rango_fechas, (tuple, list)):
    if len(rango_fechas) == 2:
        f_ini, f_fin = rango_fechas
    elif len(rango_fechas) == 1:
        f_ini = f_fin = rango_fechas[0]
    else:
        f_ini, f_fin = fecha_min, fecha_max
else:
    f_ini = f_fin = rango_fechas

zonas_sel = st.sidebar.multiselect("Comuna / Municipio", ZONAS, default=ZONAS)
condiciones_disp = sorted(df["condicion_climatica"].unique())
condicion_sel = st.sidebar.multiselect(
    "Condición climática", condiciones_disp, default=condiciones_disp,
)
riesgo_sel = st.sidebar.multiselect("Nivel de riesgo", RIESGO_ORDEN, default=RIESGO_ORDEN)

mask = (
    (df["fecha"].dt.date >= f_ini)
    & (df["fecha"].dt.date <= f_fin)
    & (df["zona"].isin(zonas_sel))
    & (df["condicion_climatica"].isin(condicion_sel))
    & (df["nivel_riesgo"].isin(riesgo_sel))
)
df_f = df.loc[mask].copy()

st.sidebar.metric("Registros tras filtro", f"{len(df_f):,}".replace(",", "."))


# ============================================================================
# ENCABEZADO
# ============================================================================
st.title("Clima y Riesgo — Medellín y Área Metropolitana")
st.caption(
    "Datos meteorológicos **sintéticos** por comuna/municipio, pensados como insumo "
    "exploratorio para apoyar decisiones sobre riesgos climáticos. "
    "Proyecto académico — no oficial."
)

if df_f.empty:
    st.warning(
        "No hay registros que coincidan con los filtros seleccionados. "
        "Ajusta los filtros en la barra lateral."
    )
    st.stop()

# Zonas realmente presentes tras el filtrado. Se usan en los selectores de las
# pestañas para que no ofrezcan zonas que el filtro global ya descartó.
ZONAS_DISPONIBLES = sorted(df_f["zona"].unique())


# ============================================================================
# KPIs
# ============================================================================
ultima_fecha = df_f["fecha"].max()
snapshot_actual = df_f[df_f["fecha"] == ultima_fecha]
zonas_riesgo_alto = (
    snapshot_actual.loc[snapshot_actual["nivel_riesgo"].isin(["Alto", "Crítico"]), "zona"].nunique()
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Registros", f"{len(df_f):,}".replace(",", "."))
k2.metric("Temp. promedio", f"{df_f['temperatura_c'].mean():.1f} °C")
k3.metric("Humedad promedio", f"{df_f['humedad_relativa'].mean():.1f} %")
k4.metric("Precipitación acumulada", f"{df_f['precipitacion_mm'].sum():,.0f} mm".replace(",", "."))
k5.metric(f"Zonas en riesgo Alto/Crítico ({ultima_fecha.date()})", zonas_riesgo_alto)

st.divider()


# ============================================================================
# TABS
# ============================================================================
tab_resumen, tab_series, tab_cuanti, tab_cuali, tab_dinamico, tab_mapa, tab_datos = st.tabs([
    "Resumen", "Serie de Tiempo", "Estadística Cuantitativa",
    "Estadística Cualitativa", "Gráficos Dinámicos", "Mapa de Riesgo", "Datos",
])

# ══════════════════════════ TAB RESUMEN ═════════════════════════════════════
with tab_resumen:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Temperatura promedio diaria")
        serie_temp = df_f.groupby("fecha", as_index=False)["temperatura_c"].mean()
        fig = px.line(serie_temp, x="fecha", y="temperatura_c", markers=True,
                      title="Temperatura promedio por día (zonas filtradas)")
        fig.update_layout(xaxis_title="Fecha", yaxis_title="°C")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Distribución del nivel de riesgo")
        conteo = (
            df_f["nivel_riesgo"].value_counts()
            .reindex(RIESGO_ORDEN, fill_value=0)
            .rename_axis("nivel_riesgo").reset_index(name="registros")
        )
        # Se ocultan las categorías vacías: un sector de 0 % ensucia la dona.
        conteo = conteo[conteo["registros"] > 0]
        fig = px.pie(conteo, names="nivel_riesgo", values="registros", hole=0.45,
                     category_orders={"nivel_riesgo": RIESGO_ORDEN},
                     color="nivel_riesgo", color_discrete_map=COLOR_RIESGO,
                     title="Proporción de registros por nivel de riesgo")
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        st.subheader("Precipitación acumulada por zona (top 10)")
        top_precip = (
            df_f.groupby("zona", as_index=False)["precipitacion_mm"].sum()
            .nlargest(10, "precipitacion_mm")
        )
        fig = px.bar(top_precip, x="precipitacion_mm", y="zona", orientation="h",
                     title="Zonas con mayor precipitación acumulada")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="mm acumulados")
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        st.subheader("Condición climática predominante")
        conteo_cond = (
            df_f["condicion_climatica"].value_counts()
            .rename_axis("condicion_climatica").reset_index(name="registros")
        )
        fig = px.bar(conteo_cond, x="condicion_climatica", y="registros",
                     title="Frecuencia de condiciones climáticas")
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════ TAB SERIE DE TIEMPO ════════════════════════════════
with tab_series:
    st.subheader("Comportamiento de una variable en el tiempo, por zona")

    c1, c2, c3 = st.columns(3)
    with c1:
        # Solo zonas presentes tras el filtro global; antes ofrecía las 25
        # siempre, y elegir una descartada producía un gráfico vacío.
        zonas_ts = st.multiselect(
            "Zonas a graficar", ZONAS_DISPONIBLES,
            default=ZONAS_DISPONIBLES[:3], key="ts_zonas",
        )
    with c2:
        variable_ts = st.selectbox("Variable", COLUMNAS_NUMERICAS, index=0, key="ts_var")
    with c3:
        ventana_mm = st.slider("Ventana media móvil (días)", 1, 14, 1, key="ts_ventana",
                               help="1 = sin suavizado")

    mostrar_umbral_ts = st.checkbox(
        "Mostrar umbral / línea de alerta", value=(variable_ts == "precipitacion_mm"),
    )
    umbral_ts = slider_umbral(variable_ts, df_f[variable_ts]) if mostrar_umbral_ts else None

    if not zonas_ts:
        st.info("Selecciona al menos una zona para graficar la serie de tiempo.")
    else:
        df_ts = df_f[df_f["zona"].isin(zonas_ts)].sort_values(["zona", "fecha"]).copy()

        if ventana_mm > 1:
            df_ts[variable_ts] = (
                df_ts.groupby("zona", observed=True)[variable_ts]
                .transform(lambda s: s.rolling(ventana_mm, min_periods=1).mean())
            )

        fig = px.line(df_ts, x="fecha", y=variable_ts, color="zona", markers=True,
                      title=f"{variable_ts} en el tiempo por zona")
        if umbral_ts is not None:
            fig.add_hline(y=umbral_ts, line_dash="dash", line_color="#E74C3C",
                          annotation_text=f"Umbral: {umbral_ts:.1f}")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        if umbral_ts is not None:
            ultimos = df_ts[df_ts["fecha"] == df_ts["fecha"].max()]
            en_alerta = ultimos[ultimos[variable_ts] >= umbral_ts]
            if not en_alerta.empty:
                zonas_alerta = ", ".join(en_alerta["zona"].tolist())
                st.warning(f"Zonas que superan el umbral en la fecha más reciente: **{zonas_alerta}**")
            else:
                st.success("Ninguna zona supera el umbral en la fecha más reciente.")

# ═════════════════════ TAB ESTADÍSTICA CUANTITATIVA ═════════════════════════
with tab_cuanti:
    st.subheader("Resumen estadístico de variables numéricas")

    resumen_num = df_f[COLUMNAS_NUMERICAS].describe().T
    resumen_num["varianza"] = df_f[COLUMNAS_NUMERICAS].var()
    resumen_num["asimetría (skew)"] = df_f[COLUMNAS_NUMERICAS].skew()
    resumen_num["curtosis"] = df_f[COLUMNAS_NUMERICAS].kurt()
    st.dataframe(resumen_num.style.format("{:.2f}"), use_container_width=True)

    st.caption(
        "Asimetría > 0 indica cola derecha: es lo esperable en `precipitacion_mm`, "
        "donde predominan los días secos y unos pocos aguaceros estiran la distribución."
    )

    st.divider()
    col_sel, col_bins = st.columns([2, 1])
    with col_sel:
        var_num = st.selectbox("Variable numérica a analizar", COLUMNAS_NUMERICAS, key="cuanti_var")
    with col_bins:
        bins = st.slider("N° de bins (histograma)", 5, 100, 30, key="cuanti_bins")

    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(df_f, x=var_num, nbins=bins, marginal="box",
                           title=f"Distribución de {var_num}")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.box(df_f, x="nivel_riesgo", y=var_num, color="nivel_riesgo",
                     category_orders={"nivel_riesgo": RIESGO_ORDEN},
                     color_discrete_map=COLOR_RIESGO,
                     title=f"{var_num} por nivel de riesgo")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Matriz de correlación")
    corr = df_f[COLUMNAS_NUMERICAS].corr(numeric_only=True)
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1, title="Correlación entre variables numéricas")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "`poblacion` es constante por zona, así que sus correlaciones reflejan "
        "el tamaño de las zonas, no una relación meteorológica."
    )

# ═════════════════════ TAB ESTADÍSTICA CUALITATIVA ══════════════════════════
with tab_cuali:
    st.subheader("Frecuencias de variables categóricas")
    var_cat = st.selectbox("Variable categórica a analizar", COLUMNAS_CATEGORICAS, key="cuali_var")

    conteo = (
        df_f[var_cat].value_counts(dropna=False)
        .rename_axis(var_cat).reset_index(name="frecuencia")
    )
    conteo = conteo[conteo["frecuencia"] > 0]
    conteo["porcentaje"] = (conteo["frecuencia"] / conteo["frecuencia"].sum() * 100).round(2)

    moda = df_f[var_cat].mode(dropna=True)
    moda_txt = str(moda.iloc[0]) if not moda.empty else "N/A"

    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Moda", moda_txt)
        st.metric("N° de categorías", int(df_f[var_cat].nunique()))
        st.dataframe(conteo, use_container_width=True, hide_index=True)
    with c2:
        es_riesgo = var_cat == "nivel_riesgo"
        fig = px.bar(
            conteo, x=var_cat, y="frecuencia", text="porcentaje", color=var_cat,
            category_orders={var_cat: RIESGO_ORDEN} if es_riesgo else None,
            color_discrete_map=COLOR_RIESGO if es_riesgo else None,
            title=f"Frecuencia de {var_cat}",
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Tabla cruzada (contingencia)")

    c3, c4 = st.columns(2)
    with c3:
        var_a = st.selectbox("Variable 1", COLUMNAS_CATEGORICAS, index=1, key="cruzada_a")
    with c4:
        var_b = st.selectbox("Variable 2", COLUMNAS_CATEGORICAS, index=2, key="cruzada_b")

    if var_a == var_b:
        st.info("Selecciona dos variables distintas para construir la tabla cruzada.")
    else:
        tabla_cruzada = pd.crosstab(df_f[var_a], df_f[var_b])
        # Se eliminan filas/columnas vacías que las categóricas arrastran.
        tabla_cruzada = tabla_cruzada.loc[
            tabla_cruzada.sum(axis=1) > 0, tabla_cruzada.sum(axis=0) > 0
        ]
        st.dataframe(tabla_cruzada, use_container_width=True)
        fig = px.imshow(tabla_cruzada, text_auto=True, color_continuous_scale="Blues",
                        title=f"Mapa de calor: {var_a} vs {var_b}")
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════ TAB GRÁFICOS DINÁMICOS ═════════════════════════════
with tab_dinamico:
    st.subheader("Constructor de gráficas interactivas")

    todas_las_columnas = COLUMNAS_NUMERICAS + COLUMNAS_CATEGORICAS + ["fecha"]

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        tipo_grafico = st.selectbox(
            "Tipo de gráfica",
            ["Dispersión", "Barras", "Histograma", "Caja (Box)", "Línea", "Violín"],
        )
    with col_b:
        eje_x = st.selectbox("Variable eje X", todas_las_columnas,
                             index=todas_las_columnas.index("temperatura_c"))
    with col_c:
        opciones_y = ["(ninguna)"] + todas_las_columnas
        eje_y = st.selectbox(
            "Variable eje Y", opciones_y,
            index=0 if tipo_grafico == "Histograma" else opciones_y.index("precipitacion_mm"),
        )

    # Aviso explícito cuando el tipo de gráfico ignora el eje X elegido, en
    # lugar de descartarlo en silencio como hacía la versión anterior.
    if tipo_grafico in ("Caja (Box)", "Violín") and pd.api.types.is_numeric_dtype(df_f[eje_x]):
        st.info(
            f"En **{tipo_grafico}** el eje X agrupa por categoría. Como `{eje_x}` es "
            "numérica, se graficará una sola caja. Elige una variable categórica en X "
            "para comparar grupos."
        )

    col_d, col_e, col_f = st.columns(3)
    with col_d:
        color_por = st.selectbox("Colorear por", ["(ninguno)"] + COLUMNAS_CATEGORICAS)
    with col_e:
        paleta = st.selectbox("Paleta de color",
                              ["Plotly", "Vivid", "Bold", "Pastel", "Set2", "D3", "Antique"])
    with col_f:
        opacidad = st.slider("Opacidad", 0.1, 1.0, 0.8)

    mapa_paletas = {
        "Plotly": px.colors.qualitative.Plotly, "Vivid": px.colors.qualitative.Vivid,
        "Bold": px.colors.qualitative.Bold, "Pastel": px.colors.qualitative.Pastel,
        "Set2": px.colors.qualitative.Set2, "D3": px.colors.qualitative.D3,
        "Antique": px.colors.qualitative.Antique,
    }
    secuencia_color = mapa_paletas[paleta]

    with st.expander("Personalización adicional y umbrales", expanded=False):
        cu1, cu2, cu3 = st.columns(3)
        with cu1:
            titulo_default = f"{tipo_grafico}: {eje_x}" + (
                f" vs {eje_y}" if eje_y != "(ninguna)" else ""
            )
            titulo_custom = st.text_input("Título del gráfico", value=titulo_default)
        with cu2:
            mostrar_umbral = st.checkbox("Mostrar línea de umbral", value=False)
        with cu3:
            color_umbral = st.color_picker("Color del umbral", "#E45756")

        umbral_valor, eje_umbral = None, None
        if mostrar_umbral:
            numericas_disp = [c for c in COLUMNAS_NUMERICAS if c in (eje_x, eje_y)]
            if not numericas_disp:
                st.info("El umbral solo aplica si el eje X o Y es una variable numérica.")
            else:
                cu4, cu5 = st.columns(2)
                with cu4:
                    eje_umbral = st.selectbox("Aplicar umbral sobre", numericas_disp)
                with cu5:
                    umbral_valor = slider_umbral(eje_umbral, df_f[eje_umbral], percentil=50)

        mostrar_tendencia = False
        if tipo_grafico == "Dispersión" and eje_y != "(ninguna)":
            mostrar_tendencia = st.checkbox("Mostrar línea de tendencia (ajuste lineal)", value=False)

    y_arg = None if eje_y == "(ninguna)" else eje_y
    color_arg = None if color_por == "(ninguno)" else color_por

    fig = None
    try:
        if tipo_grafico == "Dispersión":
            fig = px.scatter(df_f, x=eje_x, y=y_arg, color=color_arg,
                             color_discrete_sequence=secuencia_color, opacity=opacidad,
                             title=titulo_custom, hover_data=["zona"])
            if (mostrar_tendencia and y_arg
                    and pd.api.types.is_numeric_dtype(df_f[eje_x])
                    and pd.api.types.is_numeric_dtype(df_f[y_arg])):
                datos = df_f[[eje_x, y_arg]].dropna()
                if len(datos) >= 2:
                    coef = np.polyfit(datos[eje_x], datos[y_arg], 1)
                    x_line = np.linspace(datos[eje_x].min(), datos[eje_x].max(), 50)
                    r = datos[eje_x].corr(datos[y_arg])
                    fig.add_trace(go.Scatter(
                        x=x_line, y=coef[0] * x_line + coef[1], mode="lines",
                        name=f"Tendencia (r = {r:.2f})",
                        line=dict(color="black", dash="dash"),
                    ))

        elif tipo_grafico == "Barras":
            if y_arg is None:
                agregado = df_f[eje_x].value_counts().rename_axis(eje_x).reset_index(name="conteo")
                fig = px.bar(agregado, x=eje_x, y="conteo", color=color_arg,
                             color_discrete_sequence=secuencia_color, title=titulo_custom)
            else:
                fig = px.bar(df_f, x=eje_x, y=y_arg, color=color_arg,
                             color_discrete_sequence=secuencia_color, opacity=opacidad,
                             title=titulo_custom)

        elif tipo_grafico == "Histograma":
            fig = px.histogram(df_f, x=eje_x, color=color_arg,
                               color_discrete_sequence=secuencia_color, opacity=opacidad,
                               title=titulo_custom)

        elif tipo_grafico == "Caja (Box)":
            x_cat = eje_x if not pd.api.types.is_numeric_dtype(df_f[eje_x]) else None
            fig = px.box(df_f, x=x_cat, y=y_arg or eje_x, color=color_arg,
                         color_discrete_sequence=secuencia_color, title=titulo_custom)

        elif tipo_grafico == "Línea":
            y_linea = y_arg or "temperatura_c"
            # Con 25 zonas y sin agrupar, una línea sobre 'fecha' zigzaguea
            # entre los valores de cada zona. Si no hay color por zona, se
            # promedia por punto del eje X para que la línea sea legible.
            if color_arg is None and pd.api.types.is_numeric_dtype(df_f[y_linea]):
                df_linea = df_f.groupby(eje_x, as_index=False, observed=True)[y_linea].mean()
                fig = px.line(df_linea.sort_values(eje_x), x=eje_x, y=y_linea,
                              color_discrete_sequence=secuencia_color,
                              title=f"{titulo_custom} (promedio por {eje_x})")
            else:
                fig = px.line(df_f.sort_values(eje_x), x=eje_x, y=y_linea, color=color_arg,
                              color_discrete_sequence=secuencia_color, title=titulo_custom)

        elif tipo_grafico == "Violín":
            x_cat = eje_x if not pd.api.types.is_numeric_dtype(df_f[eje_x]) else None
            fig = px.violin(df_f, x=x_cat, y=y_arg or eje_x, color=color_arg, box=True,
                            color_discrete_sequence=secuencia_color, title=titulo_custom)

        if fig is not None:
            if umbral_valor is not None and eje_umbral:
                horizontal = (eje_umbral != eje_x) or tipo_grafico in ("Caja (Box)", "Violín", "Barras")
                anotacion = f"Umbral {eje_umbral}: {umbral_valor:.1f}"
                if horizontal:
                    fig.add_hline(y=umbral_valor, line_dash="dash",
                                  line_color=color_umbral, annotation_text=anotacion)
                else:
                    fig.add_vline(x=umbral_valor, line_dash="dash",
                                  line_color=color_umbral, annotation_text=anotacion)

            fig.update_layout(height=550)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecciona una combinación válida de variables para generar la gráfica.")

    except (ValueError, TypeError, KeyError) as e:
        st.error(
            f"No fue posible construir un **{tipo_grafico}** con `{eje_x}`"
            + (f" y `{eje_y}`" if y_arg else "")
            + f". Prueba otra combinación de variables.\n\nDetalle: {e}"
        )

# ═══════════════════════════ TAB MAPA DE RIESGO ═════════════════════════════
with tab_mapa:
    st.subheader(f"Mapa de riesgo por zona — corte al {ultima_fecha.date()}")
    st.caption(
        "Coordenadas aproximadas / ilustrativas. Tamaño del punto = población simulada. "
        "Color = nivel de riesgo simulado."
    )

    snapshot_mapa = snapshot_actual.merge(
        ATRIBUTOS_ZONA[["zona", "lat", "lon"]], on="zona", how="left"
    )

    if snapshot_mapa.empty:
        st.info("No hay datos para la fecha más reciente con los filtros actuales.")
    else:
        fig = mapa_scatter(
            snapshot_mapa, lat="lat", lon="lon", color="nivel_riesgo", size="poblacion",
            category_orders={"nivel_riesgo": RIESGO_ORDEN}, color_discrete_map=COLOR_RIESGO,
            hover_name="zona",
            hover_data={
                "temperatura_c": True, "humedad_relativa": True, "precipitacion_mm": True,
                "condicion_climatica": True, "poblacion": True, "lat": False, "lon": False,
            },
            zoom=9.7, height=600, title="Nivel de riesgo simulado por zona",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Ranking de zonas por nivel de riesgo (fecha más reciente)")
        # nivel_riesgo ya es una categórica ORDENADA, así que sort_values
        # respeta Bajo < Medio < Alto < Crítico sin diccionarios auxiliares.
        ranking = snapshot_mapa.sort_values(
            ["nivel_riesgo", "precipitacion_mm"], ascending=[False, False],
        )
        st.dataframe(
            ranking[["zona", "nivel_riesgo", "precipitacion_mm", "temperatura_c",
                     "humedad_relativa", "poblacion"]],
            use_container_width=True, hide_index=True,
        )

# ══════════════════════════════ TAB DATOS ═══════════════════════════════════
with tab_datos:
    st.subheader("Vista de datos filtrados")
    st.dataframe(df_f, use_container_width=True, height=450, hide_index=True)

    st.download_button(
        "Descargar CSV filtrado",
        data=df_f.to_csv(index=False).encode("utf-8"),
        file_name="clima_medellin_sintetico_filtrado.csv",
        mime="text/csv",
    )

    with st.expander("Diccionario de columnas"):
        st.markdown(f"""
| Columna | Tipo | Descripción |
|---|---|---|
| `fecha` | datetime | Fecha del registro (serie diaria continua por zona) |
| `zona` | categórica | Comuna de Medellín o municipio del Área Metropolitana |
| `temperatura_c` | float | Temperatura simulada en °C |
| `humedad_relativa` | float | Humedad relativa simulada (%) |
| `precipitacion_mm` | float | Precipitación simulada en mm (distribución gamma) |
| `velocidad_viento_kmh` | float | Velocidad del viento simulada en km/h |
| `presion_atmosferica_hpa` | float | Presión simulada, base {PRESION_BASE_HPA:.0f} hPa a {ALTITUD_M} m s. n. m. |
| `poblacion` | int | Población aproximada de la zona (constante por zona) |
| `condicion_climatica` | categórica | Derivada en cascada de precipitación, humedad y temperatura |
| `nivel_riesgo` | categórica ordinal | Cuartiles del índice compuesto terreno + lluvia |
        """)

    with st.expander("Cómo se calcula el nivel de riesgo"):
        st.markdown(f"""
El índice combina dos componentes, **ambos normalizados a [0, 1]** antes de
ponderarse, para que el peso signifique lo que dice:

```
terreno_norm = (factor_terreno - {FT_MIN:.2f}) / ({FT_MAX:.2f} - {FT_MIN:.2f})
lluvia_norm  = min(precipitacion_mm / {LLUVIA_SATURACION_MM:.0f}, 1)

score = {peso_terreno:.2f} × terreno_norm + {1 - peso_terreno:.2f} × lluvia_norm + ruido
```

El score se ordena y se corta en cuartiles → Bajo, Medio, Alto, Crítico.

Ajusta el **peso del terreno** en la barra lateral para ver el efecto: con peso
alto el riesgo se vuelve un atributo casi fijo de cada zona (las laderas siempre
en rojo); con peso bajo responde al clima de cada día. Ese contraste es en sí
mismo el hallazgo interesante del ejercicio.
        """)
