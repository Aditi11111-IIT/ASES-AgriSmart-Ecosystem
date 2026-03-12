import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# --- 1. MODULAR IMPORTS & DATABASE ---
try:
    from crop_engine_data import get_agri_dataframe, recommend_crops
    from schemes_db import get_state_schemes, get_central_schemes
    from Locations import india_map
    from crop_master import all_crops
except ImportError as e:
    st.error(f"Missing File: {e}")
    india_map = {"Bihar": ["Patna"]}
    all_crops = []

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

# --- 2. CONFIGURATION & STYLING (PRESERVED) ---
st.set_page_config(page_title="ASES: Agri-Smart Ecosystem", layout="wide", page_icon="🌾")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"

st.markdown("""
<style>
    .main-card { padding: 25px; border-radius: 12px; background-color: #FFFFFF !important; border: 1px solid #2481CC; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .scheme-card { padding: 20px; border-radius: 12px; background-color: #e3f2fd; border-left: 8px solid #1976d2; margin-bottom: 15px; }
    .central-card { padding: 20px; border-radius: 12px; background-color: #f1f8e9; border-left: 8px solid #2e7d32; margin-bottom: 15px; }
    .stButton>button { border-radius: 8px; background-color: #2e7d32; color: white; width: 100%; }
    .call-btn { background-color: #28a745 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
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

# --- 5. TABS LOGIC ---

if tab == "🏠 Dashboard":
    st.title("👨‍🌾 Command Center")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperature", f"{st.session_state.temp}°C")
    c2.metric("Humidity", f"{st.session_state.hum}%")
    c3.metric("Location", f"{dt_loc}, {st_loc}")

elif tab == "🌾 Crop Engine":
    st.title("AgriAI Smart Recommendations")
    df, le_encoder = get_agri_dataframe()
    # Fixed: Use buttons to update soil preference before running recommendation
    soil_opts = ["Alluvial", "Black Soil", "Red Soil", "Sandy"]
    s_cols = st.columns(4)
    for i, s in enumerate(soil_opts):
        if s_cols[i].button(s): st.session_state.soil_pref = s
    
    st.markdown(f"Selected Soil: **{st.session_state.soil_pref}**")
    bud = st.slider("Investment Budget (₹/Acre)", 5000, 50000, 15000)
    
    if st.button("🚀 FIND BEST CROPS"):
        # Fixed: recommend_crops now uses dynamic soil and budget inputs
        recs = recommend_crops(df, le_encoder, st.session_state.soil_pref, bud)
        if not recs.empty:
            for _, row in recs.iterrows():
                st.markdown(f'<div class="main-card"><h3>🌱 {row["Crop Name"]}</h3><p>Est. Cost: ₹{row["Cost per Acre"]}</p></div>', unsafe_allow_html=True)
        else:
            st.warning("No matches found for this budget/soil combination.")

elif tab == "🚜 Rental Hub":
    st.title(f"🚜 Rental Machinery Desk: {dt_loc}")
    machine_types = {
        "Preparation": [("Rotavator", "🚜"), ("Power Tiller", "⚙️")],
        "Sowing": [("Seed Drill", "🌱"), ("Rice Transplanter", "🌾")],
        "Harvesting": [("Combine Harvester", "🌾✨"), ("Thresher", "🌪️")]
    }
    m_tabs = st.tabs(list(machine_types.keys()))
    for i, category in enumerate(machine_types.keys()):
        with m_tabs[i]:
            for m_name, m_icon in machine_types[category]:
                with st.container():
                    st.markdown(f"### {m_icon} {m_name}")
                    col_a, col_b = st.columns(2)
                    col_a.link_button(f"🔍 Find Centers in {dt_loc}", f"https://www.google.com/search?q={m_name}+Rental+Service+in+{dt_loc}")
                    col_b.markdown(f'<a href="tel:18001801551" class="call-btn" style="background:#ffc107 !important; color:black !important;">📞 Call Govt Helpline</a>', unsafe_allow_html=True)
                    st.divider()

elif tab == "📚 Knowledge Hub":
    st.title("📚 Crop Resource Library")
    if all_crops:
        search = st.text_input("🔍 Search Crop Name:", "").strip()
        # Fixed: Real-time filtering of crop_master data
        filtered = [c for c in all_crops if search.lower() in c['Crop'].lower()] if search else all_crops
        
        for item in filtered:
            with st.expander(f"📖 {item['Crop']}"):
                st.write(f"**Season:** {item['Season']} | **NPK Requirement:** {item['N-P-K']}")
                st.info(f"💡 **Pro-Tip:** {item['Pro-Tip']}")
    else:
        st.error("Knowledge data not loaded. Check crop_master.py")

elif tab == "🏛️ Govt Schemes":
    st.title("🏛️ Agricultural Welfare Portal")
    state_schemes = get_state_schemes()
    central_schemes = get_central_schemes()
    choice = st.radio("Select Category", ["State Schemes", "Central Schemes"], horizontal=True)
    
    if choice == "State Schemes":
        s = state_schemes.get(st_loc, {"name": "Regional Support", "desc": "Visit local Krishi Bhavan", "link": "#"})
        st.markdown(f'<div class="scheme-card"><h2>🌟 {s["name"]}</h2><p>{s["desc"]}</p><a href="{s["link"]}" target="_blank">🔗 Official Portal</a></div>', unsafe_allow_html=True)
    else:
        for cs in central_schemes:
            st.markdown(f'<div class="central-card"><h3>🏢 {cs["name"]}</h3><p>{cs["desc"]}</p></div>', unsafe_allow_html=True)

elif tab == "📈 Price Trends":
    st.title("📈 Price Forecast & Calculator")
    if all_crops:
        crop_names = [c['Crop'] for c in all_crops]
        col1, col2, col3 = st.columns(3)
        with col1: sel_crop = st.selectbox("Select Crop", crop_names)
        with col2: weight = st.number_input("Quantity (Quintals)", min_value=0.1, value=10.0)
        with col3: season_sel = st.selectbox("Season Tag", ["Kharif", "Rabi", "Zaid"])

        base_price = 2000 + (hash(sel_crop) % 2000)
        total_val = base_price * weight
        st.metric("Estimated Market Value", f"₹{total_val:,.2f}")

        if st.button("📓 Save Sale to Agri Khata"):
            add_entry("Income (Sale)", sel_crop, weight, total_val, season_sel)
            st.success("Sale Recorded!")

        # 12-Month Trend Cycle
        months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
        # Simplified trend logic
        trend_prices = [base_price * (1 + (i % 3 - 1) * 0.05) for i in range(12)]
        fig = px.line(x=months, y=trend_prices, markers=True, title=f"Annual Price Forecast: {sel_crop}")
        fig.update_traces(line_color='#2e7d32')
        st.plotly_chart(fig, use_container_width=True)

elif tab == "📒 Agri Khata":
    st.title("📒 Seasonal Digital Ledger")
    filter_season = st.selectbox("🔍 Filter by Season", ["All Seasons", "Kharif", "Rabi", "Zaid"])
    
    conn = sqlite3.connect('agri_khata.db')
    query = "SELECT * FROM ledger" if filter_season == "All Seasons" else f"SELECT * FROM ledger WHERE season='{filter_season}'"
    df_ledger = pd.read_sql_query(query, conn)
    conn.close()

    if not df_ledger.empty:
        # Fixed: Improved financial summary metrics
        income = df_ledger[df_ledger['type'].str.contains('Income')]['total'].sum()
        expense = df_ledger[df_ledger['type'].str.contains('Expense')]['total'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Revenue", f"₹{income:,.2f}")
        c2.metric("Total Expense", f"₹{expense:,.2f}")
        c3.metric("Net Profit", f"₹{income - expense:,.2f}", delta=float(income-expense))
        
        st.dataframe(df_ledger, use_container_width=True, hide_index=True)
    else:
        st.info("No records found for this season.")

    with st.expander("➕ Log New Expense"):
        col_ex1, col_ex2 = st.columns(2)
        e_item = col_ex1.text_input("Expense Detail (e.g., Seeds, Fertilizer)")
        e_amt = col_ex2.number_input("Amount (₹)", min_value=0)
        e_s = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"], key="exp_season")
        if st.button("Save Expense"):
            add_entry("Expense", e_item, "1", e_amt, e_s)
            st.rerun()
