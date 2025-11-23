import streamlit as st 
import pandas as pd
from sqlalchemy import create_engine

# -----------------------
# Conexión a MySQL
# -----------------------
user = "etl_user"
password = "TuPasswordFuerte"
host = "192.168.0.128"
port = 3307
database = "dw_soporte"   # BD donde está vw_cubo_proyectos

engine = create_engine(
    f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
)

@st.cache_data
def cargar_cubo():
    query = "SELECT * FROM vw_cubo_proyectos"
    df = pd.read_sql(query, engine)

    # Asegurar tipo datetime y crear nombre de mes
    df["fecha_completa"] = pd.to_datetime(df["fecha_completa"])

    mapa_meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    df["nombre_mes"] = df["fecha_completa"].dt.month.map(mapa_meses)

    return df

df = cargar_cubo()

st.title("Cubo OLAP de Proyectos - Dashboard con Streamlit")

# Si no hay datos, salimos
if df.empty:
    st.error("No hay datos en vw_cubo_proyectos. Verifica tu DW.")
    st.stop()

# -----------------------
# Controles de SLICE / DICE (filtros)
# -----------------------

st.sidebar.header("Filtros (Slice / Dice)")

# Filtro por rango de años (corregido)
anios = sorted(df["anio"].dropna().unique())

if len(anios) == 0:
    st.error("No hay años disponibles en los datos.")
    st.stop()
elif len(anios) == 1:
    # Solo un año: usamos ese y no mostramos slider
    anio_min = anio_max = anios[0]
    st.sidebar.write(f"Datos solo del año: {anio_min}")
else:
    anio_min, anio_max = st.sidebar.select_slider(
        "Rango de años",
        options=anios,
        value=(anios[0], anios[-1])
    )

# Filtro por industria (multi-select)
industrias = sorted(df["industria"].dropna().unique())
industrias_sel = st.sidebar.multiselect(
    "Industrias",
    options=industrias,
    default=industrias  # todas por default
)

# Filtro por estado
estados = sorted(df["estado"].dropna().unique())
estados_sel = st.sidebar.multiselect(
    "Estados del proyecto",
    options=estados,
    default=estados
)

# Aplicar filtros (slice/dice)
mask = (
    (df["anio"] >= anio_min) &
    (df["anio"] <= anio_max) &
    (df["industria"].isin(industrias_sel)) &
    (df["estado"].isin(estados_sel))
)
df_filtrado = df[mask]

st.write(f"Proyectos filtrados: {len(df_filtrado)}")

if df_filtrado.empty:
    st.warning("Los filtros seleccionados no devuelven proyectos.")
    st.stop()

# -----------------------
# Selección de medida y dimensiones (Pivot + Roll-up/Drill-down)
# -----------------------

st.sidebar.header("Configuración del cubo")

medidas = {
    "Presupuesto total": "presupuesto",
    "Costo real total": "costo_real",
    "Desviación presupuestal": "desviacion_presupuestal",
    "Horas estimadas": "horas_estimadas_total",
    "Horas reales": "horas_reales_total",
    "Defectos reportados": "defectos_reportados",
    "Costo de defectos": "costo_defecto"
}

nombre_medida = st.sidebar.selectbox("Medida", list(medidas.keys()))
col_medida = medidas[nombre_medida]

# Dimensión para filas
dim_filas_opciones = {
    "Año": "anio",
    "Trimestre": "trimestre",
    "Mes": "nombre_mes",
    "Industria": "industria",
    "Cliente": "nombre_cliente",
    "Tipo de proyecto": "tipo_proyecto",
    "Equipo": "nombre_equipo",
    "Estado": "estado"
}

dim_filas_nombre = st.sidebar.selectbox(
    "Dimensión para filas (ROW)",
    list(dim_filas_opciones.keys())
)
dim_filas = dim_filas_opciones[dim_filas_nombre]

# Dimensión para columnas (para pivot)
dim_cols_nombre = st.sidebar.selectbox(
    "Dimensión para columnas (COLUMN)",
    ["(Ninguna)"] + list(dim_filas_opciones.keys())
)

# -----------------------
# Agregación (ROLL-UP) y tabla dinámica (PIVOT)
# -----------------------

if dim_cols_nombre == "(Ninguna)":
    # Solo agrupación simple (roll-up)
    tabla = (
        df_filtrado
        .groupby(dim_filas, dropna=False)[col_medida]
        .sum()
        .reset_index()
        .sort_values(by=col_medida, ascending=False)
    )
    st.subheader(f"{nombre_medida} por {dim_filas_nombre}")
    st.dataframe(tabla)
else:
    # Pivot (filas + columnas = pivot)
    dim_cols = dim_filas_opciones[dim_cols_nombre]
    tabla_pivot = pd.pivot_table(
        df_filtrado,
        values=col_medida,
        index=dim_filas,
        columns=dim_cols,
        aggfunc="sum",
        fill_value=0
    )
    st.subheader(f"{nombre_medida} por {dim_filas_nombre} y {dim_cols_nombre}")
    st.dataframe(tabla_pivot)

# -----------------------
# DRILL-DOWN (desglose)
# -----------------------
st.markdown("### Drill-down")
st.write(
    "Selecciona un valor de la dimensión de filas para hacer drill-down a un nivel más detallado."
)

valores_fila = sorted(df_filtrado[dim_filas].dropna().unique())
if len(valores_fila) == 0:
    st.info("No hay valores disponibles para drill-down con los filtros actuales.")
else:
    valor_fila = st.selectbox(
        f"Valor de {dim_filas_nombre} para drill-down",
        valores_fila
    )

    df_drill = df_filtrado[df_filtrado[dim_filas] == valor_fila].copy()

    # Ejemplo de drill-down: si estabas por Año, bajar a Mes y Proyecto
    if dim_filas == "anio":
        cols_dd = ["anio", "nombre_mes", "nombre_proyecto", col_medida]
    elif dim_filas == "industria":
        cols_dd = ["industria", "nombre_cliente", "nombre_proyecto", col_medida]
    else:
        # fallback genérico
        cols_dd = [dim_filas, "nombre_proyecto", col_medida]

    st.write(f"Desglose de {nombre_medida} para {dim_filas_nombre} = {valor_fila}")
    st.dataframe(df_drill[cols_dd].sort_values(by=col_medida, ascending=False))
