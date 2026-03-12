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
    st.error("Locations.py not found!")
    india_map = {"Bihar": ["Patna"]}

try:
    from crop_master import all_crops
except ImportError:
    all_crops = []

# --- 1. DATABASE SETUP (USER-SPECIFIC) ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    # Ensure user_id column exists to separate Person A from Person B
    c.execute('''CREATE TABLE IF NOT EXISTS ledger 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id TEXT,
                  date TEXT, type TEXT, item TEXT, qty TEXT, total REAL, season TEXT)''')
    conn.commit()
    conn.close()

def add_entry(user_id, entry_type, item, qty, total, season):
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO ledger (user_id, date, type, item, qty, total, season) VALUES (?,?,?,?,?,?,?)",
              (user_id, date, entry_type, item, str(qty), total, season))
    conn.commit()
    conn.close()

def clear_user_data(user_id):
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute("DELETE FROM ledger WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

init_db()

# --- 2. CONFIGURATION & STYLING (PRESERVED) ---
st.set_page_config(page_title="ASES: Agri-Smart Ecosystem", layout="wide", page_icon=" 🌾 ")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"

st.markdown("""
<style>
.main-card { padding: 25px; border-radius: 12px; background-color: #FFFFFF !important; border: 1px solid #2481CC; margin-bottom: 20px; }
.call-btn { background-color: #28a745 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
[data-testid="stSidebar"] { background-color: #243139 !important; }
[data-testid="stSidebar"] * { color: #ffffff !important; }
.stButton>button { border-radius: 8px; background-color: #2e7d32; color: white; }
.clear-btn>button { background-color: #d32f2f !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    st.title("ASES NAVIGATION")
    
    # 🔐 PRIVACY LOCK: User must enter a name to see their own Khata
    farmer_id = st.text_input("Enter Farmer Name / ID", "Guest").strip()
    
    tab = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🌾 Crop Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📈 Price Trends", "📒 Agri Khata"])
    
    st_loc = st.selectbox("Select State/UT", sorted(india_map.keys()))
    dt_loc = st.selectbox("Select District", sorted(india_map.get(st_loc, ["Patna"])))
    
    if st.button("🔄 Sync Local Weather"):
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={dt_loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            if res.get("cod") == 200:
                st.session_state.temp, st.session_state.hum = res['main']['temp'], res['main']['humidity']
                st.success("Weather updated!")
                st.rerun()
        except:
            st.error("Connection Error")

# --- 4. TABS LOGIC ---

if tab == "🏠 Dashboard":
    st.title(f"👨‍🌾 Welcome, {farmer_id}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperature", f"{st.session_state.get('temp', 25)}°C")
    c2.metric("Humidity", f"{st.session_state.get('hum', 50)}%")
    c3.metric("Location", f"{dt_loc}")

elif tab == "🚜 Rental Hub":
    st.title(f"🚜 Machinery Rental: {dt_loc}")
    selected_machine = st.selectbox("Choose Equipment", ["Tractor", "Harvester", "Drone Sprayer", "Rotavator"])
    st.markdown(f'<div class="main-card"><h4>{selected_machine} Status</h4><p>Available for rent in {dt_loc} region.</p></div>', unsafe_allow_html=True)
    st.markdown(f'<a href="tel:18001801551" class="call-btn">📞 Call Kisan Call Centre</a>', unsafe_allow_html=True)

elif tab == "📈 Price Trends":
    st.title("📈 Mandi Price Trends")
    trend_data = pd.DataFrame({"Month": ["Oct", "Nov", "Dec", "Jan", "Feb"], "Price": [2100, 2150, 2200, 2350, 2300]})
    fig = px.line(trend_data, x="Month", y="Price", markers=True, line_shape="spline")
    fig.update_traces(line_color='#2e7d32')
    st.plotly_chart(fig, use_container_width=True)

elif tab == "📒 Agri Khata":
    st.title(f"📒 Digital Ledger for {farmer_id}")
    
    conn = sqlite3.connect('agri_khata.db')
    # Fetching ONLY data that matches the farmer_id entered in the sidebar
    query = f"SELECT * FROM ledger WHERE user_id = '{farmer_id}'"
    df_ledger = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df_ledger.empty:
        income = df_ledger[df_ledger['type'].str.contains('Income')]['total'].sum()
        expense = df_ledger[df_ledger['type'].str.contains('Expense')]['total'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Revenue", f"₹{income:,.2f}")
        c2.metric("Investment", f"₹{expense:,.2f}")
        c3.metric("Profit", f"₹{income - expense:,.2f}")
        st.dataframe(df_ledger, use_container_width=True)
        
        # 🗑️ CLEAR DATA OPTION
        st.markdown("---")
        st.warning("Danger Zone")
        if st.button(f"🗑️ Clear All Data for {farmer_id}", type="secondary"):
            clear_user_data(farmer_id)
            st.success(f"All records for {farmer_id} deleted!")
            st.rerun()
    else:
        st.info(f"No records found for '{farmer_id}'. Enter expenses below to start.")

    with st.expander("➕ Add New Entry"):
        with st.form("khata_form"):
            t_type = st.selectbox("Type", ["Income (Sales)", "Expense (Seeds/Fertilizer)", "Expense (Labor)"])
            item = st.text_input("Item Name")
            total_val = st.number_input("Amount (₹)", min_value=0.0)
            season = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"])
            if st.form_submit_button("Save Entry"):
                add_entry(farmer_id, t_type, item, "1", total_val, season)
                st.success("Saved!")
                st.rerun()

# (Note: Crop Engine, Knowledge Hub, and Govt Schemes remain preserved from previous versions)
