import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# 🌾 Modular Imports (Corrected variable names)
try:
    from crop_engine_data import get_agri_dataframe, recommend_crops
    from schemes_db import get_state_schemes, get_central_schemes
    from Locations import india_map
    from crop_master import all_crops
except ImportError as e:
    st.error(f"⚠️ Missing Module: {e}")
    india_map = {"Bihar": ["Patna", "Gaya", "Muzaffarpur"]}
    all_crops = []

# --- 1. DATABASE SETUP (PERSISTENT) ---
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

# --- 2. CONFIGURATION & STYLING ---
st.set_page_config(page_title="ASES: Agri-Smart Ecosystem", layout="wide", page_icon=" 🌾 ")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"

st.markdown("""
<style>
.main-card { padding: 25px; border-radius: 12px; background-color: #FFFFFF !important; border: 1px solid #2481CC; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px; }
.scheme-card { padding: 20px; border-radius: 12px; background-color: #e3f2fd; border-left: 8px solid #1976d2; margin-bottom: 15px; }
.central-card { padding: 20px; border-radius: 12px; background-color: #f1f8e9; border-left: 8px solid #2e7d32; margin-bottom: 15px; }
.stButton>button { border-radius: 8px; background-color: #2e7d32; color: white; width: 100%; }
.call-btn { background-color: #ffc107 !important; color: black !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
[data-testid="stSidebar"] { background-color: #243139 !important; }
[data-testid="stSidebar"] * { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'temp' not in st.session_state: st.session_state.temp = 25
if 'hum' not in st.session_state: st.session_state.hum = 50
if 'soil_pref' not in st.session_state: st.session_state.soil_pref = "Alluvial"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    tab = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🌾 Crop Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📈 Price Trends", "📒 Agri Khata"])
    st_loc = st.selectbox("Your State", sorted(india_map.keys()))
    dt_loc = st.selectbox("Your District", sorted(india_map.get(st_loc, ["Patna"])))
    
    if st.button("🔄 Sync Weather"):
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={dt_loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            if res.get("cod") == 200:
                st.session_state.temp, st.session_state.hum = res['main']['temp'], res['main']['humidity']
                st.success("Weather synced!")
                st.rerun()
        except: st.error("Connection Error")

# --- 5. TABS LOGIC ---

if tab == "🏠 Dashboard":
    st.title(f"👨‍🌾 Command Center: {dt_loc}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperature", f"{st.session_state.temp}°C")
    c2.metric("Humidity", f"{st.session_state.hum}%")
    c3.metric("Status", "Online", delta="IITP-ASES v1.4")
    
    if st.session_state.temp > 35: st.error("🔥 Heatwave Alert: Check soil moisture immediately.")
    elif st.session_state.hum > 80: st.warning("🪳 High Humidity: Potential fungal/pest risk detected.")

elif tab == "🌾 Crop Engine":
    st.title("AgriAI Smart Recommendations")
    df, le_encoder = get_agri_dataframe()
    
    # --- Feature: Small Farmer Filter ---
    is_small_farmer = st.checkbox("🚜 Small Farmer Mode", help="Limits results to high-resilience, low-budget crops.")
    soil_opts = ["Alluvial", "Black Soil", "Red Soil", "Sandy"]
    soil = st.selectbox("Select Soil Type", soil_opts)
    
    max_bud = 10000 if is_small_farmer else 50000
    bud = st.slider("Budget (₹/Acre)", 2000 if is_small_farmer else 5000, max_bud, 10000)
    
    if st.button("🚀 FIND BEST CROPS"):
        recs = recommend_crops(df, le_encoder, soil, bud)
        if is_small_farmer: recs = recs
