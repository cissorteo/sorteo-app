import streamlit as st
from supabase import create_client
import random
from datetime import datetime
from itertools import combinations

# ====================================
# CONFIG
# ====================================

st.set_page_config(
    page_title="🎲 Sorteo Pitufo",
    page_icon="🎲",
    layout="centered"
)

# ====================================
# SUPABASE
# ====================================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ====================================
# ESTILO
# ====================================

st.markdown("""
<style>

.stButton > button {
    width: 100%;
    border-radius: 12px;
    height: 50px;
    font-size: 18px;
    font-weight: bold;
}

.stTextInput > div > div > input {
    border-radius: 10px;
}

.block-container {
    padding-top: 2rem;
}

</style>
""", unsafe_allow_html=True)

# ====================================
# FUNCIONES PERSONAS
# ====================================

def get_personas():
    res = supabase.table("personas").select("nombre").execute()
    return [x["nombre"] for x in res.data]

def add_persona(nombre):
    try:
        supabase.table("personas").insert({
            "nombre": nombre
        }).execute()
    except:
        pass

def delete_persona(nombre):
    supabase.table("personas").delete().eq(
        "nombre", nombre
    ).execute()

# ====================================
# FUNCIONES HISTORIAL
# ====================================

def get_hist():
    res = supabase.table("historial").select("*").execute()
    return res.data

def guardar_historial(fecha, g1, g2):

    supabase.table("historial").insert({
        "fecha": fecha,
        "grupo1": ", ".join(g1),
        "grupo2": ", ".join(g2)
    }).execute()

def borrar_historial():
    supabase.table("historial").delete().neq(
        "id", 0
    ).execute()

# ====================================
# ESTADÍSTICAS
# ====================================

def generar_estadisticas():

    historial = get_hist()
    conteo = {}

    for fila in historial:

        grupos = [
            fila["grupo1"].split(", "),
            fila["grupo2"].split(", ")
        ]

        for grupo in grupos:

            for a, b in combinations(grupo, 2):

                clave = tuple(sorted([a, b]))

                conteo[clave] = conteo.get(clave, 0) + 1

    return conteo

# ====================================
# GENERAR SORTEO
# ====================================

def generar_sorteo(tam_grupo1):

    personas = get_personas()

    if len(personas) < 2:
        return None, None, None

    mejor_score = 999999
    mejor_g1 = None
    mejor_g2 = None

    estadisticas = generar_estadisticas()

    for _ in range(3000):

        random.shuffle(personas)

        grupo1 = personas[:tam_grupo1]
        grupo2 = personas[tam_grupo1:]

        score = 0

        for grupo in [grupo1, grupo2]:

            for a, b in combinations(grupo, 2):

                clave = tuple(sorted([a, b]))

                score += estadisticas.get(clave, 0)

        if score < mejor_score:

            mejor_score = score
            mejor_g1 = grupo1[:]
            mejor_g2 = grupo2[:]

    fecha = datetime.now().strftime("%d/%m/%Y")

    guardar_historial(
        fecha,
        mejor_g1,
        mejor_g2
    )

    return fecha, mejor_g1, mejor_g2

# ====================================
# UI
# ====================================

st.title("🎲 Sorteo Pitufo")

# ====================================
# PERSONAS
# ====================================

st.subheader("👥 Personas")

if "nuevo_nombre" not in st.session_state:
    st.session_state.nuevo_nombre = ""

def agregar_persona():

    nombre = st.session_state.nuevo_nombre.strip()

    if nombre != "":
        add_persona(nombre)

    st.session_state.nuevo_nombre = ""

st.text_input(
    "Añadir persona",
    key="nuevo_nombre",
    on_change=agregar_persona
)

personas = get_personas()

for persona in personas:

    col1, col2 = st.columns([5,1])

    col1.write(persona)

    if col2.button("❌", key=persona):

        delete_persona(persona)
        st.rerun()

# ====================================
# CONFIGURACIÓN GRUPOS
# ====================================

st.markdown("---")

st.subheader("⚙️ Configuración grupos")

total_personas = len(personas)

if total_personas >= 2:

    tam_grupo1 = st.slider(
        "Personas en Grupo 1",
        min_value=1,
        max_value=total_personas - 1,
        value=total_personas // 2
    )

    tam_grupo2 = total_personas - tam_grupo1

    st.info(
        f"Grupo 1: {tam_grupo1} personas | "
        f"Grupo 2: {tam_grupo2} personas"
    )

# ====================================
# BOTÓN SORTEO
# ====================================

st.markdown("---")

if st.button("🎲 Generar sorteo"):

    if total_personas < 2:

        st.error("Necesitas al menos 2 personas")

    else:

        fecha, grupo1, grupo2 = generar_sorteo(
            tam_grupo1
        )

        st.success(f"Sorteo generado ({fecha})")

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("Grupo 1")

            for p in grupo1:
                st.write(f"✅ {p}")

        with col2:

            st.subheader("Grupo 2")

            for p in grupo2:
                st.write(f"✅ {p}")

# ====================================
# HISTORIAL
# ====================================

st.markdown("---")

st.subheader("📜 Historial")

historial = get_hist()

for fila in reversed(historial):

    with st.expander(f"📅 {fila['fecha']}"):

        st.write("### Grupo 1")
        st.write(fila["grupo1"])

        st.write("### Grupo 2")
        st.write(fila["grupo2"])

# ====================================
# BORRAR HISTORIAL
# ====================================

if st.button("🗑️ Borrar historial"):

    borrar_historial()

    st.success("Historial borrado")

    st.rerun()

# ====================================
# ESTADÍSTICAS
# ====================================

st.markdown("---")

st.subheader("📊 Estadísticas")

stats = generar_estadisticas()

if stats:

    ranking = sorted(
        stats.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for pareja, veces in ranking[:15]:

        st.write(
            f"👥 {pareja[0]} + {pareja[1]} "
            f"→ {veces} veces"
        )

else:

    st.info("Todavía no hay estadísticas")
