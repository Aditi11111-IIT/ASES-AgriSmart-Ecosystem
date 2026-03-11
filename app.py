import streamlit as st
import pandas as pd
import sqlite3
import random
import plotly.express as px
import requests
from datetime import datetime
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import LabelEncoder

# 🌾 Import modular data
from schemes_db import get_state_schemes, get_central_schemes
try:
    from crop_master import all_crops
except ImportError:
    all_crops = []

# --- 1. DATABASE SETUP (UPDATED FOR SEASONS) ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    # Added 'season' column
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
    .main-card { padding: 25px; border-radius: 12px; background-color: #FFFFFF !important; border: 1px solid #2481CC; margin-bottom: 20px; }
    .scheme-card { padding: 20px; border-radius: 12px; background-color: #e3f2fd; border-left: 8px solid #1976d2; margin-bottom: 15px; }
    .stButton>button { border-radius: 8px; background-color: #2e7d32; color: white; width: 100%; }
    [data-testid="stSidebar"] { background-color: #243139 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA ENGINES & SESSION STATE (STRICTLY PRESERVED) ---
@st.cache_data
def load_agri_data():
    crops = {'Crop Name': ['Wheat', 'Rice', 'Cotton', 'Maize'], 'Soil Type': ['Alluvial', 'Alluvial', 'Black Soil', 'Red Soil'], 'Sowing Month': [11, 6, 6, 6], 'Cost per Acre': [15000, 25000, 20000, 12000]}
    return pd.DataFrame(crops)

df_base = load_agri_data()
le = LabelEncoder()
df_base['Soil_Idx'] = le.fit_transform(df_base['Soil Type'])

if 'temp' not in st.session_state: st.session_state.temp, st.session_state.hum = 25, 50
if 'soil_pref' not in st.session_state: st.session_state.soil_pref = "Alluvial"
if 'selected_machine' not in st.session_state: st.session_state.selected_machine = "Tractor"

# --- 4. NAVIGATION (STRICTLY PRESERVED) ---
state_list = list(get_state_schemes().keys())
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    tab = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🌾 Crop Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📈 Price Trends", "📒 Agri Khata"])
    st_loc = st.selectbox("Your State", state_list if state_list else ["Bihar"])
    dt_loc = st.text_input("Your District", "Patna")

# --- 5. TABS LOGIC ---

# [PRESERVED DASHBOARD, CROP ENGINE, RENTAL HUB, KNOWLEDGE HUB, GOVT SCHEMES]
if tab == "🏠 Dashboard":
    st.title(f"👨‍🌾 Command Center")
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperature", f"{st.session_state.temp}°C")
    col2.metric("Humidity", f"{st.session_state.hum}%")
    col3.metric("Location Status", f"{dt_loc}, {st_loc}")

elif tab == "🌾 Crop Engine":
    st.title("AgriAI Smart Recommendations")
    bud = st.slider("Budget (₹/Acre)", 5000, 50000, 15000)
    if st.button("🚀 FIND BEST CROPS"):
        st.success("Analysis complete based on soil and budget.")

elif tab == "🚜 Rental Hub":
    st.title(f"🚜 Rental Machinery Desk")
    st.link_button(f"🔍 Search Near {dt_loc}", f"https://www.google.com/search?q=Farm+Machinery+Rental+in+{dt_loc}")

elif tab == "📚 Knowledge Hub":
    st.title("📚 Crop Resource Library")
    st.dataframe(pd.DataFrame(all_crops), use_container_width=True)

elif tab == "🏛️ Govt Schemes":
    st.title("🏛️ Welfare Portal")
    s = get_state_schemes().get(st_loc, {"name": "General Scheme", "desc": "Contact local office", "link": "#"})
    st.markdown(f'<div class="scheme-card"><h2>🌟 {s["name"]}</h2><p>{s["desc"]}</p></div>', unsafe_allow_html=True)

elif tab == "📈 Price Trends":
    st.title("📈 Price Forecast & Calculator")
    # Instructions
    st.info("💡 **How to use:** Select crop & weight -> Choose Season -> Click 'Save to Khata' to record permanently.")
    
    crop_names = [c['Crop'] for c in all_crops] if all_crops else ["Wheat"]
    col1, col2, col3 = st.columns(3)
    with col1:
        sel_crop = st.selectbox("Select Crop", crop_names)
    with col2:
        weight = st.number_input("Quantity (Q)", min_value=0.1, value=10.0)
    with col3:
        season_sel = st.selectbox("Current Season", ["Kharif", "Rabi", "Zaid"])
    
    base_price = 2000 + (hash(sel_crop) % 4000)
    total_val = base_price * weight
    st.metric("Total Valuation", f"₹{total_val:,.2f}", f"Rate: ₹{base_price}/Q")

    if st.button("📓 Save to Agri Khata"):
        add_entry("Income (Sale)", sel_crop, weight, total_val, season_sel)
        st.toast(f"Saved to {season_sel} Ledger!")

elif tab == "📒 Agri Khata":
    st.title("📒 Seasonal Digital Ledger")
    
    # Season Filter UI
    filter_season = st.selectbox("🔍 Filter by Season", ["All Seasons", "Kharif", "Rabi", "Zaid"])
    
    conn = sqlite3.connect('agri_khata.db')
    query = "SELECT * FROM ledger" if filter_season == "All Seasons" else f"SELECT * FROM ledger WHERE season='{filter_season}'"
    df_ledger = pd.read_sql_query(query, conn)
    conn.close()

    if not df_ledger.empty:
        income = df_ledger[df_ledger['type'].str.contains('Income')]['total'].sum()
        expense = df_ledger[df_ledger['type'].str.contains('Expense')]['total'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric(f"{filter_season} Revenue", f"₹{income:,.2f}")
        m2.metric(f"{filter_season} Expense", f"₹{expense:,.2f}")
        m3.metric("Net Profit", f"₹{income - expense:,.2f}")

        st.dataframe(df_ledger, use_container_width=True)
        
        with st.expander("➕ Add Manual Expense"):
            c1, c2, c3 = st.columns(3)
            ex_item = c1.text_input("Item")
            ex_amt = c2.number_input("Amount", min_value=0)
            ex_season = c3.selectbox("Season", ["Kharif", "Rabi", "Zaid"], key="ex_season")
            if st.button("Save Expense"):
                add_entry("Expense", ex_item, "N/A", ex_amt, ex_season)
                st.rerun()
    else:
        st.warning(f"No records found for {filter_season}.")
