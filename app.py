import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# --- 1. CONFIGURATION & API KEYS ---
st.set_page_config(page_title="ASES: Agri-Smart", layout="wide", page_icon="🌾")
OGD_API_KEY = "579b464db66ec23bdd0000019b64f520463c4fba468cc24026c3cff6"
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"

# --- 2. MODULAR IMPORTS ---
try:
    from Locations import india_map
    from crop_master import all_crops
    from crop_engine_data import get_agri_dataframe, recommend_crops
    from schemes_db import get_state_schemes, get_central_schemes
except ImportError as e:
    st.error(f"⚠️ Critical Module Missing: {e}")
    india_map = {"Bihar": ["Patna", "Gaya", "Muzaffarpur"]}
    all_crops = []

# --- 3. DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ledger 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_key TEXT,
                  date TEXT, type TEXT, item TEXT, qty TEXT, total REAL, season TEXT)''')
    conn.commit()
    conn.close()

def delete_user_data(username):
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute("DELETE FROM ledger WHERE user_key = ?", (username,))
    conn.commit()
    conn.close()

init_db()

# --- 4. REAL-TIME DATA ENGINE ---
def get_live_mandi_prices(state, commodity):
    url = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
    params = {
        "api-key": OGD_API_KEY,
        "format": "json",
        "filters[state]": state,
        "filters[commodity]": commodity,
        "limit": 10
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "records" in data and len(data["records"]) > 0:
            return pd.DataFrame(data["records"])
        return None
    except:
        return None

# --- 5. STYLING ---
st.markdown("""
<style>
    .main-card { padding: 20px; border-radius: 15px; background-color: rgba(46, 125, 50, 0.1); border: 1px solid #2e7d32; margin-bottom: 15px; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; height: 3em; background-color: #2e7d32; color: white; }
</style>
""", unsafe_allow_html=True)

# --- 6. AUTHENTICATION ---
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

# --- 7. MAIN DASHBOARD ---
else:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=100)
        st.subheader(f"Welcome, {st.session_state.username}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        tab = st.radio("MENU", ["🏠 Home", "🎯 Crop AI", "📈 Market Trends", "📒 Agri Ledger"])
        
        state_list = sorted(list(india_map.keys()))
        s_state = st.selectbox("Current State", state_list)
        s_dist = st.selectbox("District", sorted(india_map.get(s_state, ["Patna"])))

    # --- TAB 1: HOME ---
    if tab == "🏠 Home":
        st.title(f"📍 Region: {s_dist}, {s_state}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Current Status", "Active")
        c2.metric("Soil Health", "Optimal")
        c3.metric("Project", "IITP-ASES")
        st.info("💡 Pro Tip: Check the 'Market Trends' tab for real-time Mandi prices before selling.")

    # --- TAB 2: CROP AI (Correct API Usage) ---
    elif tab == "🎯 Crop AI":
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
            else: st.warning("No crops found for this budget. Try increasing the limit.")

    # --- TAB 3: MARKET TRENDS (Real-time API & 12 Months) ---
    elif tab == "📈 Market Trends":
        st.title("📈 Market Price Analysis")
        crop_list = [c['Crop'] for c in all_crops] if all_crops else ["Wheat", "Rice", "Maize"]
        c_name = st.selectbox("Choose Commodity", crop_list)
        
        # Real-time Fetch
        with st.spinner("Fetching Live Mandi Prices..."):
            live_data = get_live_mandi_prices(s_state, c_name)
        
        if live_data is not None:
            st.success(f"Live Data for {c_name} in {s_state}")
            latest = live_data.iloc[0]
            st.metric(f"Current Price ({latest['market']})", f"₹{latest['modal_price']} / Quintal")
            
            live_data['modal_price'] = pd.to_numeric(live_data['modal_price'])
            fig_bar = px.bar(live_data, x='market', y='modal_price', title="Price Variation by Mandi", color_discrete_sequence=['#2e7d32'])
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("Live data currently unavailable for this selection. Showing historical cycles.")

        # Full 12-Month Trend Cycle
        st.markdown("---")
        st.subheader("📅 12-Month Price Cycle Forecast")
        months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
        prices = [1900, 1850, 2000, 2100, 2150, 2050, 2100, 2250, 2180, 2300, 2450, 2400]
        fig_line = px.line(x=months, y=prices, markers=True, title=f"Annual Trend: {c_name}", labels={'x':'Month', 'y':'Price (₹)'})
        fig_line.update_traces(line_color='#2e7d32')
        st.plotly_chart(fig_line, use_container_width=True)

    # --- TAB 4: AGRI LEDGER ---
    elif tab == "📒 Agri Ledger":
        st.title("📒 Digital Agri Ledger")
        if st.button("🗑️ Reset Ledger Data", type="primary"):
            delete_user_data(st.session_state.username)
            st.rerun()

        conn = sqlite3.connect('agri_khata.db')
        df_khata = pd.read_sql_query(f"SELECT * FROM ledger WHERE user_key='{st.session_state.username}'", conn)
        conn.close()

        if not df_khata.empty:
            inc = df_khata[df_khata['type'].str.contains('Income')]['total'].sum()
            exp = df_khata[df_khata['type'].str.contains('Expense')]['total'].sum()
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Revenue", f"₹{inc:,.2f}")
            m2.metric("Total Investment", f"₹{exp:,.2f}")
            m3.metric("Net Profit", f"₹{inc - exp:,.2f}")
            st.dataframe(df_khata.drop(columns=['id', 'user_key']), use_container_width=True)

        with st.expander("➕ Log New Transaction"):
            with st.form("ledger_form"):
                tp = st.selectbox("Category", ["Income (Sales)", "Expense (Seeds)", "Expense (Labor)", "Expense (Machinery)"])
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
                    
