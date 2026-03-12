import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

#  🌾  Modular Imports
from crop_engine_data import get_agri_dataframe, recommend_crops
from schemes_db import get_state_schemes, get_central_schemes

#  📍  External Location Data Import
try:
    from Locations import india_map
except ImportError:
    st.error("Locations.py not found!")
    india_map = {"Bihar": ["Patna"]}
try:
    from crop_master import all_crops
except ImportError:
    all_crops = []

# --- 1. DATABASE SETUP (PRESERVED & UPDATED FOR PRIVACY) ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    # Added user_id to separate data between different users
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

def delete_all_data(user_id):
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute("DELETE FROM ledger WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

init_db()

# --- 2. CONFIGURATION & STYLING (STRICTLY PRESERVED) ---
st.set_page_config(page_title="ASES: Agri-Smart Ecosystem", layout="wide", page_icon=" 🌾 ")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"

st.markdown("""
<style>
.main { background-color: #f0f2f6; }
.main-card { padding: 25px; border-radius: 12px; background-color: #FFFFFF !important; border: 1px solid #2481CC; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px; }
.stButton>button { border-radius: 8px; background-color: #2e7d32; color: white; width: 100%; }
[data-testid="stSidebar"] { background-color: #243139 !important; }
[data-testid="stSidebar"] * { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR (SIGN-IN & NAVIGATION) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    
    # 1. EASY SIGN-IN / SIGN-UP
    st.subheader("👤 Farmer Access")
    farmer_name = st.text_input("Enter Name to Sign In/Up", value="Guest").strip()
    if farmer_name == "Guest":
        st.caption("Sign in with your name to save personal data.")

    tab = st.radio("SELECT SERVICE", [" 🏠  Dashboard", " 🌾  Crop Engine", " 🚜  Rental Hub", " 📚  Knowledge Hub", " 🏛️  Govt Schemes", " 📈  Price Trends", " 📒  Agri Khata"])
    
    st_loc = st.selectbox("Your State", sorted(india_map.keys()))
    dt_loc = st.selectbox("Your District", sorted(india_map.get(st_loc, ["Patna"])))
    
    if st.button("Update Local Weather"):
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={dt_loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            if res.get("cod") == 200:
                st.session_state.temp, st.session_state.hum = res['main']['temp'], res['main']['humidity']
                st.success("Weather synced!")
                st.rerun()
        except:
            st.error("Connection Error")

# --- 4. TABS LOGIC ---

if tab == " 🏠  Dashboard":
    st.title(f" 👨‍🌾  Command Center: {farmer_name}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperature", f"{st.session_state.get('temp', 25)}°C")
    col2.metric("Humidity", f"{st.session_state.get('hum', 50)}%")
    col3.metric("Location Status", f"{dt_loc}")

elif tab == " 🌾  Crop Engine":
    st.title("AgriAI Smart Recommendations")
    df, le_encoder = get_agri_dataframe()
    soil_opts = ["Alluvial", "Black Soil", "Red Soil", "Sandy"]
    s_cols = st.columns(4)
    if 'soil_pref' not in st.session_state: st.session_state.soil_pref = "Alluvial"
    for i, s in enumerate(soil_opts):
        if s_cols[i].button(s): st.session_state.soil_pref = s
    st.markdown(f"Current Soil: **{st.session_state.soil_pref}**")
    bud = st.slider("Budget (₹/Acre)", 5000, 50000, 15000)
    if st.button(" 🚀  FIND BEST CROPS"):
        recs = recommend_crops(df, le_encoder, st.session_state.soil_pref, bud)
        for _, row in recs.iterrows():
            st.markdown(f'<div class="main-card"><h3>{row["Crop Name"]}</h3><p>Cost: ₹{row["Cost per Acre"]}</p></div>', unsafe_allow_html=True)

elif tab == " 🚜  Rental Hub":
    st.title(f" 🚜  Rental Machinery Desk: {dt_loc}")
    # Original HTML Injection for click-to-call preserved
    st.markdown(f'<div class="main-card"><h4>Nearby Assistance</h4><p>Contact local centers in {dt_loc}.</p><a href="tel:18001801551" style="text-decoration:none;"><button style="width:100%; padding:10px; background-color:#28a745; color:white; border:none; border-radius:5px; cursor:pointer;">📞 Call Govt CHC Helpline</button></a></div>', unsafe_allow_html=True)

elif tab == " 📚  Knowledge Hub":
    st.title(" 📚  Crop Resource Library")
    if all_crops:
        search = st.text_input(" 🔍  Search Crop Name:", "").strip()
        filtered = [c for c in all_crops if search.lower() in c['Crop'].lower()] if search else all_crops
        st.dataframe(pd.DataFrame(filtered), use_container_width=True)

elif tab == " 📈  Price Trends":
    st.title(" 📈  Mandi Price Trends")
    # Original spline graph logic preserved
    trend_prices = [2100, 2250, 2180, 2300, 2450, 2400]
    months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
    fig = px.line(pd.DataFrame({"Month": months, "Price": trend_prices}), x="Month", y="Price", markers=True, line_shape="spline", color_discrete_sequence=["#2e7d32"])
    st.plotly_chart(fig, use_container_width=True)

elif tab == " 📒  Agri Khata":
    st.title(f" 📒  Digital Ledger: {farmer_name}")
    
    # 2. CLEAR DATA OPTION AT THE TOP
    if st.button("⚠️ Clear All My Data", type="secondary"):
        delete_all_data(farmer_name)
        st.warning(f"All records for {farmer_name} have been wiped.")
        st.rerun()
    
    st.markdown("---")
    filter_season = st.selectbox(" 🔍  Filter Season", ["All Seasons", "Kharif", "Rabi", "Zaid"])
    
    conn = sqlite3.connect('agri_khata.db')
    # Use user_id to ensure Person A doesn't see Person B's data
    query = f"SELECT * FROM ledger WHERE user_id = '{farmer_name}'"
    if filter_season != "All Seasons":
        query += f" AND season='{filter_season}'"
    
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
        st.info("No records found for your account.")

    with st.expander(" ➕  Add Entry"):
        with st.form("add_form"):
            e_type = st.selectbox("Type", ["Income (Sales)", "Expense (Seeds)", "Expense (Labor)"])
            e_item = st.text_input("Item")
            e_amt = st.number_input("Amount (₹)", min_value=0)
            e_szn = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"])
            if st.form_submit_button("Save Entry"):
                add_entry(farmer_name, e_type, e_item, "1", e_amt, e_szn)
                st.success("Saved!")
                st.rerun()
