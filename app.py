import streamlit as st
import random
import sqlite3
from datetime import datetime
from itertools import combinations

# ---------- CONFIG ----------
st.set_page_config(page_title="Sorteo PRO+", page_icon="🎲", layout="centered")

# ---------- ESTILOS (premium) ----------
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background:#f6f8fb; }
.main .block-container { max-width:760px; padding-top:1.2rem; }
h1 { text-align:center; font-weight:800; letter-spacing:.2px; }

.stButton>button {
  width:100%; height:56px; border-radius:14px; font-size:18px; font-weight:700;
  background:linear-gradient(135deg,#4f46e5,#7c3aed); color:#fff; border:none;
}
.stButton>button:hover { filter:brightness(1.06); }

.card {
  background:#fff; border-radius:16px; padding:16px; margin-bottom:12px;
  box-shadow:0 8px 22px rgba(0,0,0,.06);
}
.card-title { font-weight:800; margin-bottom:8px; }

.chip {
  display:inline-block; padding:6px 10px; margin:4px 6px 0 0;
  border-radius:999px; background:#eef2ff; color:#3730a3; font-weight:600; font-size:13px;
}

hr { border:none; height:1px; background:#e5e7eb; margin:1rem 0; }
.small { color:#6b7280; font-size:12px; }
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
    if nombre.strip() == "":
        return
    try:
        c.execute("INSERT INTO personas VALUES (?)", (nombre.strip(),))
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
    """Cuenta cuántas veces han coincidido las parejas en el historial."""
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
    """Genera grupos con tamaño flexible y equilibrio de parejas."""
    personas = get_personas()
    n = len(personas)

    # Necesitamos al menos 2 personas y que el tamaño tenga sentido
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
        fecha = datetime.now().strftime('%Y-%m-%d')
        guardar_historial(fecha, mejor[0], mejor[1])
        return fecha, mejor[0], mejor[1]

    return None, None, None

# ---------- UI ----------
st.title("🎲 Sorteo de grupos PRO+")

# ----- PERSONAS -----
st.subheader("👥 Personas")
personas = get_personas()

col1, col2 = st.columns([3,1])
with col1:
    nueva = st.text_input("Añadir persona", placeholder="Escribe un nombre…")
with col2:
    if st.button("➕ Añadir"):
        add_persona(nueva)
        st.rerun()

st.markdown('<div class="card"><div class="card-title">Lista</div>', unsafe_allow_html=True)
if personas:
    for p in personas:
        c1, c2 = st.columns([4,1])
        c1.markdown(f"• {p}")
        if c2.button("❌", key=f"del_person_{p}"):
            delete_persona(p)
            st.rerun()
else:
    st.write("Aún no hay personas")
st.markdown('</div>', unsafe_allow_html=True)

# ----- CONFIGURACIÓN DE GRUPOS -----
st.subheader("⚙️ Configuración de grupos")

n = len(personas)
hist = get_historial()
total = len(hist)

modo = st.radio(
    "Modo de tamaño",
    ["Automático (equilibrado)", "Elegir tamaño del Grupo 1"],
    horizontal=True
)

if n >= 2:
    if modo == "Automático (equilibrado)":
        # Reparte lo más equilibrado posible
        base = n // 2
        # Alterna quién es el grupo grande
        if n % 2 == 0:
            size_g1 = base
        else:
            size_g1 = base if (total % 2 == 0) else base + 1

        st.markdown(
            f'<div class="card small">Se generará automáticamente: '
            f'Grupo 1 = {size_g1} | Grupo 2 = {n - size_g1}</div>',
            unsafe_allow_html=True
        )
    else:
        size_g1 = st.slider(
            "Tamaño del Grupo 1",
            min_value=1,
            max_value=max(1, n-1),
            value=min(max(1, n//2), n-1)
        )
else:
    size_g1 = 1

# ----- GENERAR -----
st.divider()
if st.button("🎲 Generar sorteo"):
    fecha, g1, g2 = generar(size_g1)

    if fecha:
        st.success(f"Sorteo: {fecha}")

        # Grupo 1
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="card-title">Grupo 1 ({len(g1)})</div>', unsafe_allow_html=True)
        for p in g1:
            st.markdown(f'<span class="chip">✅ {p}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Grupo 2
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="card-title">Grupo 2 ({len(g2)})</div>', unsafe_allow_html=True)
        for p in g2:
            st.markdown(f'<span class="chip">🔹 {p}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error("Configuración no válida")

# ----- HISTORIAL -----
st.divider()
st.subheader("📜 Historial")

hist = get_historial()

if not hist:
    st.info("No hay historial aún")
else:
    for i, (fecha, g1, g2) in enumerate(reversed(hist)):
        st.markdown('<div class="card">', unsafe_allow_html=True)

        col1, col2 = st.columns([4,1])
        with col1:
            st.markdown(f"<b>{fecha}</b>", unsafe_allow_html=True)
            st.markdown(f"<div>Grupo 1: {g1}</div>", unsafe_allow_html=True)
            st.markdown(f"<div>Grupo 2: {g2}</div>", unsafe_allow_html=True)

        with col2:
            if st.button("❌", key=f"del_hist_{i}"):
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
    st.success("Historial borrado")
    st.rerun()

# ----- ESTADÍSTICAS -----
st.divider()
st.subheader("📊 Estadísticas")

stats = coincidencias()

st.markdown('<div class="card">', unsafe_allow_html=True)
if stats:
    for (a, b), n in sorted(stats.items(), key=lambda x: -x[1])[:10]:
        st.write(f"{a} - {b}: {n} veces")
else:
    st.write("Sin datos aún")
st.markdown('</div>', unsafe_allow_html=True)
