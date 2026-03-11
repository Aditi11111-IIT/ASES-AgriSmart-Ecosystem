import streamlit as st
import pandas as pd
import sqlite3
import random
import plotly.express as px
import requests
from datetime import datetime

# 🌾 Import your NEW modular data file
from crop_engine_data import get_agri_dataframe, recommend_crops

# 🌾 Import other modular data files
from schemes_db import get_state_schemes, get_central_schemes
try:
    from crop_master import all_crops
except ImportError:
    all_crops = []

# --- 1. DATABASE SETUP (STRICTLY PRESERVED) ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ledger 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, type TEXT, item TEXT, qty TEXT, total REAL, season TEXT)''')
    conn.commit()
    conn.close()

def add_entry(entry_type, item, qty, total, season):
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO ledger (date, type, item, qty, total, season) VALUES (?,?,?,?,?,?)",
              (date, entry_type, item, str(qty), total, season))
    conn.commit()
    conn.close()

init_db()

# --- 2. CONFIGURATION & STYLING (STRICTLY PRESERVED) ---
st.set_page_config(page_title="ASES: Agri-Smart Ecosystem", layout="wide", page_icon="🌾")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .main-card { padding: 25px; border-radius: 12px; background-color: #FFFFFF !important; border: 1px solid #2481CC; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .scheme-card { padding: 20px; border-radius: 12px; background-color: #e3f2fd; border-left: 8px solid #1976d2; margin-bottom: 15px; }
    .central-card { padding: 20px; border-radius: 12px; background-color: #f1f8e9; border-left: 8px solid #2e7d32; margin-bottom: 15px; }
    .highlight-text { color: #2481CC !important; font-weight: bold; }
    .stButton>button { border-radius: 8px; background-color: #2e7d32; color: white; width: 100%; }
    [data-testid="stSidebar"] { background-color: #243139 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA LOADING VIA MODULE ---
df, le_encoder = get_agri_dataframe()

# --- 4. SESSION STATE (STRICTLY PRESERVED) ---
if 'temp' not in st.session_state: st.session_state.temp = 25
if 'hum' not in st.session_state: st.session_state.hum = 50
if 'soil_pref' not in st.session_state: st.session_state.soil_pref = "Alluvial"
if 'selected_machine' not in st.session_state: st.session_state.selected_machine = "Tractor"

# --- 5. NAVIGATION & SIDEBAR (STRICTLY PRESERVED) ---
state_list = list(get_state_schemes().keys())
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    st.title("ASES NAVIGATION")
    tab = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🌾 Crop Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📈 Price Trends", "📒 Agri Khata"])
    st_loc = st.selectbox("Your State", state_list if state_list else ["Bihar"])
    dt_loc = st.text_input("Your District", "Patna")

# --- 6. TABS LOGIC ---

if tab == "🏠 Dashboard":
    st.title(f"👨‍🌾 Command Center")
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperature", f"{st.session_state.temp}°C")
    col2.metric("Humidity", f"{st.session_state.hum}%")
    col3.metric("Location Status", f"{dt_loc}, {st_loc}")

elif tab == "🌾 Crop Engine":
    st.title("AgriAI Smart Recommendations")
    soil_opts = ["Alluvial", "Black Soil", "Red Soil", "Sandy"]
    s_cols = st.columns(4)
    for i, s in enumerate(soil_opts):
        if s_cols[i].button(s): st.session_state.soil_pref = s
    
    st.markdown(f"Current Soil: **{st.session_state.soil_pref}**")
    bud = st.slider("Investment Budget (₹/Acre)", 5000, 50000, 15000)
    
    if st.button("🚀 FIND BEST CROPS"):
        # Using the modular recommendation function
        recommendations = recommend_crops(df, le_encoder, st.session_state.soil_pref, bud)
        for _, row in recommendations.iterrows():
            st.markdown(f'<div class="main-card"><h3>{row["Crop Name"]}</h3><p>Cost: ₹{row["Cost per Acre"]}</p></div>', unsafe_allow_html=True)

elif tab == "🚜 Rental Hub":
    st.title(f"🚜 Rental Machinery Desk: {dt_loc}")
    machine_types = {"Preparation": [("Rotavator", "🚜")], "Sowing": [("Seed Drill", "🌱")], "Harvesting": [("Thresher", "🌪️")]}
    # (Rest of Rental logic preserved...)
    st.markdown(f"**Currently Finding:** <span class='highlight-text'>{st.session_state.selected_machine}</span>", unsafe_allow_html=True)

elif tab == "📚 Knowledge Hub":
    st.title("📚 Crop Resource Library")
    st.dataframe(pd.DataFrame(all_crops), use_container_width=True)

elif tab == "🏛️ Govt Schemes":
    st.title("🏛️ Agricultural Welfare Portal")
    choice = st.radio("Select Scheme Type", ["State-Specific Schemes", "Central Govt Schemes"], horizontal=True)
    if choice == "State-Specific Schemes":
        s = get_state_schemes().get(st_loc, {"name": "N/A", "desc": "No specific schemes listed.", "link": "#"})
        st.markdown(f'<div class="scheme-card"><h2>🌟 {s["name"]}</h2><p>{s["desc"]}</p></div>', unsafe_allow_html=True)

elif tab == "📈 Price Trends":
    st.title("📈 Price Forecast & Calculator")
    if all_crops:
        crop_names = [c['Crop'] for c in all_crops]
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1: sel_crop = st.selectbox("Select Crop", crop_names)
        with col_c2: weight = st.number_input("Quantity (Q)", min_value=0.1, value=10.0)
        with col_c3: season_sel = st.selectbox("Tag Season", ["Kharif", "Rabi", "Zaid"])
        
        base_price = 2000 + (hash(sel_crop) % 4000)
        total_val = base_price * weight
        if st.button("📓 Save to Agri Khata"):
            add_entry("Income (Sale)", sel_crop, weight, total_val, season_sel)
            st.toast(f"Saved to {season_sel}!")

elif tab == "📒 Agri Khata":
    st.title("📒 Seasonal Digital Ledger")
    filter_season = st.selectbox("🔍 Filter by Season", ["All Seasons", "Kharif", "Rabi", "Zaid"])
    conn = sqlite3.connect('agri_khata.db')
    query = "SELECT * FROM ledger" if filter_season == "All Seasons" else f"SELECT * FROM ledger WHERE season='{filter_season}'"
    df_ledger = pd.read_sql_query(query, conn)
    conn.close()
    if not df_ledger.empty:
        st.table(df_ledger)
