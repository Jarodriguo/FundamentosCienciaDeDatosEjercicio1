"""
Dashboard interactivo — Clima y riesgo por comunas (Medellín y Área Metropolitana)
====================================================================================
Datos 100% SINTÉTICOS generados dentro de la propia app, pensados como apoyo
académico (EAFIT) para ejercitar analítica de datos orientada a la gestión de
riesgos climáticos (lluvias, deslizamientos, inundaciones) a nivel de comuna /
municipio del Valle de Aburrá.

⚠️ IMPORTANTE: los datos, coordenadas y niveles de riesgo son simulados con
fines educativos. NO deben usarse como fuente oficial para decisiones reales
de gestión del riesgo — para eso existen entidades como el DAGRAN / SIATA.

Ejecutar con:
    streamlit run main_app.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# CONFIGURACIÓN GENERAL DE LA PÁGINA
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Clima y Riesgo — Medellín y Área Metropolitana",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CODIGO_ACCESO = "4650"

RIESGO_ORDEN = ["Bajo", "Medio", "Alto", "Crítico"]
COLOR_RIESGO = {"Bajo": "#2ECC71", "Medio": "#F1C40F", "Alto": "#E67E22", "Crítico": "#E74C3C"}

# 16 comunas urbanas de Medellín + 9 municipios del Área Metropolitana del Valle
# de Aburrá. Población y coordenadas son APROXIMADAS / ilustrativas.
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

COLUMNAS_NUMERICAS = [
    "temperatura_c", "humedad_relativa", "precipitacion_mm",
    "velocidad_viento_kmh", "presion_atmosferica_hpa", "poblacion",
]
COLUMNAS_CATEGORICAS = ["zona", "condicion_climatica", "nivel_riesgo"]


# ----------------------------------------------------------------------------
# GENERACIÓN DE DATOS SINTÉTICOS (10 columnas, serie de tiempo por zona)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def generar_datos(dias: int, semilla: int) -> pd.DataFrame:
    """Simula registros meteorológicos diarios por comuna/municipio.
    Columnas (10): fecha, zona, temperatura_c, humedad_relativa,
    precipitacion_mm, velocidad_viento_kmh, presion_atmosferica_hpa,
    poblacion, condicion_climatica, nivel_riesgo.
    Cada zona conserva una serie de tiempo continua de `dias` días.
    """
    rng = np.random.default_rng(semilla)

    fecha_fin = pd.Timestamp.today().normalize()
    fecha_inicio = fecha_fin - pd.Timedelta(days=dias - 1)
    fechas = pd.date_range(fecha_inicio, fecha_fin, freq="D")

    base = pd.DataFrame(
        pd.MultiIndex.from_product([ZONAS, fechas], names=["zona", "fecha"]).to_frame(index=False)
    )
    n = len(base)

    poblacion = base["zona"].map(lambda z: ZONAS_INFO[z]["poblacion"]).values
    factor_terreno = base["zona"].map(lambda z: ZONAS_INFO[z]["factor_terreno"]).values
    ajuste_temp = base["zona"].map(lambda z: ZONAS_INFO[z]["ajuste_temp"]).values

    dia_idx = (base["fecha"] - fecha_inicio).dt.days.values
    ciclo = np.sin(2 * np.pi * dia_idx / max(dias, 1))

    # --- temperatura y humedad ---
    temperatura_c = 23 + ajuste_temp + 1.5 * ciclo + rng.normal(0, 1.2, n)
    humedad_relativa = np.clip(75 - (temperatura_c - 23) * 3 + rng.normal(0, 6, n), 35, 98)

    # --- precipitación (más probable en zonas de ladera / factor_terreno alto) ---
    precipitacion_mm = np.clip(
        rng.gamma(shape=1.3, scale=7.0, size=n) * (0.7 + factor_terreno * 0.5) - 3, 0, None
    )

    # --- viento y presión (afectados por eventos de lluvia) ---
    velocidad_viento_kmh = np.clip(8 + precipitacion_mm * 0.15 + rng.normal(0, 4, n), 0, 45)
    presion_atmosferica_hpa = np.clip(855 - precipitacion_mm * 0.05 + rng.normal(0, 2, n), 838, 868)

    # --- condición climática (categórica, derivada) ---
    condiciones = [
        precipitacion_mm > 35,
        precipitacion_mm > 15,
        precipitacion_mm > 3,
        humedad_relativa > 85,
        temperatura_c > 26,
    ]
    etiquetas = ["Tormenta", "Lluvia Fuerte", "Lluvia Ligera", "Nublado", "Soleado"]
    condicion_climatica = np.select(condiciones, etiquetas, default="Parcialmente Nublado")

    # --- nivel de riesgo (categórica ordinal, para apoyo a decisiones) ---
    jitter = rng.uniform(0, 1e-6, n)
    riesgo_score = factor_terreno * 1.6 + (precipitacion_mm / 60) + rng.normal(0, 0.15, n) + jitter
    nivel_riesgo = pd.qcut(riesgo_score, q=4, labels=RIESGO_ORDEN)

    df = pd.DataFrame({
        "fecha": base["fecha"],
        "zona": base["zona"],
        "temperatura_c": np.round(temperatura_c, 1),
        "humedad_relativa": np.round(humedad_relativa, 1),
        "precipitacion_mm": np.round(precipitacion_mm, 1),
        "velocidad_viento_kmh": np.round(velocidad_viento_kmh, 1),
        "presion_atmosferica_hpa": np.round(presion_atmosferica_hpa, 1),
        "poblacion": poblacion.astype(int),
        "condicion_climatica": condicion_climatica,
        "nivel_riesgo": pd.Categorical(nivel_riesgo, categories=RIESGO_ORDEN, ordered=True),
    })

    return df.sort_values(["zona", "fecha"]).reset_index(drop=True)


# ----------------------------------------------------------------------------
# BANNER LATERAL PERSONALIZADO (visible siempre, incluso antes del login)
# ----------------------------------------------------------------------------
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
            <p style="color:#CBD5E1;margin:2px 0 0 0;font-size:0.82rem;">
                Julio de 2026
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


render_banner()

# ----------------------------------------------------------------------------
# CONTROL DE ACCESO (código: 4650)
# ----------------------------------------------------------------------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acceso al Dashboard")
    st.write(
        "Este panel es un ejercicio académico (EAFIT). Ingresa el **código de acceso** "
        "para continuar."
    )
    with st.form("form_login"):
        codigo_ingresado = st.text_input("Código de acceso", type="password", max_chars=10)
        enviado = st.form_submit_button("Ingresar", type="primary")
    if enviado:
        if codigo_ingresado.strip() == CODIGO_ACCESO:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Código incorrecto. Intenta nuevamente.")
    st.stop()

st.sidebar.button("🔓 Cerrar sesión", on_click=lambda: st.session_state.update(autenticado=False))
st.sidebar.divider()

# ----------------------------------------------------------------------------
# BARRA LATERAL: CONFIGURACIÓN DE DATOS + FILTROS
# ----------------------------------------------------------------------------
st.sidebar.subheader("⚙️ Generación de datos sintéticos")

dias_serie = st.sidebar.slider(
    "Días de la serie (por zona)", min_value=10, max_value=60, value=20,
    help="25 zonas x N días = total de registros. Con 20 días se obtienen 500 registros.",
)
total_registros_estimado = dias_serie * len(ZONAS)
st.sidebar.caption(f"📌 Total de registros a generar: **{total_registros_estimado}** "
                    f"({len(ZONAS)} zonas × {dias_serie} días)")

if "semilla" not in st.session_state:
    st.session_state.semilla = 42

col_seed1, col_seed2 = st.sidebar.columns([2, 1])
with col_seed1:
    semilla = st.number_input("Semilla aleatoria", min_value=0, max_value=999999,
                               value=st.session_state.semilla, step=1, key="semilla_input")
with col_seed2:
    st.write("")
    st.write("")
    if st.button("🎲", help="Generar una semilla aleatoria nueva"):
        st.session_state.semilla = int(np.random.randint(0, 999999))
        st.rerun()

st.session_state.semilla = semilla
df = generar_datos(int(dias_serie), int(semilla))

st.sidebar.caption(
    "⚠️ Datos **100% sintéticos** con fines académicos. No constituyen fuente "
    "oficial para decisiones reales de gestión del riesgo."
)

st.sidebar.divider()
st.sidebar.subheader("🔎 Filtros")

fecha_min, fecha_max = df["fecha"].min().date(), df["fecha"].max().date()
rango_fechas = st.sidebar.date_input(
    "Rango de fechas", value=(fecha_min, fecha_max), min_value=fecha_min, max_value=fecha_max,
)
if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    f_ini, f_fin = rango_fechas
else:
    f_ini, f_fin = fecha_min, fecha_max

zonas_sel = st.sidebar.multiselect("Comuna / Municipio", ZONAS, default=ZONAS)
condicion_sel = st.sidebar.multiselect(
    "Condición climática", sorted(df["condicion_climatica"].unique()),
    default=sorted(df["condicion_climatica"].unique()),
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


# ----------------------------------------------------------------------------
# ENCABEZADO
# ----------------------------------------------------------------------------
st.title("🌦️ Clima y Riesgo — Medellín y Área Metropolitana")
st.caption(
    "Datos meteorológicos **sintéticos** por comuna/municipio, pensados como insumo "
    "exploratorio para apoyar decisiones sobre riesgos climáticos (lluvias, "
    "deslizamientos, inundaciones). Proyecto académico — no oficial."
)

if df_f.empty:
    st.warning("No hay registros que coincidan con los filtros seleccionados. Ajusta los filtros en la barra lateral.")
    st.stop()

# ----------------------------------------------------------------------------
# KPIs
# ----------------------------------------------------------------------------
ultima_fecha = df_f["fecha"].max()
snapshot_actual = df_f[df_f["fecha"] == ultima_fecha]
zonas_riesgo_alto = snapshot_actual[snapshot_actual["nivel_riesgo"].isin(["Alto", "Crítico"])]["zona"].nunique()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Registros", f"{len(df_f):,}".replace(",", "."))
k2.metric("Temp. promedio", f"{df_f['temperatura_c'].mean():.1f} °C")
k3.metric("Humedad promedio", f"{df_f['humedad_relativa'].mean():.1f} %")
k4.metric("Precipitación acumulada", f"{df_f['precipitacion_mm'].sum():,.0f} mm".replace(",", "."))
k5.metric(f"Zonas en riesgo Alto/Crítico ({ultima_fecha.date()})", zonas_riesgo_alto)

st.divider()

# ----------------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------------
tab_resumen, tab_series, tab_cuanti, tab_cuali, tab_dinamico, tab_mapa, tab_datos = st.tabs(
    ["📊 Resumen", "⏱️ Serie de Tiempo", "🔢 Estadística Cuantitativa", "🏷️ Estadística Cualitativa",
     "📈 Gráficos Dinámicos", "🗺️ Mapa de Riesgo", "🗂️ Datos"]
)

# ============================== TAB RESUMEN =================================
with tab_resumen:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Temperatura promedio diaria (todas las zonas filtradas)")
        serie_temp = df_f.groupby("fecha", as_index=False)["temperatura_c"].mean()
        fig = px.line(serie_temp, x="fecha", y="temperatura_c", markers=True,
                       title="Temperatura promedio por día")
        fig.update_layout(xaxis_title="Fecha", yaxis_title="°C")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Distribución del nivel de riesgo")
        conteo = df_f["nivel_riesgo"].value_counts().reindex(RIESGO_ORDEN).reset_index()
        conteo.columns = ["nivel_riesgo", "registros"]
        fig = px.pie(conteo, names="nivel_riesgo", values="registros", hole=0.45,
                     category_orders={"nivel_riesgo": RIESGO_ORDEN},
                     color="nivel_riesgo", color_discrete_map=COLOR_RIESGO,
                     title="Proporción de registros por nivel de riesgo")
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Precipitación acumulada por zona (top 10)")
        top_precip = df_f.groupby("zona", as_index=False)["precipitacion_mm"].sum().nlargest(10, "precipitacion_mm")
        fig = px.bar(top_precip, x="precipitacion_mm", y="zona", orientation="h",
                     title="Zonas con mayor precipitación acumulada")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="mm acumulados")
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        st.subheader("Condición climática predominante")
        conteo_cond = df_f["condicion_climatica"].value_counts().reset_index()
        conteo_cond.columns = ["condicion_climatica", "registros"]
        fig = px.bar(conteo_cond, x="condicion_climatica", y="registros",
                     title="Frecuencia de condiciones climáticas")
        st.plotly_chart(fig, use_container_width=True)

# ============================ TAB SERIE DE TIEMPO ============================
with tab_series:
    st.subheader("Comportamiento de una variable en el tiempo, por zona")

    c1, c2, c3 = st.columns(3)
    with c1:
        zonas_ts = st.multiselect("Zonas a graficar", ZONAS, default=ZONAS[:3], key="ts_zonas")
    with c2:
        variable_ts = st.selectbox("Variable", COLUMNAS_NUMERICAS, index=0, key="ts_var")
    with c3:
        ventana_mm = st.slider("Ventana media móvil (días)", 1, 14, 1, key="ts_ventana",
                                help="1 = sin suavizado")

    mostrar_umbral_ts = st.checkbox("Mostrar umbral / línea de alerta", value=(variable_ts == "precipitacion_mm"))
    umbral_ts = None
    if mostrar_umbral_ts:
        v_min, v_max = float(df_f[variable_ts].min()), float(df_f[variable_ts].max())
        umbral_ts = st.slider(f"Valor de alerta para {variable_ts}", v_min, v_max,
                               value=float(np.percentile(df_f[variable_ts], 85)))

    if not zonas_ts:
        st.info("Selecciona al menos una zona para graficar la serie de tiempo.")
    else:
        df_ts = df_f[df_f["zona"].isin(zonas_ts)].sort_values(["zona", "fecha"]).copy()
        if ventana_mm > 1:
            df_ts[variable_ts] = df_ts.groupby("zona")[variable_ts].transform(
                lambda s: s.rolling(ventana_mm, min_periods=1).mean()
            )
        fig = px.line(df_ts, x="fecha", y=variable_ts, color="zona", markers=True,
                       title=f"{variable_ts} en el tiempo por zona")
        if mostrar_umbral_ts and umbral_ts is not None:
            fig.add_hline(y=umbral_ts, line_dash="dash", line_color="#E74C3C",
                          annotation_text=f"Umbral: {umbral_ts:.1f}")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        if mostrar_umbral_ts and umbral_ts is not None:
            ultimos_valores = df_ts[df_ts["fecha"] == df_ts["fecha"].max()]
            en_alerta = ultimos_valores[ultimos_valores[variable_ts] >= umbral_ts]
            if not en_alerta.empty:
                zonas_alerta = ", ".join(en_alerta["zona"].tolist())
                st.warning(f"⚠️ Zonas que superan el umbral en la fecha más reciente: **{zonas_alerta}**")
            else:
                st.success("✅ Ninguna zona supera el umbral en la fecha más reciente.")

# ========================= TAB ESTADÍSTICA CUANTITATIVA =====================
with tab_cuanti:
    st.subheader("Resumen estadístico de variables numéricas")
    resumen_num = df_f[COLUMNAS_NUMERICAS].describe().T
    resumen_num["varianza"] = df_f[COLUMNAS_NUMERICAS].var()
    resumen_num["asimetría (skew)"] = df_f[COLUMNAS_NUMERICAS].skew()
    resumen_num["curtosis"] = df_f[COLUMNAS_NUMERICAS].kurt()
    st.dataframe(resumen_num.style.format("{:.2f}"), use_container_width=True)

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
                     category_orders={"nivel_riesgo": RIESGO_ORDEN}, color_discrete_map=COLOR_RIESGO,
                     title=f"{var_num} por nivel de riesgo")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Matriz de correlación (variables numéricas)")
    corr = df_f[COLUMNAS_NUMERICAS].corr(numeric_only=True)
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                     title="Correlación entre variables numéricas")
    st.plotly_chart(fig, use_container_width=True)

# ========================= TAB ESTADÍSTICA CUALITATIVA ======================
with tab_cuali:
    st.subheader("Frecuencias de variables categóricas")
    var_cat = st.selectbox("Variable categórica a analizar", COLUMNAS_CATEGORICAS, key="cuali_var")

    conteo = df_f[var_cat].value_counts(dropna=False).reset_index()
    conteo.columns = [var_cat, "frecuencia"]
    conteo["porcentaje"] = (conteo["frecuencia"] / conteo["frecuencia"].sum() * 100).round(2)
    moda = df_f[var_cat].mode(dropna=True)
    moda_txt = str(moda.iloc[0]) if not moda.empty else "N/A"

    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Moda", moda_txt)
        st.metric("N° de categorías", df_f[var_cat].nunique())
        st.dataframe(conteo, use_container_width=True, hide_index=True)
    with c2:
        orden = RIESGO_ORDEN if var_cat == "nivel_riesgo" else None
        colores = COLOR_RIESGO if var_cat == "nivel_riesgo" else None
        fig = px.bar(conteo, x=var_cat, y="frecuencia", text="porcentaje", color=var_cat,
                     category_orders={var_cat: orden} if orden else None,
                     color_discrete_map=colores,
                     title=f"Frecuencia de {var_cat}")
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Tabla cruzada (contingencia)")
    c3, c4 = st.columns(2)
    with c3:
        var_a = st.selectbox("Variable 1", COLUMNAS_CATEGORICAS, index=0, key="cruzada_a")
    with c4:
        var_b = st.selectbox("Variable 2", COLUMNAS_CATEGORICAS, index=2, key="cruzada_b")

    if var_a != var_b:
        tabla_cruzada = pd.crosstab(df_f[var_a], df_f[var_b])
        st.dataframe(tabla_cruzada, use_container_width=True)
        fig = px.imshow(tabla_cruzada, text_auto=True, color_continuous_scale="Blues",
                         title=f"Mapa de calor: {var_a} vs {var_b}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Selecciona dos variables distintas para construir la tabla cruzada.")

# ============================ TAB GRÁFICOS DINÁMICOS =========================
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
        eje_x = st.selectbox("Variable eje X", todas_las_columnas, index=todas_las_columnas.index("temperatura_c"))
    with col_c:
        opciones_y = ["(ninguna)"] + todas_las_columnas
        eje_y = st.selectbox(
            "Variable eje Y", opciones_y,
            index=opciones_y.index("precipitacion_mm") if tipo_grafico not in ("Histograma",) else 0,
        )

    col_d, col_e, col_f = st.columns(3)
    with col_d:
        color_por = st.selectbox("Colorear por", ["(ninguno)"] + COLUMNAS_CATEGORICAS)
    with col_e:
        paleta = st.selectbox(
            "Paleta de color",
            ["Plotly", "Vivid", "Bold", "Pastel", "Set2", "D3", "Antique"],
        )
    with col_f:
        opacidad = st.slider("Opacidad", 0.1, 1.0, 0.8)

    mapa_paletas = {
        "Plotly": px.colors.qualitative.Plotly, "Vivid": px.colors.qualitative.Vivid,
        "Bold": px.colors.qualitative.Bold, "Pastel": px.colors.qualitative.Pastel,
        "Set2": px.colors.qualitative.Set2, "D3": px.colors.qualitative.D3,
        "Antique": px.colors.qualitative.Antique,
    }
    secuencia_color = mapa_paletas[paleta]

    with st.expander("🎨 Personalización adicional y umbrales", expanded=False):
        cu1, cu2, cu3 = st.columns(3)
        with cu1:
            titulo_custom = st.text_input("Título del gráfico", value=f"{tipo_grafico}: {eje_x}"
                                           + (f" vs {eje_y}" if eje_y != "(ninguna)" else ""))
        with cu2:
            mostrar_umbral = st.checkbox("Mostrar línea de umbral", value=False)
        with cu3:
            color_umbral = st.color_picker("Color del umbral", "#E45756")

        umbral_valor = None
        eje_umbral = None
        if mostrar_umbral:
            variables_numericas_disp = [c for c in COLUMNAS_NUMERICAS if c in (eje_x, eje_y)]
            if not variables_numericas_disp:
                st.info("El umbral solo aplica si el eje X o Y es una variable numérica.")
            else:
                cu4, cu5 = st.columns(2)
                with cu4:
                    eje_umbral = st.selectbox("Aplicar umbral sobre", variables_numericas_disp)
                with cu5:
                    v_min, v_max = float(df_f[eje_umbral].min()), float(df_f[eje_umbral].max())
                    umbral_valor = st.slider("Valor del umbral", v_min, v_max, (v_min + v_max) / 2)

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
            if mostrar_tendencia and pd.api.types.is_numeric_dtype(df_f[eje_x]) and y_arg:
                datos_validos = df_f[[eje_x, y_arg]].dropna()
                coef = np.polyfit(datos_validos[eje_x], datos_validos[y_arg], 1)
                x_line = np.linspace(datos_validos[eje_x].min(), datos_validos[eje_x].max(), 50)
                y_line = coef[0] * x_line + coef[1]
                fig.add_trace(go.Scatter(x=x_line, y=y_line, mode="lines",
                                          name="Tendencia lineal", line=dict(color="black", dash="dash")))

        elif tipo_grafico == "Barras":
            if y_arg is None:
                agregado = df_f[eje_x].value_counts().reset_index()
                agregado.columns = [eje_x, "conteo"]
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
            fig = px.box(df_f, x=eje_x if not pd.api.types.is_numeric_dtype(df_f[eje_x]) else None,
                          y=y_arg or eje_x, color=color_arg,
                          color_discrete_sequence=secuencia_color, title=titulo_custom)

        elif tipo_grafico == "Línea":
            df_linea = df_f.sort_values(eje_x)
            fig = px.line(df_linea, x=eje_x, y=y_arg or df_linea.select_dtypes("number").columns[0],
                           color=color_arg, color_discrete_sequence=secuencia_color, title=titulo_custom)

        elif tipo_grafico == "Violín":
            fig = px.violin(df_f, x=eje_x if not pd.api.types.is_numeric_dtype(df_f[eje_x]) else None,
                             y=y_arg or eje_x, color=color_arg, box=True,
                             color_discrete_sequence=secuencia_color, title=titulo_custom)

        if fig is not None:
            if mostrar_umbral and umbral_valor is not None and eje_umbral:
                if eje_umbral == eje_x and tipo_grafico in ("Caja (Box)", "Violín", "Barras"):
                    fig.add_hline(y=umbral_valor, line_dash="dash", line_color=color_umbral,
                                  annotation_text=f"Umbral {eje_umbral}: {umbral_valor:.1f}")
                elif eje_umbral == eje_x:
                    fig.add_vline(x=umbral_valor, line_dash="dash", line_color=color_umbral,
                                  annotation_text=f"Umbral {eje_umbral}: {umbral_valor:.1f}")
                else:
                    fig.add_hline(y=umbral_valor, line_dash="dash", line_color=color_umbral,
                                  annotation_text=f"Umbral {eje_umbral}: {umbral_valor:.1f}")

            fig.update_layout(height=550)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecciona una combinación válida de variables para generar la gráfica.")
    except Exception as e:
        st.error(f"No fue posible construir la gráfica con esta combinación de variables: {e}")

# ============================== TAB MAPA DE RIESGO ============================
with tab_mapa:
    st.subheader(f"Mapa de riesgo por zona — corte al {ultima_fecha.date()}")
    st.caption(
        "Coordenadas aproximadas / ilustrativas. Tamaño del punto = población simulada. "
        "Color = nivel de riesgo simulado."
    )

    lat_lon_df = pd.DataFrame([
        {"zona": z, "lat": info["lat"], "lon": info["lon"]} for z, info in ZONAS_INFO.items()
    ])
    snapshot_mapa = snapshot_actual[snapshot_actual["zona"].isin(zonas_sel)].merge(lat_lon_df, on="zona", how="left")

    if snapshot_mapa.empty:
        st.info("No hay datos para la fecha más reciente con los filtros actuales.")
    else:
        fig = px.scatter_mapbox(
            snapshot_mapa, lat="lat", lon="lon", color="nivel_riesgo", size="poblacion",
            category_orders={"nivel_riesgo": RIESGO_ORDEN}, color_discrete_map=COLOR_RIESGO,
            hover_name="zona",
            hover_data={"temperatura_c": True, "humedad_relativa": True, "precipitacion_mm": True,
                        "condicion_climatica": True, "poblacion": True, "lat": False, "lon": False},
            zoom=9.7, height=600, mapbox_style="open-street-map",
            title="Nivel de riesgo simulado por zona",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Ranking de zonas por nivel de riesgo (fecha más reciente)")
        orden_riesgo_num = {"Bajo": 0, "Medio": 1, "Alto": 2, "Crítico": 3}
        ranking = snapshot_mapa.assign(_orden=snapshot_mapa["nivel_riesgo"].map(orden_riesgo_num))
        ranking = ranking.sort_values(["_orden", "precipitacion_mm"], ascending=[False, False])
        st.dataframe(
            ranking[["zona", "nivel_riesgo", "precipitacion_mm", "temperatura_c",
                     "humedad_relativa", "poblacion"]].reset_index(drop=True),
            use_container_width=True,
        )

# ============================== TAB DATOS ====================================
with tab_datos:
    st.subheader("Vista de datos filtrados")
    st.dataframe(df_f, use_container_width=True, height=450)
    csv = df_f.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar CSV filtrado", data=csv,
                        file_name="clima_medellin_sintetico_filtrado.csv", mime="text/csv")

    with st.expander("ℹ️ Diccionario de columnas"):
        st.markdown("""
| Columna | Tipo | Descripción |
|---|---|---|
| `fecha` | datetime | Fecha del registro (serie de tiempo diaria por zona) |
| `zona` | categórica (string) | Comuna de Medellín o municipio del Área Metropolitana |
| `temperatura_c` | numérica (float) | Temperatura simulada en °C |
| `humedad_relativa` | numérica (float) | % de humedad relativa simulada |
| `precipitacion_mm` | numérica (float) | Precipitación simulada en mm |
| `velocidad_viento_kmh` | numérica (float) | Velocidad del viento simulada en km/h |
| `presion_atmosferica_hpa` | numérica (float) | Presión atmosférica simulada en hPa |
| `poblacion` | numérica (int) | Población aproximada de la zona (constante por zona) |
| `condicion_climatica` | categórica (string) | Soleado / Nublado / Lluvia / Tormenta, derivada de precipitación y humedad |
| `nivel_riesgo` | categórica ordinal | Bajo / Medio / Alto / Crítico — combina terreno y precipitación |
        """)
