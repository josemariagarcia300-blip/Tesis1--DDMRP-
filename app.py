import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- Configuración de la Página de Streamlit ---
st.set_page_config(
    page_title="Análisis DDMRP de Familias de Productos",
    layout="wide", # Usa un layout "wide" para mejor visualización
    initial_sidebar_state="expanded"
)

# --- 1. TUS DATOS REALES (Base de la tesis) ---
data = {
    'Familia': ['BILLETERA', 'CASACA', 'CARTERA', 'MORRAL', 'CORREA', 'MONEDERO', 'MOCHILA', 'ZAPATO', 'OTRAS_18'],
    'Venta_Soles': [1407357, 936994, 833176, 594924, 213614, 173627, 108392, 99848, 77197],
    'Unidades_Vendidas': [5614, 723, 1273, 1077, 1099, 1334, 149, 250, 2242]
}
df = pd.DataFrame(data)

# --- 2. ENRIQUECIMIENTO DE DATOS (Cálculos reales + Simulación inteligente) ---
# Calculamos el precio promedio real por unidad
df['Precio_Promedio'] = (df['Venta_Soles'] / df['Unidades_Vendidas']).round(2)

# Asignamos perfiles DDMRP basados en el análisis anterior
perfiles = {
    'BILLETERA': {'Perfil': 'Estable', 'LT': 30, 'Factor_Var': 0.5, 'MOQ': 50},
    'CASACA': {'Perfil': 'Alto Valor', 'LT': 60, 'Factor_Var': 1.5, 'MOQ': 20},
    'CARTERA': {'Perfil': 'Valor Medio', 'LT': 45, 'Factor_Var': 0.8, 'MOQ': 30},
    'MORRAL': {'Perfil': 'Valor Medio', 'LT': 45, 'Factor_Var': 0.8, 'MOQ': 30},
    'CORREA': {'Perfil': 'Valor Medio', 'LT': 45, 'Factor_Var': 0.8, 'MOQ': 30},
    'MONEDERO': {'Perfil': 'Estable', 'LT': 30, 'Factor_Var': 0.5, 'MOQ': 50},
    'MOCHILA': {'Perfil': 'Alto Valor', 'LT': 60, 'Factor_Var': 1.5, 'MOQ': 20},
    'ZAPATO': {'Perfil': 'Valor Medio', 'LT': 45, 'Factor_Var': 0.8, 'MOQ': 30},
    'OTRAS_18': {'Perfil': 'Cola Larga', 'LT': 45, 'Factor_Var': 1.2, 'MOQ': 100}
}

df['Perfil_DDMRP'] = df['Familia'].map(lambda x: perfiles[x]['Perfil'])
df['Lead_Time'] = df['Familia'].map(lambda x: perfiles[x]['LT'])
df['Factor_Variabilidad'] = df['Familia'].map(lambda x: perfiles[x]['Factor_Var'])
df['MOQ'] = df['Familia'].map(lambda x: perfiles[x]['MOQ'])

# --- 3. CÁLCULOS DDMRP (El Motor) ---
# Asumimos una ventana de análisis de 90 días para el ADU (Average Daily Usage)
dias_analisis = 90
df['ADU'] = (df['Unidades_Vendidas'] / dias_analisis).round(2)

# Fórmulas del artículo Nblock
factor_lead_time = 0.5 # Factor estándar base para zona roja y verde

df['Zona_Roja_Base'] = (df['ADU'] * df['Lead_Time'] * factor_lead_time).round(1)
df['Zona_Roja_Seguridad'] = (df['Zona_Roja_Base'] * df['Factor_Variabilidad']).round(1)
df['Zona_Roja_Total'] = (df['Zona_Roja_Base'] + df['Zona_Roja_Seguridad']).round(1) # Piso del buffer

df['Zona_Amarilla'] = (df['ADU'] * df['Lead_Time']).round(1) # Cobertura

# Zona Verde: El mayor de tres valores (simplificado a MOQ vs consumo durante LT)
df['Zona_Verde'] = df.apply(lambda row: max(
    row['ADU'] * row['Lead_Time'] * factor_lead_time,
    row['MOQ']
), axis=1).round(1)

df['Tope_Buffer'] = (df['Zona_Roja_Total'] + df['Zona_Amarilla'] + df['Zona_Verde']).round(1)
df['Punto_Reposicion'] = (df['Zona_Roja_Total'] + df['Zona_Amarilla']).round(1)

# --- 4. SIMULACIÓN DE ESTADO ACTUAL (Para el Dashboard Comercial) ---
# Simulamos un Stock físico y una Demanda Calificada (pedidos en mano) aleatorios pero realistas
np.random.seed(42)
df['Stock_Fisico'] = np.random.randint(df['Zona_Roja_Total'], df['Tope_Buffer'] * 1.2).astype(int)
df['Ordenes_Transito'] = np.random.randint(0, df['MOQ']).astype(int)
df['Demanda_Calificada'] = np.random.randint(0, df['Zona_Amarilla']).astype(int)

# Ecuación de Flujo Disponible (Net Flow Position)
df['Flujo_Disponible'] = df['Stock_Fisico'] + df['Ordenes_Transito'] - df['Demanda_Calificada']

# --- 5. LÓGICA DEL SEMÁFORO COMERCIAL (Traducción para el Área Comercial) ---
def determinar_semaforo(row):
    if row['Flujo_Disponible'] <= row['Zona_Roja_Total']:
        return "🔴 CRÍTICO: Proteger Stock / Ofrecer Sustituto"
    elif row['Flujo_Disponible'] <= row['Punto_Reposicion']:
        return "🟡 PRECAUCIÓN: En Reposición / No promocionar"
    elif row['Flujo_Disponible'] > row['Tope_Buffer']:
        return "🟠 EXCESO: Sugerir Liquidación / Combo"
    else:
        return "🟢 SALUDABLE: Venta Libre / Push de Marketing"

df['Semaforo_Comercial'] = df.apply(determinar_semaforo, axis=1)

# --- Columnas relevantes para la tesis ---
columnas_tesis = [
    'Familia', 'Perfil_DDMRP', 'ADU', 'Lead_Time', 'Factor_Variabilidad',
    'Zona_Roja_Total', 'Zona_Amarilla', 'Punto_Reposicion', 'Tope_Buffer',
    'Stock_Fisico', 'Flujo_Disponible', 'Semaforo_Comercial'
]

# --- Función para generar resumen general de acciones ---
def generar_resumen_general(dataframe):
    resumen = {
        'Acción': [],
        'Unidades_Impactadas': [],
        'Familias_Impactadas': []
    }

    # Acciones de reposición (CRÍTICO y PRECAUCIÓN)
    df_critico_precaucion = dataframe[dataframe['Semaforo_Comercial'].isin([
        "🔴 CRÍTICO: Proteger Stock / Ofrecer Sustituto",
        "🟡 PRECAUCIÓN: En Reposición / No promocionar"
    ])]
    if not df_critico_precaucion.empty:
        # Para unidades impactadas, calcular cuánto falta para el Punto_Reposicion o Zona_Roja_Total
        unidades_necesarias = (df_critico_precaucion['Punto_Reposicion'] - df_critico_precaucion['Flujo_Disponible']).sum()
        resumen['Acción'].append('Reponer Inventario')
        resumen['Unidades_Impactadas'].append(max(0, int(unidades_necesarias)))
        resumen['Familias_Impactadas'].append(df_critico_precaucion['Familia'].tolist())

    # Acciones de campaña (SALUDABLE)
    df_saludable = dataframe[dataframe['Semaforo_Comercial'] == "🟢 SALUDABLE: Venta Libre / Push de Marketing"]
    if not df_saludable.empty:
        # Para unidades impactadas, calcular el excedente sobre el Punto_Reposicion (mantener saludable)
        unidades_disponibles = (df_saludable['Flujo_Disponible'] - df_saludable['Punto_Reposicion']).sum()
        resumen['Acción'].append('Promocionar / Campañas')
        resumen['Unidades_Impactadas'].append(max(0, int(unidades_disponibles)))
        resumen['Familias_Impactadas'].append(df_saludable['Familia'].tolist())

    # Acciones de liquidación (EXCESO)
    df_exceso = dataframe[dataframe['Semaforo_Comercial'] == "🟠 EXCESO: Sugerir Liquidación / Combo"]
    if not df_exceso.empty:
        # Para unidades impactadas, calcular el excedente sobre el Tope_Buffer
        unidades_exceso = (df_exceso['Flujo_Disponible'] - df_exceso['Tope_Buffer']).sum()
        resumen['Acción'].append('Liquidar Exceso')
        resumen['Unidades_Impactadas'].append(max(0, int(unidades_exceso)))
        resumen['Familias_Impactadas'].append(df_exceso['Familia'].tolist())

    resumen_df = pd.DataFrame(resumen)
    return resumen_df

# Generar el resumen general una vez
resumen_final = generar_resumen_general(df)

# --- Sidebar Navigation ---
st.sidebar.header("Módulos Principales")
modulo_seleccionado = st.sidebar.radio(
    "Ir a",
    ['Comercialización', 'Operatividad', 'Inventario', 'Distribución']
)

# --- Content Area based on Main Module Selection ---
if modulo_seleccionado == 'Comercialización':
    st.title("📈 Análisis DDMRP de Familias de Productos - Comercialización")
    st.markdown("Una herramienta interactiva para la gestión de inventarios basada en la metodología Demand Driven MRP para el área comercial.")

    st.sidebar.header("Secciones de Comercialización")
    seccion_comercializacion = st.sidebar.radio(
        "Ver",
        ['Dashboard', 'Detalle de Familias', 'Resumen de Acciones', 'Otras Secciones (Próximamente)']
    )

    if seccion_comercializacion == 'Dashboard':
        st.subheader("Tabla Resumen DDMRP")
        st.dataframe(df[columnas_tesis])

        # --- Visualización 1: Comparación de Flujo Disponible vs. Tope de Buffer ---
        st.subheader("📊 Comparación de Flujo Disponible vs. Tope de Buffer por Familia")
        st.markdown(
            "Este gráfico de barras muestra:\n\n"+
            "*   **Flujo_Disponible** (azul): Representa el inventario real disponible, ajustado por pedidos en tránsito y demanda comprometida.\n"+
            "*   **Tope_Buffer** (naranja): Es el nivel máximo deseado del buffer de inventario, incluyendo las zonas Roja, Amarilla y Verde, que indica la capacidad máxima de inventario antes de considerarse un exceso.\n\n"+
            "Al comparar estas dos métricas, se puede identificar visualmente qué familias tienen un inventario por debajo, dentro o por encima de su nivel óptimo, ayudando a tomar decisiones sobre reabastecimiento o liquidación de stock."
        )

        fig_buffer, ax_buffer = plt.subplots(figsize=(12, 6))
        sns.barplot(x='Familia', y='value', hue='variable', data=pd.melt(df, id_vars=['Familia'], value_vars=['Flujo_Disponible', 'Tope_Buffer']), ax=ax_buffer)
        ax_buffer.set_title('Comparación de Flujo Disponible vs. Tope de Buffer por Familia')
        ax_buffer.set_xlabel('Familia')
        ax_buffer.set_ylabel('Cantidad')
        ax_buffer.tick_params(axis='x', rotation=45)
        ax_buffer.legend(title='Métrica')
        plt.tight_layout()
        st.pyplot(fig_buffer)

        # --- Visualización 2: Resumen de Artículos por Estado de Semáforo Comercial ---
        st.subheader("🚦 Resumen de Artículos por Estado de Semáforo Comercial")
        st.markdown("Esta tabla muestra la cantidad de familias de productos en cada estado del semáforo comercial (Crítico, Precaución, Exceso, Saludable).")
        st.dataframe(df['Semaforo_Comercial'].value_counts().reset_index().rename(columns={'index': 'Estado del Semáforo', 'Semaforo_Comercial': 'Cantidad de Familias'}))

    elif seccion_comercializacion == 'Detalle de Familias':
        # --- Interfaz Interactiva para seleccionar una Familia y mostrar su información ---
        st.subheader("🔍 Información Detallada por Familia (Interactiva)")
        st.markdown("Selecciona una familia de la lista para ver su información DDMRP detallada.")

        familia_seleccionada = st.radio(
            'Selecciona una Familia:',
            options=df['Familia'].tolist(),
            index=0 # Default to the first family
        )

        if familia_seleccionada:
            info_familia = df[df['Familia'] == familia_seleccionada][columnas_tesis]
            st.write(f"#### Información detallada para {familia_seleccionada}")
            st.dataframe(info_familia)

    elif seccion_comercializacion == 'Resumen de Acciones':
        # --- Resumen General de Acciones Sugeridas ---
        st.subheader("📋 Resumen General de Acciones Sugeridas")
        st.markdown("Aquí tienes un resumen consolidado que te indica qué acciones tomar (reponer, mantener, campañas) y los totales de unidades disponibles para cada tipo de acción, según el `Semaforo_Comercial`.")
        st.dataframe(resumen_final)

elif modulo_seleccionado == 'Operatividad':
    st.title("Módulo de Operatividad")
    st.write("Contenido para Operatividad (Próximamente)...")

elif modulo_seleccionado == 'Inventario':
    st.title("Módulo de Inventario")
    st.write("Contenido para Inventario (Próximamente)...")

elif modulo_seleccionado == 'Distribución':
    st.title("Módulo de Distribución")
    st.write("Contenido para Distribución (Próximamente)...")
