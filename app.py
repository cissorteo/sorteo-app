import streamlit as st
import random
import sqlite3
from datetime import datetime
from itertools import combinations

# ---------- CONFIG ----------
st.set_page_config(page_title="Sorteo DIOS", page_icon="🎲")

conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

# ---------- DB ----------
c.execute("CREATE TABLE IF NOT EXISTS personas (nombre TEXT UNIQUE)")
c.execute("""CREATE TABLE IF NOT EXISTS historial (
       fecha TEXT,
       grupo1 TEXT,
       grupo2 TEXT
)""")
conn.commit()

# ---------- FUNCIONES ----------
def get_personas():
    c.execute("SELECT nombre FROM personas")
    return [x[0] for x in c.fetchall()]

def add_persona(nombre):
    if nombre.strip() == "":
        return
    try:
        c.execute("INSERT INTO personas VALUES (?)", (nombre,))
        conn.commit()
    except:
        pass

def delete_persona(nombre):
    c.execute("DELETE FROM personas WHERE nombre=?", (nombre,))
    conn.commit()

def get_historial():
    c.execute("SELECT * FROM historial")
    return c.fetchall()

def guardar_historial(fecha, g1, g2):
    c.execute(
        "INSERT INTO historial VALUES (?, ?, ?)",
        (fecha, ",".join(g1), ",".join(g2))
    )
    conn.commit()

def coincidencias():
    hist = get_historial()
    conteo = {}

    for _, g1, g2 in hist:
        grupos = [g1.split(","), g2.split(",")]
        for grupo in grupos:
            for a, b in combinations(grupo, 2):
                clave = tuple(sorted([a, b]))
                conteo[clave] = conteo.get(clave, 0) + 1

    return conteo

def generar():
    personas = get_personas()

    if len(personas) != 7:
        return None, None, None
    conteo = coincidencias()
    mejor = None
    mejor_score = float("inf")

    for _ in range(3000):
        random.shuffle(personas)
        g1 = personas[:3]
        g2 = personas[3:]

        score = 0

        for grupo in [g1, g2]:
            for a, b in combinations(grupo, 2):
                clave = tuple(sorted([a, b]))
                score += conteo.get(clave, 0)

        if score < mejor_score:
            mejor_score = score
            mejor = (g1[:], g2[:])

    if mejor:
        fecha = datetime.now().strftime('%Y-%m-%d')
        guardar_historial(fecha, mejor[0], mejor[1])
        return fecha, mejor[0], mejor[1]

    return None, None, None

# ---------- UI ----------
st.title("🎲 Sorteo Turnos de Desayuno")

# PERSONAS
st.subheader("👥 Personas")

personas = get_personas()

col1, col2 = st.columns([2,1])

with col1:
    nueva = st.text_input("Añadir persona")
with col2:
    if st.button("➕ Añadir"):
        add_persona(nueva)
        st.rerun()

for p in personas:
    col1, col2 = st.columns([3,1])
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
        st.write("**Grupo 1:**", g1)
        st.write("**Grupo 2:**", g2)
    else:
        st.error("Necesitas exactamente 7 personas")

# HISTORIAL
st.divider()
st.subheader("📜 Historial")

hist = get_historial()

if not hist:
    st.info("No hay historial aún")
else:
for i, (fecha, g1, g2) in enumerate(reversed(hist)):
    col1, col2 = st.columns([4,1])

with col1:
    st.write(f"**{fecha}**")
    st.write("Grupo 1:", g1)
    st.write("Grupo 2:", g2)

with col2:
    if st.button("❌", key=f"del_{i}"):
        c.execute("DELETE FROM historial WHERE fecha=? AND grupo1=? AND grupo2=?", (fecha, g1, g2))
        conn.commit()
        st.rerun()

st.write("---")

# ESTADÍSTICAS
st.divider()
st.subheader("📊 Estadísticas")

stats = coincidencias()

for (a, b), n in sorted(stats.items(), key=lambda x: -x[1])[:10]:
    st.write(f"{a} - {b}: {n} veces")
