import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# --- 1. MODULAR IMPORTS & DATABASE ---
try:
    from crop_engine_data import get_agri_dataframe, recommend_crops
    from schemes_db import get_state_schemes, get_central_schemes
    from Locations import india_map
    from crop_master import all_crops
except ImportError as e:
    st.error(f"⚠️ Critical Module Missing: {e}")
    india_map = {"Bihar": ["Patna", "Gaya", "Muzaffarpur"]}
    all_crops = []

def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    # user_key ensures data privacy
    c.execute('''CREATE TABLE IF NOT EXISTS ledger 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_key TEXT,
                  date TEXT, type TEXT, item TEXT, qty TEXT, total REAL, season TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. CONFIGURATION & STYLING ---
st.set_page_config(page_title="ASES: Agri-Smart Ecosystem", layout="wide", page_icon="🌾")

st.markdown("""
<style>
    .main-card { padding: 20px; border-radius: 15px; background-color: rgba(46, 125, 50, 0.1); border: 1px solid #2e7d32; margin-bottom: 15px; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; background-color: #2e7d32; color: white; }
    [data-testid="stSidebar"] { background-color: #243139 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    .call-btn { background-color: #ffc107 !important; color: black !important; padding: 10px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 3. AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🌾 Agri-Smart Ecosystem (ASES)")
    t1, t2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"):
            conn = sqlite3.connect('agri_khata.db')
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
            if c.fetchone():
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else: st.error("Invalid credentials.")
            conn.close()
    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            try:
                conn = sqlite3.connect('agri_khata.db')
                c = conn.cursor()
                c.execute("INSERT INTO users VALUES (?,?)", (nu, np))
                conn.commit()
                st.success("Registration successful!")
                conn.close()
            except sqlite3.IntegrityError: st.error("Username already exists.")

# --- 4. MAIN DASHBOARD ---
else:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=100)
        st.subheader(f"Welcome, {st.session_state.username}")
        tab = st.radio("MENU", ["🏠 Home", "🎯 AgriAI Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📉 Price Trends", "📒 Agri Ledger"])
        
        state_list = sorted(list(india_map.keys()))
        s_state = st.selectbox("Current State", state_list)
        s_dist = st.selectbox("District", sorted(india_map.get(s_state, ["Patna"])))
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- TAB: HOME ---
    if tab == "🏠 Home":
        st.title(f"📍 Region: {s_dist}, {s_state}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Status", "Active")
        c2.metric("Soil", "Optimal")
        c3.metric("Center", "IIT Patna")

    # --- TAB: AGRIAI ENGINE (Fixed Logic) ---
    elif tab == "🎯 AgriAI Engine":
        st.title("🎯 Precision Crop Engine")
        df, le = get_agri_dataframe()
        col1, col2 = st.columns(2)
        with col1: soil = st.selectbox("Soil Type", ["Alluvial", "Black Soil", "Red Soil", "Sandy"])
        with col2: budget = st.slider("Investment Budget (₹/Acre)", 5000, 50000, 15000)
        
        if st.button("🚀 GET RECOMMENDATIONS"):
            recs = recommend_crops(df, le, soil, budget)
            if not recs.empty:
                for _, row in recs.iterrows():
                    st.markdown(f'<div class="main-card"><b>🌱 {row["Crop Name"]}</b><br>Estimated Cost: ₹{row["Cost per Acre"]}</div>', unsafe_allow_html=True)
            else: st.warning("Try increasing the budget for better matches.")

    # --- TAB: RENTAL HUB (Populated) ---
    elif tab == "🚜 Rental Hub":
        st.title(f"🚜 Machinery Rental Desk: {s_dist}")
        machine_types = {
            "Land Preparation": [("Rotavator", "🚜"), ("Power Tiller", "⚙️")],
            "Sowing/Planting": [("Seed Drill", "🌱"), ("Rice Transplanter", "🌾")],
            "Harvesting": [("Combine Harvester", "🌾✨"), ("Thresher", "🌪️")]
        }
        m_tabs = st.tabs(list(machine_types.keys()))
        for i, category in enumerate(machine_types.keys()):
            with m_tabs[i]:
                for m_name, m_icon in machine_types[category]:
                    with st.container():
                        st.markdown(f"### {m_icon} {m_name}")
                        st.link_button(f"🔍 Find Rental Centers in {s_dist}", f"https://www.google.com/search?q={m_name}+Rental+Service+in+{s_dist}")
                        st.markdown(f'<a href="tel:18001801551" class="call-btn">📞 Call Govt Helpline</a>', unsafe_allow_html=True)
                        st.divider()

    # --- TAB: KNOWLEDGE HUB (Detailed) ---
    elif tab == "📚 Knowledge Hub":
        st.title("📚 Crop Resource Library")
        search = st.text_input("🔍 Search Crop Name:", "").strip()
        filtered = [c for c in all_crops if search.lower() in c['Crop'].lower()] if search else all_crops
        
        for item in filtered:
            with st.expander(f"📖 {item['Crop']}"):
                st.write(f"**Season:** {item['Season']} | **NPK Requirement:** {item['N-P-K']}")
                st.info(f"💡 **Expert Tip:** {item['Pro-Tip']}")

    # --- TAB: GOVT SCHEMES ---
    elif tab == "🏛️ Govt Schemes":
        st.title("🏛️ Welfare Portal")
        state_schemes = get_state_schemes()
        s = state_schemes.get(s_state, {"name": "Regional Support", "desc": "Visit local Krishi Bhavan", "link": "#"})
        st.markdown(f'<div class="main-card"><h2>🌟 {s["name"]}</h2><p>{s["desc"]}</p><a href="{s["link"]}" target="_blank">🔗 Official Portal</a></div>', unsafe_allow_html=True)

    # --- TAB: PRICE TRENDS ---
    elif tab == "📉 Price Trends":
        st.title("📉 Market Price Analysis")
        crop_list = [c['Crop'] for c in all_crops] if all_crops else ["Wheat", "Rice"]
        c_name = st.selectbox("Choose Commodity", crop_list)
        months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
        prices = [2100, 2050, 2150, 2200, 2300, 2250, 2350, 2400, 2380, 2450, 2500, 2480]
        fig = px.line(x=months, y=prices, markers=True, title=f"12-Month Trend: {c_name}")
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB: AGRI LEDGER (Privacy Focused) ---
    elif tab == "📒 Agri Ledger":
        st.title("📒 Your Private Digital Ledger")
        conn = sqlite3.connect('agri_khata.db')
        # DATA PRIVACY: Only select records where user_key matches current session
        query = f"SELECT * FROM ledger WHERE user_key='{st.session_state.username}'"
        df_khata = pd.read_sql_query(query, conn)
        conn.close()

        if not df_khata.empty:
            inc = df_khata[df_khata['type'].str.contains('Income')]['total'].sum()
            exp = df_khata[df_khata['type'].str.contains('Expense')]['total'].sum()
            m1, m2, m3 = st.columns(3)
            m1.metric("Revenue", f"₹{inc:,.2f}")
            m2.metric("Investment", f"₹{exp:,.2f}")
            m3.metric("Net Profit", f"₹{inc - exp:,.2f}")
            st.dataframe(df_khata.drop(columns=['id', 'user_key']), use_container_width=True)
        else:
            st.info("No records found in your private ledger.")

        with st.expander("➕ Log New Transaction"):
            with st.form("ledger_form"):
                tp = st.selectbox("Category", ["Income (Sales)", "Expense (Seeds)", "Expense (Labor)"])
                itm = st.text_input("Item Name")
                val = st.number_input("Amount (₹)", min_value=0.0)
                season = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"])
                if st.form_submit_button("Save Entry"):
                    conn = sqlite3.connect('agri_khata.db')
                    c = conn.cursor()
                    dt = datetime.now().strftime("%Y-%m-%d")
                    c.execute("INSERT INTO ledger (user_key, date, type, item, qty, total, season) VALUES (?,?,?,?,?,?,?)",
                              (st.session_state.username, dt, tp, itm, "1", val, season))
                    conn.commit()
                    conn.close()
                    st.rerun()
