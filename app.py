import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# 🌾 Modular Imports
from crop_engine_data import get_agri_dataframe, recommend_crops
from schemes_db import get_state_schemes, get_central_schemes

# 📍 External Location Data Import
try:
    from Locations import india_map
except ImportError:
    st.error("Locations.py file not found in the directory!")
    india_map = {"Bihar": ["Patna"]}  # Emergency fallback

try:
    from crop_master import all_crops
except ImportError:
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
    c.execute("INSERT INTO ledger (date, type, item, qty, total, season) VALUES (?,?,?,?,?,?)\",
              (date, entry_type, item, str(qty), total, season))
    conn.commit()
    conn.close()

init_db()

# --- 2. CONFIGURATION & TRICOLOR STYLING ---
st.set_page_config(page_title="ASES: Agri-Smart Ecosystem", layout="wide", page_icon="🌾")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #243139 !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .main-card { padding: 20px; border-radius: 12px; background-color: #FFFFFF; border: 1px solid #2e7d32; margin-bottom: 15px; }
    .stButton>button { border-radius: 12px; height: 3.5em; background-color: #2e7d32; color: white; width: 100%; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #ff9800; border: 2px solid white; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (DYNAMIC LOCATION SELECTION) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    st.title("ASES NAVIGATION")
    tab = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🌾 Crop Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📈 Price Trends", "📒 Agri Khata"])
    
    st.markdown("---")
    # State selection from dictionary keys
    st_loc = st.selectbox("Select State/UT", sorted(india_map.keys()))
    
    # District selection filtered by chosen State
    district_list = india_map.get(st_loc, ["Select District"])
    dt_loc = st.selectbox("Select District", sorted(district_list))
    
    if st.button("🔄 Sync Local Weather", use_container_width=True):
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={dt_loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            if res.get("cod") == 200:
                st.session_state.temp = res['main']['temp']
                st.session_state.hum = res['main']['humidity']
                st.success(f"Weather synced for {dt_loc}!")
                st.rerun()
        except:
            st.error("Weather service currently unavailable.")

# --- 4. DASHBOARD LOGIC ---
if tab == "🏠 Dashboard":
    st.title("👨‍🌾 Command Center")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperature", f"{st.session_state.get('temp', '--')}°C")
    c2.metric("Humidity", f"{st.session_state.get('hum', '--')}%")
    c3.metric("Location", f"{dt_loc}, {st_loc}")
    
    st.markdown(f'''
        <div class="main-card" style="border-left: 8px solid #ff9800;">
            <h3>Current Status</h3>
            <p>Monitoring agricultural conditions for <b>{dt_loc}</b> region.</p>
        </div>
    ''', unsafe_allow_html=True)

# --- 5. OTHER TABS (CORE LOGIC PRESERVED) ---
elif tab == "🌾 Crop Engine":
    st.title("🌾 Smart Crop Recommendations")
    df, le_encoder = get_agri_dataframe()
    budget = st.slider("Investment Budget (₹/Acre)", 5000, 100000, 20000)
    soil_type = st.selectbox("Soil Type", ["Alluvial", "Black", "Red", "Sandy", "Loamy"])
    
    if st.button("🚀 Analyze Best Crops"):
        recs = recommend_crops(df, le_encoder, soil_type, budget)
        for _, row in recs.iterrows():
            st.markdown(f'<div class="main-card"><h4>{row["Crop Name"]}</h4><p>Estimated Cost: ₹{row["Cost per Acre"]}</p></div>', unsafe_allow_html=True)

elif tab == "🏛️ Govt Schemes":
    st.title("🏛️ Government Schemes")
    state_schemes = get_state_schemes()
    central_schemes = get_central_schemes()
    
    cat = st.radio("Filter By", ["State-Specific", "Central Government"], horizontal=True)
    
    if cat == "State-Specific":
        scheme = state_schemes.get(st_loc, {"name": "General Assistance", "desc": "Contact local Krishi Bhavan.", "link": "#"})
        st.markdown(f'''
            <div class="main-card" style="border-left: 8px solid #ff9800;">
                <h4>{scheme['name']}</h4>
                <p>{scheme['desc']}</p>
                <a href="{scheme['link']}" target="_blank">View Details</a>
            </div>
        ''', unsafe_allow_html=True)
    else:
        for s in central_schemes:
            st.markdown(f'<div class="main-card"><b>{s["name"]}</b>: {s["desc"]}</div>', unsafe_allow_html=True)

# (Remaining tabs logic for Price Trends, Rental Hub, and Agri Khata follow the original structure)
