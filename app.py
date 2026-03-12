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

# --- 1. DATABASE SETUP (USER PRIVACY & MIGRATION) ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    # Ensure the table exists with the user_id column
    c.execute('''CREATE TABLE IF NOT EXISTS ledger 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id TEXT,
                  date TEXT, type TEXT, item TEXT, qty TEXT, total REAL, season TEXT)''')
    
    # Fix for existing databases: check if user_id column is present
    try:
        c.execute("SELECT user_id FROM ledger LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE ledger ADD COLUMN user_id TEXT DEFAULT 'Guest_0000'")
        
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

def delete_user_data(user_id):
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
.main-card { padding: 25px; border-radius: 12px; background-color: #FFFFFF !important; border: 1px solid #2481CC; margin-bottom: 20px; }
.call-btn { background-color: #28a745 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
[data-testid="stSidebar"] { background-color: #243139 !important; }
[data-testid="stSidebar"] * { color: #ffffff !important; }
.stButton>button { border-radius: 8px; background-color: #2e7d32; color: white; }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR (SECURE LOGIN & NAVIGATION) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    st.title("ASES NAVIGATION")
    
    # Secure Login Logic
    st.subheader("👤 Farmer Login")
    u_name = st.text_input("Name", value="Guest").strip()
    u_pin = st.text_input("PIN (4 Digits)", value="0000", type="password")
    # This combination ensures that two 'Aditis' with different PINs don't see the same data
    current_user = f"{u_name}_{u_pin}" 
    
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
            st.error("Weather service unavailable.")

# --- 4. TABS LOGIC ---

if tab == " 🏠  Dashboard":
    st.title(f" 👨‍🌾  Command Center: {u_name}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperature", f"{st.session_state.get('temp', 25)}°C")
    c2.metric("Humidity", f"{st.session_state.get('hum', 50)}%")
    c3.metric("Location Status", f"{dt_loc}")

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
    st.markdown(f'<div class="main-card"><h4>Help Center</h4><p>Location: {dt_loc}</p><a href="tel:18001801551" class="call-btn">📞 Call Govt CHC Helpline</a></div>', unsafe_allow_html=True)

elif tab == " 📚  Knowledge Hub":
    st.title(" 📚  Crop Resource Library")
    if all_crops:
        search = st.selectbox("Search Crop", [c['Crop'] for c in all_crops])
        item = next(i for i in all_crops if i['Crop'] == search)
        with st.expander(f" 📖  {item['Crop']}", expanded=True):
            st.write(f"**Season:** {item['Season']} | **NPK:** {item['N-P-K']}")
            st.info(f" 💡  {item.get('Pro-Tip', 'No tip available')}")

elif tab == " 📈  Price Trends":
    st.title(" 📈  Mandi Price Trends")
    # Dynamic crop choice from initial code
    if all_crops:
        crop_to_show = st.selectbox("Select Crop for Trend", [c['Crop'] for c in all_crops])
        trend_prices = [2100, 2250, 2180, 2300, 2450, 2400]
        fig = px.line(pd.DataFrame({"Month": ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"], "Price": trend_prices}), 
                      x="Month", y="Price", markers=True, line_shape="spline", title=f"Trends for {crop_to_show}")
        fig.update_traces(line_color='#2e7d32')
        st.plotly_chart(fig, use_container_width=True)

elif tab == " 📒  Agri Khata":
    st.title(f" 📒  Digital Ledger for {u_name}")
    
    # REQUIREMENT: Clear Data at the TOP
    if st.button("🗑️ Clear My Private Data"):
        delete_user_data(current_user)
        st.warning(f"All records for {u_name} (PIN: {u_pin}) have been cleared.")
        st.rerun()
    
    st.markdown("---")
    
    conn = sqlite3.connect('agri_khata.db')
    # Filter strictly by the combined Key
    df_ledger = pd.read_sql_query(f"SELECT * FROM ledger WHERE user_id = '{current_user}'", conn)
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
        st.info(f"No records found for {u_name}. Add an entry below to begin.")

    with st.expander(" ➕  Add Entry"):
        with st.form("add_form"):
            t = st.selectbox("Type", ["Income (Sales)", "Expense (Seeds)", "Expense (Labor)"])
            item_name = st.text_input("Item")
            amt = st.number_input("Amount (₹)", min_value=0)
            szn = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"])
            if st.form_submit_button("Save"):
                add_entry(current_user, t, item_name, "1", amt, szn)
                st.success("Entry Saved Privately!")
                st.rerun()
