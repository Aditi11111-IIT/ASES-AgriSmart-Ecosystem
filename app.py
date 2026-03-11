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

# --- 4. TAB LOGIC ---

if tab == "🏠 Dashboard":
    st.title("👨‍🌾 Command Center")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperature", f"{st.session_state.get('temp', 25)}°C")
    c2.metric("Humidity", f"{st.session_state.get('hum', 50)}%")
    c3.metric("Location", f"{dt_loc}, {st_loc}")
    
    st.markdown(f'''
        <div class="main-card" style="border-left: 8px solid #ff9800;">
            <h3>Welcome to Agri-Smart Ecosystem</h3>
            <p>Currently monitoring <b>{dt_loc}</b>. Use the sidebar to access specialized farming services.</p>
        </div>
    ''', unsafe_allow_html=True)

elif tab == "🌾 Crop Engine":
    st.title("🌾 Smart Crop Recommendations")
    df, le_encoder = get_agri_dataframe()
    budget = st.slider("Investment Budget (₹/Acre)", 5000, 100000, 20000)
    soil_type = st.selectbox("Soil Type", ["Alluvial", "Black", "Red", "Sandy", "Loamy"])
    
    if st.button("🚀 Analyze Best Crops"):
        recs = recommend_crops(df, le_encoder, soil_type, budget)
        if not recs.empty:
            for _, row in recs.iterrows():
                st.markdown(f'''
                    <div class="main-card">
                        <h4>{row["Crop Name"]}</h4>
                        <p><b>Estimated Cost:</b> ₹{row["Cost per Acre"]}<br>
                        <b>Potential Yield:</b> {row.get("Yield", "High")}</p>
                    </div>
                ''', unsafe_allow_html=True)
        else:
            st.warning("No crops found for this budget/soil combination.")

elif tab == "🚜 Rental Hub":
    st.title("🚜 Equipment Rental Marketplace")
    machines = {
        "Tractor": {"price": "₹800/hr", "img": "🚜"},
        "Harvester": {"price": "₹1500/hr", "img": "🌾"},
        "Drone Sprayer": {"price": "₹500/acre", "img": "🚁"}
    }
    for name, info in machines.items():
        with st.container():
            st.markdown(f'''
                <div class="main-card">
                    <h3>{info["img"]} {name}</h3>
                    <p>Price: <b>{info["price"]}</b></p>
                    <button style="width:100%; padding:10px; background:#2e7d32; color:white; border:none; border-radius:5px;">Book Now</button>
                </div>
            ''', unsafe_allow_html=True)

elif tab == "📚 Knowledge Hub":
    st.title("📚 Farming Knowledge Base")
    category = st.selectbox("Topic", ["Pest Control", "Organic Farming", "Irrigation Tech"])
    articles = {
        "Pest Control": "Use Neem oil spray (5ml/L) for natural aphid control...",
        "Organic Farming": "Composting requires a 30:1 Carbon to Nitrogen ratio...",
        "Irrigation Tech": "Drip irrigation can save up to 40% water in {st_loc}."
    }
    st.markdown(f'<div class="main-card">{articles[category]}</div>', unsafe_allow_html=True)

elif tab == "🏛️ Govt Schemes":
    st.title("🏛️ Government Schemes")
    state_schemes = get_state_schemes()
    central_schemes = get_central_schemes()
    
    cat = st.radio("Filter", ["State-Specific", "Central"], horizontal=True)
    if cat == "State-Specific":
        scheme = state_schemes.get(st_loc, {"name": "Local Support", "desc": "Visit your District Agriculture Office."})
        st.markdown(f'<div class="main-card" style="border-left: 8px solid #ff9800;"><h4>{scheme["name"]}</h4><p>{scheme["desc"]}</p></div>', unsafe_allow_html=True)
    else:
        for s in central_schemes:
            st.markdown(f'<div class="main-card"><b>{s["name"]}</b>: {s["desc"]}</div>', unsafe_allow_html=True)

elif tab == "📈 Price Trends":
    st.title("📈 Mandi Price Insights")
    st.info(f"Showing estimated trends for {dt_loc}")
    # Placeholder chart for price trends
    chart_data = pd.DataFrame({"Month": ["Jan", "Feb", "Mar"], "Price": [2100, 2250, 2180]})
    fig = px.line(chart_data, x="Month", y="Price", title="Wheat Price Trend (₹/Quintal)")
    st.plotly_chart(fig, use_container_width=True)

elif tab == "📒 Agri Khata":
    st.title("📒 Seasonal Digital Ledger")
    filter_season = st.selectbox("🔍 View Records", ["All Seasons", "Kharif", "Rabi", "Zaid"])
    
    conn = sqlite3.connect('agri_khata.db')
    query = "SELECT * FROM ledger" if filter_season == "All Seasons" else f"SELECT * FROM ledger WHERE season='{filter_season}'"
    df_ledger = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df_ledger.empty:
        inc = df_ledger[df_ledger['type'].str.contains('Income')]['total'].sum()
        exp = df_ledger[df_ledger['type'].str.contains('Expense')]['total'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Revenue", f"₹{inc:,.0f}")
        c2.metric("Investment", f"₹{exp:,.0f}")
        c3.metric("Net Profit", f"₹{inc - exp:,.0f}")
        st.dataframe(df_ledger, use_container_width=True)
    else:
        st.info("No records found for this selection.")

    with st.expander("➕ Add Transaction"):
        with st.form("khata_form"):
            t_type = st.selectbox("Type", ["Income (Sales)", "Expense (Seeds)", "Expense (Labor)", "Expense (Machinery)"])
            item = st.text_input("Item Description")
            amt = st.number_input("Amount (₹)", min_value=0.0)
            szn = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"])
            if st.form_submit_button("Save Transaction"):
                add_entry(t_type, item, "1", amt, szn)
                st.success("Record Saved!")
                st.rerun()
