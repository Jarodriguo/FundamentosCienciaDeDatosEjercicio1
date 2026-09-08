# Dashboard de Clima y Riesgo — Medellín y Área Metropolitana

Dashboard interactivo que simula y analiza condiciones meteorológicas diarias en las 16 comunas de Medellín y los 9 municipios del Valle de Aburrá, con clasificación de niveles de riesgo climático por zona.

[![Abrir en Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://fundamentoscienciadedatosejercicio1-sizunwk4appjfyxtlrqxs7.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-app-red)
![Plotly](https://img.shields.io/badge/Plotly-visualización-purple)

<!-- Reemplaza esta línea por una captura o GIF del dashboard: ![Demo](assets/demo.gif) -->

---

## ⚠️ Sobre los datos

**Los datos de esta aplicación son 100% sintéticos y se generan dentro de la propia app.** No provienen de ninguna estación meteorológica ni entidad oficial, y no deben usarse para decisiones reales de gestión del riesgo. Para información oficial del Valle de Aburrá están el [SIATA](https://siata.gov.co/) y el DAGRAN.

La simulación no es ruido aleatorio: replica relaciones físicas conocidas (ver [Modelo de simulación](#modelo-de-simulación)) para que el análisis exploratorio tenga sentido estadístico. El objetivo del proyecto es demostrar el flujo completo de una herramienta analítica, no producir un pronóstico.

---

## Contexto y objetivo

El Valle de Aburrá es un valle estrecho con laderas densamente pobladas, donde las temporadas de lluvia se traducen en riesgo real de deslizamientos e inundaciones. La pregunta que guía el ejercicio es de herramienta, no de pronóstico:

> ¿Cómo debería verse un tablero que permita a un equipo de gestión del riesgo explorar datos meteorológicos por comuna, detectar zonas que superan umbrales de alerta y comparar el comportamiento entre territorios?

El proyecto construye esa herramienta de punta a punta: genera los datos, los procesa, los analiza estadísticamente y los presenta en una interfaz que un usuario no técnico puede operar.

Desarrollado como ejercicio del curso **Fundamentos de Ciencia de Datos (EAFIT, 2026)**.

---

## Qué hace la aplicación

| Módulo | Contenido |
|---|---|
| **Resumen** | KPIs generales, temperatura promedio diaria, distribución de niveles de riesgo, top 10 de zonas por precipitación acumulada y frecuencia de condiciones climáticas |
| **Serie de tiempo** | Evolución de cualquier variable por zona, con media móvil configurable (1–14 días) y línea de umbral que dispara alertas sobre las zonas que la superan |
| **Estadística cuantitativa** | Descriptivos extendidos (media, desviación, varianza, asimetría, curtosis), histogramas con caja marginal, comparación por nivel de riesgo y matriz de correlación |
| **Estadística cualitativa** | Tablas de frecuencia con porcentajes, moda, número de categorías y tablas de contingencia cruzadas con mapa de calor |
| **Gráficos dinámicos** | Constructor de visualizaciones: 6 tipos de gráfico, ejes y variable de color seleccionables, 7 paletas, opacidad, título editable, líneas de umbral y ajuste lineal de tendencia |
| **Mapa de riesgo** | Mapa geoespacial sobre OpenStreetMap con las 25 zonas; color por nivel de riesgo, tamaño por población, más ranking ordenado de zonas |
| **Datos** | Tabla filtrada, descarga en CSV y diccionario de columnas |

Todos los módulos responden a un mismo conjunto de filtros globales: rango de fechas, zonas, condición climática y nivel de riesgo.

---

## Modelo de simulación

El generador (`generar_datos`) produce una serie de tiempo diaria continua por zona. Cada variable se deriva de relaciones físicas plausibles en lugar de muestrearse de forma independiente:

- **Temperatura.** Base de 23 °C ajustada por zona (El Poblado más frío, Itagüí más cálido), con un ciclo sinusoidal estacional y ruido gaussiano.
- **Humedad relativa.** Inversamente proporcional a la desviación de temperatura, acotada entre 35 % y 98 %.
- **Precipitación.** Distribución **gamma** (asimétrica a la derecha, como la lluvia real: muchos días secos, pocos días de aguacero), escalada por el `factor_terreno` de cada zona. Las laderas reciben más lluvia que el fondo del valle.
- **Viento y presión.** Ambos reaccionan a los eventos de lluvia. La presión ronda los **855 hPa**, coherente con los ~1.500 m s.n.m. del valle.
- **Condición climática.** Variable categórica derivada en cascada a partir de precipitación, humedad y temperatura.
- **Nivel de riesgo.** Índice compuesto (terreno + precipitación + ruido) discretizado en cuartiles ordinales: Bajo, Medio, Alto, Crítico.

Cada zona tiene parámetros propios de población, factor de terreno, ajuste térmico y coordenadas, de modo que las diferencias entre comunas son estructurales y no fruto del azar.

**Reproducibilidad:** la semilla aleatoria es configurable desde la interfaz y el generador está cacheado con `@st.cache_data`. Con la misma semilla y el mismo número de días, el resultado es idéntico.

---

## Diccionario de datos

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha` | datetime | Fecha del registro |
| `zona` | categórica | Comuna de Medellín o municipio del Área Metropolitana |
| `temperatura_c` | float | Temperatura simulada (°C) |
| `humedad_relativa` | float | Humedad relativa simulada (%) |
| `precipitacion_mm` | float | Precipitación simulada (mm) |
| `velocidad_viento_kmh` | float | Velocidad del viento simulada (km/h) |
| `presion_atmosferica_hpa` | float | Presión atmosférica simulada (hPa) |
| `poblacion` | int | Población aproximada de la zona |
| `condicion_climatica` | categórica | Soleado, Nublado, Parcialmente Nublado, Lluvia Ligera, Lluvia Fuerte, Tormenta |
| `nivel_riesgo` | categórica ordinal | Bajo, Medio, Alto, Crítico |

El volumen es configurable: 25 zonas × N días (10 a 60). Con el valor por defecto de 20 días se generan 500 registros.

---

## Stack

- **Python 3.12**
- **Streamlit** — interfaz, estado de sesión, caché y filtros reactivos
- **pandas** — manipulación tabular, `groupby`, `crosstab`, `qcut`, medias móviles
- **NumPy** — generación aleatoria con `default_rng`, distribuciones y lógica vectorizada con `np.select`
- **Plotly Express / Graph Objects** — visualización interactiva y mapas

---

## Ejecución local

```bash
git clone https://github.com/Jarodriguo/FundamentosCienciaDeDatosEjercicio1.git
cd FundamentosCienciaDeDatosEjercicio1

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
streamlit run main_app.py
```

La app abre en `http://localhost:8501`. No requiere archivos de datos ni credenciales: todo se genera en memoria.

> **Nota:** la versión desplegada solicita un código de acceso al ingresar. El código es `4650`.
> <!-- Elimina estas dos líneas si retiras la pantalla de acceso del código. -->

---

## Decisiones técnicas

**Por qué datos sintéticos.** El ejercicio requería controlar la estructura del dataset (10 columnas con tipos numéricos, categóricos nominales y categóricos ordinales) para ejercitar el análisis estadístico completo. Generarlos permitió además garantizar reproducibilidad y evitar dependencias de APIs externas en el despliegue.

**Por qué distribución gamma para la precipitación.** Una normal produciría lluvia simétrica alrededor de un promedio, que no se parece a la realidad. La gamma genera la asimetría característica: mayoría de días con poca o nula lluvia y una cola de eventos intensos, que es justamente donde vive el riesgo.

**Por qué cuartiles para el nivel de riesgo.** Usar `qcut` sobre el índice compuesto garantiza que las cuatro categorías estén siempre pobladas, sin importar la semilla o el rango de fechas. Con umbrales fijos, ciertas combinaciones dejarían categorías vacías y romperían los gráficos comparativos.

**Caché sobre la generación.** `@st.cache_data` evita regenerar el dataset completo con cada interacción del usuario, que en Streamlit reejecuta el script entero. Los filtros operan sobre el DataFrame ya construido.

---

## Limitaciones conocidas

- Los datos son simulados; el dashboard no produce conclusiones sobre el clima real de Medellín.
- Las coordenadas de las zonas son aproximaciones puntuales, no polígonos administrativos reales.
- El índice de riesgo es una construcción del ejercicio, no una metodología validada de gestión del riesgo.
- La pantalla de acceso es una demostración de manejo de estado de sesión, no un mecanismo de seguridad.

---

## Posibles extensiones

- Sustituir la generación sintética por consumo de la API pública del SIATA para trabajar con mediciones reales.
- Reemplazar los puntos del mapa por polígonos de comunas usando GeoJSON oficial y `folium` o `pydeck`.
- Añadir un modelo de predicción de precipitación a corto plazo sobre la serie de tiempo.
- Exportar reportes en PDF por zona.

---

## Autor

**Juan Alberto Rodríguez**
GitHub: [@Jarodriguo](https://github.com/Jarodriguo)

Proyecto académico — Fundamentos de Ciencia de Datos, EAFIT, 2026.
