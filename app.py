import streamlit as st
import random
import sqlite3
from datetime import datetime
from itertools import combinations

# ---------- CONFIG ----------
st.set_page_config(page_title="Sorteo PRO", page_icon="🎲", layout="centered")

# ---------- ESTILOS ----------
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background:#f6f8fb; }
.main .block-container { max-width:760px; padding-top:1.2rem; }
h1 { text-align:center; font-weight:800; }

.stButton>button {
  width:100%; height:56px; border-radius:14px; font-size:18px; font-weight:700;
  background:linear-gradient(135deg,#4f46e5,#7c3aed); color:white; border:none;
}

.card {
  background:white; border-radius:16px; padding:16px; margin-bottom:12px;
  box-shadow:0 8px 22px rgba(0,0,0,0.06);
}

.card-title { font-weight:700; margin-bottom:8px; }

.chip {
  display:inline-block;
  padding:6px 10px;
  margin:4px;
  border-radius:999px;
  background:#eef2ff;
  color:#3730a3;
}
</style>
""", unsafe_allow_html=True)

# ---------- DB ----------
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS personas (nombre TEXT UNIQUE)")
c.execute("""
CREATE TABLE IF NOT EXISTS historial (
    fecha TEXT,
    grupo1 TEXT,
    grupo2 TEXT
)
""")
conn.commit()

# ---------- FUNCIONES ----------
def get_personas():
    c.execute("SELECT nombre FROM personas")
    return [x[0] for x in c.fetchall()]

def add_persona(nombre):
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

def generar(size_g1):
    personas = get_personas()
    n = len(personas)

    if n < 2 or size_g1 < 1 or size_g1 >= n:
        return None, None, None

    conteo = coincidencias()
    mejor = None
    mejor_score = float("inf")

    for _ in range(3000):
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
        guardar_historial(fecha, mejor[0], mejor[1])
        return fecha, mejor[0], mejor[1]

    return None, None, None

# ---------- UI ----------
st.title("🎲 Sorteo de grupos")

# PERSONAS
st.subheader("👥 Personas")

personas = get_personas()

if "nuevo_nombre" not in st.session_state:
    st.session_state.nuevo_nombre = ""

def añadir_persona():
    nombre = st.session_state.nuevo_nombre.strip()
    if nombre != "" and nombre not in personas:
        add_persona(nombre)
    st.session_state.nuevo_nombre = ""

st.text_input(
    "Añadir persona",
    key="nuevo_nombre",
    placeholder="Escribe un nombre y pulsa ENTER",
    on_change=añadir_persona
)

# LISTA
st.markdown('<div class="card"><div class="card-title">Lista</div>', unsafe_allow_html=True)

if personas:
    for p in personas:
        col1, col2 = st.columns([4,1])
        col1.write(p)
        if col2.button("❌", key=f"del_{p}"):
            delete_persona(p)
            st.rerun()
else:
    st.write("No hay personas")

st.markdown('</div>', unsafe_allow_html=True)

# CONFIG
st.subheader("⚙️ Tamaño de grupos")

n = len(personas)

if n >= 2:
    size_g1 = st.slider("Grupo 1", 1, n-1, n//2)
else:
    size_g1 = 1

# GENERAR
st.divider()

if st.button("🎲 Generar sorteo"):
    fecha, g1, g2 = generar(size_g1)

    if fecha:
        st.success(f"Sorteo: {fecha}")

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="card-title">Grupo 1 ({len(g1)})</div>', unsafe_allow_html=True)
        for p in g1:
            st.markdown(f'<span class="chip">{p}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="card-title">Grupo 2 ({len(g2)})</div>', unsafe_allow_html=True)
        for p in g2:
            st.markdown(f'<span class="chip">{p}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error("Configuración no válida")

# HISTORIAL
st.divider()
st.subheader("📜 Historial")

hist = get_historial()

if not hist:
    st.info("No hay historial")
else:
    for i, (fecha, g1, g2) in enumerate(reversed(hist)):
        st.markdown('<div class="card">', unsafe_allow_html=True)

        col1, col2 = st.columns([4,1])
        col1.write(f"**{fecha}**")
        col1.write("Grupo 1:", g1)
        col1.write("Grupo 2:", g2)

        if col2.button("❌", key=f"h_{i}"):
            c.execute(
                "DELETE FROM historial WHERE fecha=? AND grupo1=? AND grupo2=?",
                (fecha, g1, g2)
            )
            conn.commit()
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# BORRAR TODO
if st.button("🗑️ Borrar todo el historial"):
    c.execute("DELETE FROM historial")
    conn.commit()
    st.rerun()

# STATS
st.divider()
st.subheader("📊 Estadísticas")

stats = coincidencias()

st.markdown('<div class="card">', unsafe_allow_html=True)

if stats:
    for (a, b), n in sorted(stats.items(), key=lambda x: -x[1])[:10]:
        st.write(f"{a} - {b}: {n} veces")
else:
    st.write("Sin datos")

st.markdown('</div>', unsafe_allow_html=True)
