import streamlit as st
from supabase import create_client
import random
from datetime import datetime
from itertools import combinations

# -------- CONFIG --------
st.set_page_config(page_title="Sorteo Pro", page_icon="🎲")

# -------- CONEXIÓN --------
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# -------- FUNCIONES --------

# PERSONAS
def get_personas():
    res = supabase.table("personas").select("nombre").execute()
    return [x["nombre"] for x in res.data]

def add_persona(nombre):
    try:
        supabase.table("personas").insert({"nombre": nombre}).execute()
    except:
        pass

def delete_persona(nombre):
    supabase.table("personas").delete().eq("nombre", nombre).execute()

# HISTORIAL
def get_hist():
    res = supabase.table("historial").select("*").execute()
    return res.data

def guardar(fecha, g1, g2):
    supabase.table("historial").insert({
        "fecha": fecha,
        "grupo1": ",".join(g1),
        "grupo2": ",".join(g2)
    }).execute()

def borrar_hist():
    supabase.table("historial").delete().neq("id", 0).execute()

# LÓGICA
def coincidencias():
    hist = get_hist()
    conteo = {}

    for h in hist:
        for grupo in [h["grupo1"].split(","), h["grupo2"].split(",")]:
            for a, b in combinations(grupo, 2):
                clave = tuple(sorted([a, b]))
                conteo[clave] = conteo.get(clave, 0) + 1

    return conteo

def generar():
    personas = get_personas()
    n = len(personas)

    if n < 2:
        return None, None, None

    total = len(get_hist())
    base = n // 2

    # alternancia automática
    size_g1 = base if n % 2 == 0 else (base if total % 2 == 0 else base + 1)

    conteo = coincidencias()
    mejor = None
    mejor_score = 999999

    for _ in range(2000):
        random.shuffle(personas)
        g1 = personas[:size_g1]
        g2 = personas[size_g1:]

        score = 0
        for grupo in [g1, g2]:
            for a, b in combinations(grupo, 2):
                clave = tuple(sorted([a, b]))
                score += conteo.get(clave, 0)

        if score < mejor_score:
            mejor_score = score
            mejor = (g1[:], g2[:])

    if mejor:
        fecha = datetime.now().strftime('%d/%m/%Y')
        guardar(fecha, mejor[0], mejor[1])
        return fecha, mejor[0], mejor[1]

    return None, None, None

# -------- UI --------

st.title("🎲 Sorteo Pro")

# AÑADIR PERSONAS
st.subheader("👥 Personas")

if "nuevo" not in st.session_state:
    st.session_state.nuevo = ""

def agregar():
    nombre = st.session_state.nuevo.strip()
    if nombre != "":
        add_persona(nombre)
    st.session_state.nuevo = ""

st.text_input("Añadir persona", key="nuevo", on_change=agregar)

personas = get_personas()

for p in personas:
    col1, col2 = st.columns([4,1])
    col1.write(p)
    if col2.button("❌", key=p):
        delete_persona(p)
        st.rerun()

# SORTEO
st.divider()

if st.button("🎲 Generar sorteo"):
    fecha, g1, g2 = generar()

    if fecha:
        st.success(f"Sorteo: {fecha}")

        st.write("### Grupo 1")
        st.write(", ".join(g1))

        st.write("### Grupo 2")
        st.write(", ".join(g2))

# HISTORIAL
st.divider()
st.subheader("📜 Historial")

hist = get_hist()

for h in reversed(hist):
    st.write(f"**{h['fecha']}**")
    st.write("Grupo 1:", h["grupo1"])
    st.write("Grupo 2:", h["grupo2"])
    st.write("---")

if st.button("🗑️ Borrar historial"):
    borrar_hist()
    st.rerun()
   # =========================
# ESTADÍSTICAS
# =========================

st.markdown("---")
st.subheader("📊 Estadísticas")

historial_stats = (
    supabase.table("historial")
    .select("*")
    .execute()
)

conteo = {}

if historial_stats.data:

    for fila in historial_stats.data:

        g1 = fila["grupo1"].split(", ")
        g2 = fila["grupo2"].split(", ")

        for persona in g1:
            conteo[persona] = conteo.get(persona, 0) + 1

        for persona in g2:
            conteo[persona] = conteo.get(persona, 0) + 1

    ranking = sorted(
        conteo.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for nombre, veces in ranking:
        st.write(f"👤 {nombre}: {veces} sorteos")

else:
    st.info("Aún no hay estadísticas.")
    
