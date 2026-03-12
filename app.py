import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime
import uuid  # 🆕 Added for user privacy

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

# --- 1. DATABASE SETUP (USER-AWARE) ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    # 🆕 Added user_id column to separate data between different farmers
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
    # 🆕 Now inserts the specific user_id
    c.execute("INSERT INTO ledger (user_id, date, type, item, qty, total, season) VALUES (?,?,?,?,?,?,?)",
              (user_id, date, entry_type, item, str(qty), total, season))
    conn.commit()
    conn.close()

init_db()

# --- 2. USER SESSION PRIVACY ---
# 🆕 This creates a unique ID for the current visitor's browser session
if 'user_key' not in st.session_state:
    st.session_state.user_key = str(uuid.uuid4())

# --- 3. CONFIGURATION & STYLING (PRESERVED) ---
st.set_page_config(page_title="ASES: Agri-Smart Ecosystem", layout="wide", page_icon=" 🌾 ")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"

st.markdown("""
<style>
.main-card { padding: 25px; border-radius: 12px; background-color: #FFFFFF !important; border: 1px solid #2481CC; margin-bottom: 20px; }
.call-btn { background-color: #28a745 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
[data-testid="stSidebar"] { background-color: #243139 !important; }
[data-testid="stSidebar"] * { color: #ffffff !important; }
.stButton>button { border-radius: 8px; background-color: #2e7d32; color: white; }
</style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Education_Patna_Logo.png", width=120)
    st.title("ASES NAVIGATION")
    tab = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🌾 Crop Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📈 Price Trends", "📒 Agri Khata"])
    
    st_loc = st.selectbox("Select State/UT", sorted(india_map.keys()))
    district_list = india_map.get(st_loc, ["Select District"])
    dt_loc = st.selectbox("Select District", sorted(district_list))
    
    if st.button("🔄 Sync Local Weather"):
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={dt_loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            if res.get("cod") == 200:
                st.session_state.temp, st.session_state.hum = res['main']['temp'], res['main']['humidity']
                st.success(f"Weather updated for {dt_loc}!")
                st.rerun()
        except:
            st.error("Weather service unavailable.")

# --- 5. TABS LOGIC ---

if tab == "🏠 Dashboard":
    st.title("👨‍🌾 Command Center")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperature", f"{st.session_state.get('temp', 25)}°C")
    c2.metric("Humidity", f"{st.session_state.get('hum', 50)}%")
    c3.metric("Location", f"{dt_loc}, {st_loc}")

elif tab == "🚜 Rental Hub":
    st.title(f"🚜 Machinery Rental: {dt_loc}")
    selected_machine = st.selectbox("Choose Equipment", ["Tractor", "Harvester", "Drone Sprayer", "Rotavator"])
    st.markdown(f'<div class="main-card"><h4>{selected_machine} Status</h4><p>Available for rent in {dt_loc} region.</p></div>', unsafe_allow_html=True)
    st.markdown(f'<a href="tel:18001801551" class="call-btn">📞 Call Kisan Call Centre</a>', unsafe_allow_html=True)
    st.link_button("🔍 Find Local Rental Centers", f"https://www.google.com/search?q={selected_machine}+rental+near+{dt_loc}")

elif tab == "📈 Price Trends":
    st.title("📈 Mandi Price Trends")
    trend_data = pd.DataFrame({"Month": ["Oct", "Nov", "Dec", "Jan", "Feb"], "Price": [2100, 2150, 2200, 2350, 2300]})
    fig = px.line(trend_data, x="Month", y="Price", markers=True, line_shape="spline")
    fig.update_traces(line_color='#2e7d32')
    st.plotly_chart(fig, use_container_width=True)

elif tab == "📒 Agri Khata":
    st.title("📒 Seasonal Digital Ledger")
    filter_season = st.selectbox("🔍 Filter Season", ["All Seasons", "Kharif", "Rabi", "Zaid"])
    
    conn = sqlite3.connect('agri_khata.db')
    # 🆕 FILTERED QUERY: Only show data belonging to THIS user's unique key
    if filter_season == "All Seasons":
        query = f"SELECT * FROM ledger WHERE user_id = '{st.session_state.user_key}'"
    else:
        query = f"SELECT * FROM ledger WHERE user_id = '{st.session_state.user_key}' AND season='{filter_season}'"
    
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
    else:
        st.info("No personal records found. Your data is private to this session.")

    with st.expander("➕ Add Entry"):
        with st.form("ledger_form"):
            t_type = st.selectbox("Type", ["Income (Sales)", "Expense (Seeds/Fertilizer)", "Expense (Labor)"])
            item = st.text_input("Item Name")
            total_val = st.number_input("Amount (₹)", min_value=0.0)
            season = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"])
            if st.form_submit_button("Save Entry"):
                # 🆕 Passing user_key to save correctly
                add_entry(st.session_state.user_key, t_type, item, "1", total_val, season)
                st.success("Entry Saved Privately!")
                st.rerun()

# (Other tabs like Crop Engine and Knowledge Hub remain exactly the same as previous integration)
