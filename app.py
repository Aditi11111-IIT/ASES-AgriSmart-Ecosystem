import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# --- 1. MODULAR IMPORTS (CLEAN & ORGANIZED) ---
from crop_engine_data import get_agri_dataframe, recommend_crops
from schemes_db import get_state_schemes, get_central_schemes
try:
    from Locations import india_map
    from crop_master import all_crops
except ImportError:
    india_map = {"Bihar": ["Patna", "Bihta"]}
    all_crops = []

# --- 2. DATABASE LOGIC (MULTI-USER & MIGRATION) ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    # Ledger Table
    c.execute('''CREATE TABLE IF NOT EXISTS ledger 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_key TEXT,
                  date TEXT, type TEXT, item TEXT, qty TEXT, total REAL, season TEXT)''')
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    
    # Check for legacy table migration
    try:
        c.execute("SELECT user_key FROM ledger LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE ledger ADD COLUMN user_key TEXT DEFAULT 'Guest_0000'")
    conn.commit()
    conn.close()

def delete_user_data(user_key):
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute("DELETE FROM ledger WHERE user_key = ?", (user_key,))
    conn.commit()
    conn.close()

init_db()

# --- 3. UI/UX THEME (ADAPTIVE LIGHT/DARK MODE) ---
st.set_page_config(page_title="ASES: Agri-Smart", layout="wide", page_icon="🌾")

st.markdown("""
<style>
    /* Professional Card Containers */
    .stApp { background-attachment: fixed; }
    .agri-card {
        padding: 20px;
        border-radius: 15px;
        background-color: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(46, 125, 50, 0.3);
        margin-bottom: 20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    /* Buttons */
    .stButton>button {
        border-radius: 12px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    /* Custom Green Metric */
    [data-testid="stMetricValue"] { color: #2e7d32 !important; }
    
    /* Login Page Styling */
    .login-container {
        max-width: 400px;
        margin: auto;
        padding: 30px;
        border-radius: 20px;
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIN & SIGNUP UI ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🌾 ASES: Agri-Smart Ecosystem")
    st.caption("IIT Patna CSDA Capstone Project")
    
    tab_l, tab_s = st.tabs(["Login", "Sign Up"])
    
    with tab_l:
        with st.container():
            l_user = st.text_input("Username", placeholder="Enter name")
            l_pass = st.text_input("Password", type="password")
            if st.button("Sign In", use_container_width=True):
                conn = sqlite3.connect('agri_khata.db')
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (l_user, l_pass))
                if c.fetchone():
                    st.session_state.logged_in = True
                    st.session_state.username = l_user
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
                conn.close()

    with tab_s:
        s_user = st.text_input("Choose Username", key="new_user")
        s_pass = st.text_input("Create Password", type="password", key="new_pass")
        if st.button("Create Account", use_container_width=True):
            try:
                conn = sqlite3.connect('agri_khata.db')
                c = conn.cursor()
                c.execute("INSERT INTO users VALUES (?,?)", (s_user, s_pass))
                conn.commit()
                st.success("Registration Successful! Please login.")
                conn.close()
            except sqlite3.IntegrityError:
                st.error("This username is already taken.")

# --- 5. MAIN APP UI (POST-LOGIN) ---
else:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
        st.subheader(f"👋 Namaste, {st.session_state.username}")
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()
        
        st.markdown("---")
        tab = st.radio("MAIN NAVIGATION", ["🏠 Dashboard", "🌾 AgriAI Engine", "🚜 Rental Hub", "📉 Price Trends", "📒 Agri Khata"])
        
        st_loc = st.selectbox("Your State", sorted(india_map.keys()))
        dt_loc = st.selectbox("Your District", sorted(india_map.get(st_loc, ["Patna"])))

    # --- TAB: DASHBOARD ---
    if tab == "🏠 Dashboard":
        st.title(f"🚀 Command Center: {dt_loc}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Current Temp", "24°C", "2°")
        col2.metric("Humidity", "62%")
        col3.metric("Rain Chance", "10%")
        
        st.markdown(f"""
        <div class="agri-card">
            <h3>Farmer Profile: {st.session_state.username}</h3>
            <p>Welcome to the ASES platform. Your data is synced with <b>{st_loc}</b> regional Mandis.</p>
        </div>
        """, unsafe_allow_html=True)

    # --- TAB: AGRI-AI ENGINE ---
    elif tab == "🌾 AgriAI Engine":
        st.title("🌾 AgriAI Smart Advisor")
        df, le = get_agri_dataframe()
        soil = st.selectbox("Select Soil Type", ["Alluvial", "Black Soil", "Red Soil", "Sandy"])
        budget = st.slider("Investment Budget (₹)", 5000, 50000, 15000)
        
        if st.button("🚀 GET RECOMMENDATION", use_container_width=True):
            recs = recommend_crops(df, le, soil, budget)
            for _, row in recs.iterrows():
                st.markdown(f"""
                <div class="agri-card">
                    <h4>{row['Crop Name']}</h4>
                    <p>Estimated Cost: ₹{row['Cost per Acre']} | Recommended for {soil}</p>
                </div>
                """, unsafe_allow_html=True)

    # --- TAB: PRICE TRENDS ---
    elif tab == "📉 Price Trends":
        st.title("📈 Market Price Trends")
        if all_crops:
            crop_sel = st.selectbox("Select Crop", [c['Crop'] for c in all_crops])
            # Original price logic
            prices = [2100, 2250, 2180, 2300, 2450, 2400]
            fig = px.line(pd.DataFrame({"Month": ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"], "Price": prices}), 
                          x="Month", y="Price", markers=True, line_shape="spline", title=f"Trends for {crop_sel}")
            fig.update_traces(line_color='#2e7d32')
            st.plotly_chart(fig, use_container_width=True)

    # --- TAB: AGRI KHATA (SECURE LEDGER) ---
    elif tab == "📒 Agri Khata":
        st.title("📒 Digital Seasonal Ledger")
        
        # CLEAR DATA BUTTON AT THE TOP
        c_clear = st.columns([4, 1])
        with c_clear[1]:
            if st.button("🗑️ Clear My Data", type="primary", use_container_width=True):
                delete_user_data(st.session_state.username)
                st.toast("Database Cleared!")
                st.rerun()

        st.markdown("---")
        conn = sqlite3.connect('agri_khata.db')
        df_ledger = pd.read_sql_query(f"SELECT * FROM ledger WHERE user_key = '{st.session_state.username}'", conn)
        conn.close()

        if not df_ledger.empty:
            income = df_ledger[df_ledger['type'].str.contains('Income')]['total'].sum()
            expense = df_ledger[df_ledger['type'].str.contains('Expense')]['total'].sum()
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Revenue", f"₹{income:,.2f}")
            m2.metric("Investment", f"₹{expense:,.2f}")
            m3.metric("Net Profit", f"₹{income - expense:,.2f}")
            st.dataframe(df_ledger.drop(columns=['id', 'user_key']), use_container_width=True)
        else:
            st.info("No records found. Use the form below to start your ledger.")

        with st.expander("➕ Add Transaction"):
            with st.form("ledger_form"):
                t = st.selectbox("Transaction Type", ["Income (Sales)", "Expense (Seeds/Fertilizer)", "Expense (Labor)"])
                item = st.text_input("Item Name")
                amt = st.number_input("Amount (₹)", min_value=0)
                szn = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"])
                if st.form_submit_button("Save to Ledger"):
                    conn = sqlite3.connect('agri_khata.db')
                    c = conn.cursor()
                    dt = datetime.now().strftime("%Y-%m-%d")
                    c.execute("INSERT INTO ledger (user_key, date, type, item, qty, total, season) VALUES (?,?,?,?,?,?,?)",
                              (st.session_state.username, dt, t, item, "1", amt, szn))
                    conn.commit()
                    conn.close()
                    st.rerun()
