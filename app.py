import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# 🌾 Modular Imports
from crop_engine_data import get_agri_dataframe, recommend_crops
from schemes_db import get_state_schemes, get_central_schemes
# NEW: Import the dictionary from your Locations file
from Locations import india_map 

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

# --- 2. CONFIGURATION & TRICOLOR STYLING ---
st.set_page_config(page_title="ASES Mobile", layout="wide", page_icon="🌾")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"

# Styling preserved from source
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #243139 !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .main-card { padding: 20px; border-radius: 12px; background-color: #FFFFFF; border: 1px solid #2e7d32; margin-bottom: 15px; }
    .stButton>button { border-radius: 12px; height: 3.5em; background-color: #2e7d32; color: white; width: 100%; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (USING IMPORTED LOCATIONS) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    st.title("ASES NAVIGATION")
    tab = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🌾 Crop Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📈 Price Trends", "📒 Agri Khata"])
    
    st.markdown("---")
    
    # Dynamic Selection logic using the imported 'india_map'
    st_loc = st.selectbox("Your State", sorted(india_map.keys()))
    district_list = india_map.get(st_loc, ["Patna"])
    dt_loc = st.selectbox("Your District", sorted(district_list))
    
    if st.button("🔄 Sync Weather"):
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={dt_loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            if res.get("cod") == 200:
                st.session_state.temp = res['main']['temp']
                st.session_state.hum = res['main']['humidity']
                st.success(f"Weather updated for {dt_loc}!")
                st.rerun()
        except: st.error("Connection Error")

# --- 4. TABS LOGIC (REMAINING SAME) ---
if tab == "🏠 Dashboard":
    st.title("👨‍🌾 Command Center")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperature", f"{st.session_state.get('temp', 25)}°C")
    c2.metric("Humidity", f"{st.session_state.get('hum', 50)}%")
    c3.metric("Location", f"{dt_loc}, {st_loc}")
