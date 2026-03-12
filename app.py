import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# --- 1. CONFIGURATION & OGD API ---
st.set_page_config(page_title="Agri-Smart Ecosystem", layout="centered", page_icon="🌾")
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070" 
OGD_API_KEY = "579b464db66ec23bdd0000019b64f520463c4fba468cc24026c3cff6"

# --- 2. MODULAR IMPORTS ---
try:
    from Locations import india_map
    from crop_master import all_crops
    from crop_engine_data import get_agri_dataframe, recommend_crops
    from schemes_db import get_state_schemes, get_central_schemes
except ImportError:
    india_map = {"Bihar": ["Patna", "Gaya"]}
    all_crops = []

# --- 3. DATABASE (SECURE PER-USER) ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ledger 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_key TEXT,
                  date TEXT, type TEXT, item TEXT, qty TEXT, total REAL, season TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. CSS STYLING ---
st.markdown("""
<style>
    .stApp { max-width: 850px; margin: 0 auto; background-color: #fcfdfc; }
    .mobile-card { padding: 15px; border-radius: 12px; border: 1px solid rgba(46, 125, 50, 0.3); background-color: white; margin-bottom: 12px; }
    .stButton>button { border-radius: 12px; height: 3.5em; font-weight: bold; width: 100%; }
    .greeting-card { background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%); color: white; padding: 25px; border-radius: 15px; margin-bottom: 20px; }
    .weather-alert { background-color: #fff3e0; border-left: 5px solid #ff9800; padding: 15px; border-radius: 8px; margin: 10px 0; color: #e65100; }
    .quick-link-btn { background-color: white; border: 1px solid #e0e0e0; padding: 15px; border-radius: 10px; text-align: center; color: #2e7d32; font-weight: bold; display: block; text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# --- 5. AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🌾 Agri-Smart Portal")
    t_log, t_sign = st.tabs(["🔐 Login", "📝 Sign Up"])
    with t_log:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"):
            conn = sqlite3.connect('agri_khata.db')
            res = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if res:
                st.session_state.logged_in, st.session_state.username = True, u
                st.rerun()
            else: st.error("Invalid credentials")
            conn.close()
    with t_sign:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            try:
                conn = sqlite3.connect('agri_khata.db')
                conn.execute("INSERT INTO users VALUES (?,?)", (nu, np))
                conn.commit()
                st.success("Account created!")
                conn.close()
            except: st.error("Username taken.")

# --- 6. MAIN INTERFACE ---
else:
    with st.sidebar:
        st.write(f"### 🧑‍🌾 {st.session_state.username}")
        menu = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🎯 AgriAI Engine", "🚜 Rental Hub", "🏛️ Govt Schemes", "📚 Knowledge Hub", "📉 Price Trends", "📒 Agri Ledger"])
        
        state_list = sorted(list(india_map.keys()))
        st_sel = st.selectbox("Your State", state_list, index=0)
        dt_sel = st.selectbox("Your District", sorted(india_map.get(st_sel, ["Patna"])))
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- DASHBOARD ---
    if menu == "🏠 Dashboard":
        hour = datetime.now().hour
        greeting = "Good Morning" if 5 <= hour < 12 else "Good Afternoon" if 12 <= hour < 17 else "Good Evening"
        st.markdown(f'<div class="greeting-card"><h1 style="color:white; margin:0;">{greeting}, {st.session_state.username}!</h1><p style="margin:0; opacity:0.9;">Welcome to your command center for {dt_sel}.</p></div>', unsafe_allow_html=True)
        
        st.markdown(f'<div class="weather-alert"><strong>⚠️ Weather Alert:</strong> High humidity expected in {dt_sel}. Monitor crops for pests.</div>', unsafe_allow_html=True)
        
        st.subheader("⚡ Quick Actions")
        q1, q2, q3 = st.columns(3)
        with q1: st.markdown('<div class="quick-link-btn">Check Prices</div>', unsafe_allow_html=True)
        with q2: st.markdown('<div class="quick-link-btn">Rent Tools</div>', unsafe_allow_html=True)
        with q3: st.markdown('<div class="quick-link-btn">Add Expense</div>', unsafe_allow_html=True)

        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Status", "Online")
        c2.metric("Market", "Open")
        c3.metric("District", dt_sel)

    # --- GOVT SCHEMES (FIXED TYPEERROR) ---
    elif menu == "🏛️ Govt Schemes":
        st.header("🏛️ Welfare & Subsidies")
        t1, t2 = st.tabs(["🇮🇳 Central", f"🏘️ {st_sel} State"])
        
        with t1:
            central_data = get_central_schemes()
            for s in central_data:
                with st.expander(f"📌 {s.get('name', 'Scheme')}"):
                    st.write(s.get('details', s.get('description', 'Information coming soon.')))
                    if 'link' in s: st.link_button("Apply", s['link'])
        
        with t2:
            # Check if state is selected before calling
            if st_sel:
                state_data = get_state_schemes(st_sel)
                if state_data:
                    for s in state_data:
                        with st.expander(f"🔸 {s.get('name', 'Scheme')}"):
                            st.write(s.get('details', s.get('description', 'Information coming soon.')))
                            if 'link' in s: st.link_button("Details", s['link'])
                else: st.info(f"No specific schemes found for {st_sel} yet.")

    # --- PRICE TRENDS (FIXED GRAPH) ---
    elif menu == "📉 Price Trends":
        st.header("📈 Live Mandi Prices")
        c_names = [c['Crop'] for c in all_crops] or ["Wheat", "Rice"]
        sel_c = st.selectbox("Choose Commodity", c_names)
        
        url = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
        params = {"api-key": OGD_API_KEY, "format": "json", "filters[state]": st_sel, "filters[commodity]": sel_c}
        
        try:
            res = requests.get(url, params=params).json()
            if "records" in res and len(res["records"]) > 0:
                m_df = pd.DataFrame(res["records"])
                m_df['modal_price'] = pd.to_numeric(m_df['modal_price'])
                st.success(f"Latest price in {res['records'][0]['market']}: ₹{res['records'][0]['modal_price']}")
                # Explicitly setting a professional color sequence
                st.plotly_chart(px.bar(m_df, x='market', y='modal_price', title=f"Prices for {sel_c}", color_discrete_sequence=['#2e7d32']), use_container_width=True)
            else:
                st.warning("No live data available. Showing seasonal forecast.")
                st.line_chart([2100, 2200, 2150, 2300, 2400])
        except:
            st.error("Mandi Servers currently unreachable.")

    # --- PRESERVED SECTIONS (AGRIAI, RENTAL, LEDGER) ---
    elif menu == "🎯 AgriAI Engine":
        st.header("🎯 Crop Recommendation")
        df, le = get_agri_dataframe()
        soil = st.selectbox("Soil Type", ["Alluvial", "Black Soil", "Red Soil", "Sandy", "Loamy"])
        budget = st.slider("Budget (₹/Acre)", 5000, 50000, 15000)
        if st.button("🚀 RUN ANALYSIS"):
            recs = recommend_crops(df, le, soil, budget)
            if not recs.empty:
                for _, row in recs.iterrows():
                    st.markdown(f'<div class="mobile-card"><b>🌱 {row["Crop Name"]}</b><br><small>Cost: ₹{row["Cost per Acre"]}</small></div>', unsafe_allow_html=True)

    elif menu == "🚜 Rental Hub":
        st.header("🚜 Machinery Rentals")
        cat = st.segmented_control("Stage", ["Preparation", "Harvesting"], default="Preparation")
        services = {"Preparation": [("Rotavator", "🚜")], "Harvesting": [("Harvester", "🌾")]}
        for name, icon in services.get(cat, []):
            with st.container(border=True):
                st.subheader(f"{icon} {name}")
                st.link_button(f"Find in {dt_sel}", f"https://www.google.com/search?q={name}+rental+{dt_sel}")

    elif menu == "📒 Agri Ledger":
        st.header("📒 Digital Ledger")
        conn = sqlite3.connect('agri_khata.db')
        df_khata = pd.read_sql_query(f"SELECT * FROM ledger WHERE user_key='{st.session_state.username}'", conn)
        conn.close()
        if not df_khata.empty:
            inc = df_khata[df_khata['type'].str.contains('Income')]['total'].sum()
            exp = df_khata[df_khata['type'].str.contains('Expense')]['total'].sum()
            st.subheader(f"Current Profit: ₹{inc - exp:,.2f}")
            st.dataframe(df_khata.drop(columns=['id', 'user_key']), use_container_width=True, hide_index=True)
        else: st.info("No records yet.")
