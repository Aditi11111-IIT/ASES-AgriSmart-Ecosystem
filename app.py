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
    st.error("Locations.py not found! Ensure it is in the same folder as app.py.")
    india_map = {"Bihar": ["Patna"]} 

try:
    from crop_master import all_crops
except ImportError:
    all_crops = []

# --- 1. DATABASE SETUP ---
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
st.set_page_config(page_title="ASES: Agri-Smart Ecosystem", layout="wide", page_icon="🌾")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #243139 !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .main-card { padding: 20px; border-radius: 12px; background-color: #FFFFFF; border: 1px solid #2e7d32; margin-bottom: 15px; }
    .stButton>button { border-radius: 12px; height: 3.5em; background-color: #2e7d32; color: white; width: 100%; font-weight: bold; }
    .stButton>button:hover { background-color: #ff9800; border: 2px solid white; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    st.title("ASES NAVIGATION")
    tab = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🌾 Crop Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📈 Price Trends", "📒 Agri Khata"])
    
    st.markdown("---")
    st_loc = st.selectbox("Select State/UT", sorted(india_map.keys()))
    district_list = india_map.get(st_loc, ["Select District"])
    dt_loc = st.selectbox("Select District", sorted(district_list))
    
    if st.button("🔄 Sync Weather", use_container_width=True):
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={dt_loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            if res.get("cod") == 200:
                st.session_state.temp = res['main']['temp']
                st.session_state.hum = res['main']['humidity']
                st.success(f"Weather updated for {dt_loc}!")
                st.rerun()
        except:
            st.error("Connection Error")

# --- 4. TAB LOGIC (RESTORING ORIGINAL SOURCE SECTIONS) ---

if tab == "🏠 Dashboard":
    st.title("👨‍🌾 Command Center")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperature", f"{st.session_state.get('temp', 25)}°C")
    c2.metric("Humidity", f"{st.session_state.get('hum', 50)}%")
    c3.metric("Location", f"{dt_loc}, {st_loc}")
    st.markdown(f'<div class="main-card" style="border-left: 8px solid #ff9800;"><b>Status:</b> Currently tracking {dt_loc} region.</div>', unsafe_allow_html=True)

elif tab == "🌾 Crop Engine":
    st.title("🌾 Smart Crop Recommendations")
    df, le_encoder = get_agri_dataframe()
    budget = st.slider("Investment Budget (₹/Acre)", 5000, 100000, 20000)
    soil_type = st.selectbox("Soil Type", ["Alluvial", "Black", "Red", "Sandy", "Loamy"])
    if st.button("🚀 Analyze Best Crops"):
        recs = recommend_crops(df, le_encoder, soil_type, budget)
        st.dataframe(recs, use_container_width=True)

elif tab == "🚜 Rental Hub":
    st.title("🚜 Equipment Rental Marketplace")
    st.markdown("### Available Machinery near " + dt_loc)
    # Matching original logic: List view with selection
    col1, col2 = st.columns([1, 2])
    with col1:
        selected_machine = st.selectbox("Select Equipment", ["Tractor (50HP)", "Harvester", "Plow", "Power Tiller", "Drone Sprayer"])
    with col2:
        st.markdown(f'''<div class="main-card">
            <h4>{selected_machine} Details</h4>
            <p>Rental Cost: ₹800 - ₹2500 per unit/day<br>
            Availability: <b>In Stock</b></p>
            </div>''', unsafe_allow_html=True)
    if st.button("Confirm Booking Request"):
        st.success(f"Request for {selected_machine} sent to vendors in {dt_loc}!")

elif tab == "📚 Knowledge Hub":
    st.title("📚 Crop Knowledge Base")
    # Restoring original crop master search
    search_crop = st.selectbox("Search Crop Details", all_crops if all_crops else ["Wheat", "Rice", "Maize"])
    st.markdown(f"""
        <div class="main-card">
            <h3>Standard Guidelines for {search_crop}</h3>
            <ul>
                <li><b>Ideal Temperature:</b> 15°C - 25°C</li>
                <li><b>Water Requirement:</b> Moderate to High</li>
                <li><b>Best Sowing Month:</b> October - November (Rabi)</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

elif tab == "🏛️ Govt Schemes":
    st.title("🏛️ Government Schemes")
    state_schemes = get_state_schemes()
    central_schemes = get_central_schemes()
    cat = st.radio("Category", ["State", "Central"], horizontal=True)
    if cat == "State":
        s = state_schemes.get(st_loc, {"name": "General Farmer Support", "desc": "Contact local District office."})
        st.markdown(f'<div class="main-card"><b>{s["name"]}</b><br>{s["desc"]}</div>', unsafe_allow_html=True)
    else:
        for s in central_schemes:
            st.markdown(f'<div class="main-card"><b>{s["name"]}</b>: {s["desc"]}</div>', unsafe_allow_html=True)

elif tab == "📈 Price Trends":
    st.title("📈 Mandi Price Trends")
    st.markdown(f"**Live Market Data Simulation for {dt_loc}**")
    # Restoring Plotly Line Chart from source
    trend_data = pd.DataFrame({
        "Month": ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb"],
        "Price": [2150, 2200, 2180, 2300, 2450, 2400]
    })
    fig = px.line(trend_data, x="Month", y="Price", title=f"Price Trend (₹/Quintal)", markers=True)
    fig.update_traces(line_color='#2e7d32')
    st.plotly_chart(fig, use_container_width=True)
    

elif tab == "📒 Agri Khata":
    st.title("📒 Seasonal Digital Ledger")
    filter_season = st.selectbox("Filter Records", ["All", "Kharif", "Rabi", "Zaid"])
    conn = sqlite3.connect('agri_khata.db')
    query = "SELECT * FROM ledger" if filter_season == "All" else f"SELECT * FROM ledger WHERE season='{filter_season}'"
    df_ledger = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df_ledger.empty:
        st.dataframe(df_ledger, use_container_width=True)
    else:
        st.info("No records found.")

    with st.expander("Add Entry"):
        with st.form("ledger"):
            t = st.selectbox("Type", ["Income", "Expense"])
            item = st.text_input("Item")
            val = st.number_input("Amount")
            szn = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"])
            if st.form_submit_button("Save"):
                add_entry(t, item, "1", val, szn)
                st.rerun()
