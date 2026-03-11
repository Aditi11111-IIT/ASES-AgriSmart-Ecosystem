import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# 🌾 Modular Imports (Preserved)
from crop_engine_data import get_agri_dataframe, recommend_crops
from schemes_db import get_state_schemes, get_central_schemes
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

# --- 2. MOBILE-FIRST UI & CSS (STRICTLY PRESERVED + OPTIMIZED) ---
st.set_page_config(page_title="ASES Mobile", layout="wide", page_icon="🌾")

st.markdown("""
    <style>
    /* Mobile optimization for cards */
    .main-card { 
        padding: 18px; border-radius: 15px; 
        background-color: #FFFFFF; border: 1px solid #e0e0e0; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 12px;
    }
    .stButton>button { 
        border-radius: 12px; height: 3.5em; font-weight: bold;
        background-color: #2e7d32; color: white; width: 100%;
    }
    .income-card { background-color: #f1f8e9; border-left: 6px solid #4caf50; padding: 12px; border-radius: 10px; margin-bottom: 8px; }
    .expense-card { background-color: #fff8f1; border-left: 6px solid #ff9800; padding: 12px; border-radius: 10px; margin-bottom: 8px; }
    
    /* Responsive Text */
    @media (max-width: 600px) {
        h1 { font-size: 1.5rem !important; }
        .stMetric label { font-size: 0.85rem !important; }
        .stMetric div { font-size: 1.3rem !important; }
    }
    [data-testid="stSidebar"] { background-color: #243139 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA LOADING ---
df, le_encoder = get_agri_dataframe()

# --- 4. SESSION STATE ---
if 'temp' not in st.session_state: st.session_state.temp = 25
if 'hum' not in st.session_state: st.session_state.hum = 50
if 'soil_pref' not in st.session_state: st.session_state.soil_pref = "Alluvial"
if 'selected_machine' not in st.session_state: st.session_state.selected_machine = "Tractor"

# --- 5. SIDEBAR ---
state_list = list(get_state_schemes().keys())
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=100)
    st.title("ASES Menu")
    tab = st.radio("Services", ["🏠 Dashboard", "🌾 Crop Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📈 Price Trends", "📒 Agri Khata"])
    st.markdown("---")
    st_loc = st.selectbox("State", state_list if state_list else ["Bihar"])
    dt_loc = st.text_input("District", "Patna")

# --- 6. TABS LOGIC ---

if tab == "🏠 Dashboard":
    st.title("👨‍🌾 Command Center")
    with st.container():
        c1, c2, c3 = st.columns(3)
        c1.metric("🌡️ Temp", f"{st.session_state.temp}°C")
        c2.metric("💧 Hum", f"{st.session_state.hum}%")
        c3.metric("📍 Area", dt_loc)
    st.markdown(f'<div class="main-card"><b>Quick Status:</b> Ideal conditions for sowing in {dt_loc}. Check Price Trends for latest market rates.</div>', unsafe_allow_html=True)

elif tab == "🌾 Crop Engine":
    st.title("Smart Recommendation")
    st.write("Select Soil Type:")
    soil_opts = ["Alluvial", "Black Soil", "Red Soil", "Sandy"]
    cols = st.columns(2)
    for idx, s in enumerate(soil_opts):
        if cols[idx % 2].button(s, use_container_width=True): 
            st.session_state.soil_pref = s
    
    st.info(f"Current Soil: **{st.session_state.soil_pref}**")
    bud = st.slider("Investment Budget (₹)", 5000, 50000, 15000)
    
    if st.button("🚀 FIND BEST CROPS"):
        recs = recommend_crops(df, le_encoder, st.session_state.soil_pref, bud)
        for _, row in recs.iterrows():
            st.markdown(f'''
                <div class="main-card">
                    <h3 style="margin:0; color:#2e7d32;">{row["Crop Name"]}</h3>
                    <p style="margin:0;">Estimated Cost: <b>₹{row["Cost per Acre"]}</b></p>
                </div>
            ''', unsafe_allow_html=True)

elif tab == "🚜 Rental Hub":
    st.title("Machinery Rental")
    machine_types = {
        "Preparation": [("Rotavator", "🚜")],
        "Sowing": [("Seed Drill", "🌱")],
        "Harvest": [("Thresher", "🌪️")]
    }
    m_tabs = st.tabs(list(machine_types.keys()))
    for i, category in enumerate(machine_types.keys()):
        with m_tabs[i]:
            for m_name, m_icon in machine_types[category]:
                if st.button(f"{m_icon} Request {m_name}", key=f"m_{m_name}", use_container_width=True):
                    st.session_state.selected_machine = m_name
    
    st.success(f"Selected: {st.session_state.selected_machine}")
    st.link_button(f"🔍 Find Centers in {dt_loc}", f"https://www.google.com/search?q={st.session_state.selected_machine}+Rental+in+{dt_loc}", use_container_width=True)

elif tab == "📚 Knowledge Hub":
    st.title("Crop Library")
    search = st.text_input("🔍 Search Crop Name", "").strip()
    if search:
        filtered = [c for c in all_crops if search.lower() in c['Crop'].lower()]
        for item in filtered:
            with st.expander(f"📖 {item['Crop']}"):
                st.write(f"**Season:** {item['Season']} | **NPK:** {item['N-P-K']}")
                st.info(item['Pro-Tip'])
    st.dataframe(pd.DataFrame(all_crops), use_container_width=True, hide_index=True)

elif tab == "🏛️ Govt Schemes":
    st.title("Govt Welfare")
    state_schemes = get_state_schemes()
    s = state_schemes.get(st_loc, {"name": "General Farmer Support", "desc": "Visit local Krishi Bhavan", "link": "#"})
    st.markdown(f'''
        <div class="scheme-card">
            <h4>{s["name"]}</h4>
            <p style="font-size:0.9rem;">{s["desc"]}</p>
            <a href="{s["link"]}" target="_blank">View Details →</a>
        </div>
    ''', unsafe_allow_html=True)

elif tab == "📈 Price Trends":
    st.title("Market Trends")
    if all_crops:
        crop_names = [c['Crop'] for c in all_crops]
        sel_crop = st.selectbox("Select Crop", crop_names)
        weight = st.number_input("Quantity (Quintals)", min_value=0.1, value=10.0)
        season_sel = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"])
        
        base_price = 2000 + (hash(sel_crop) % 4000)
        total_val = base_price * weight
        st.metric("Estimated Valuation", f"₹{total_val:,.2f}")
        
        if st.button("📓 Save to Digital Khata"):
            add_entry("Income (Sale)", sel_crop, weight, total_val, season_sel)
            st.toast(f"Saved to {season_sel}!")

        # Preserved Graph
        months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
        trend_prices = [base_price * 0.95, base_price * 1.02, base_price * 0.98, base_price * 1.05, base_price * 1.10, base_price]
        fig = px.line(pd.DataFrame({"Month": months, "Price": trend_prices}), x="Month", y="Price", markers=True, line_shape="spline", color_discrete_sequence=["#2e7d32"])
        fig.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig, use_container_width=True)

elif tab == "📒 Agri Khata":
    st.title("Digital Ledger")
    filter_season = st.selectbox("View Season", ["All Seasons", "Kharif", "Rabi", "Zaid"])
    
    conn = sqlite3.connect('agri_khata.db')
    query = "SELECT * FROM ledger" if filter_season == "All Seasons" else f"SELECT * FROM ledger WHERE season='{filter_season}'"
    df_ledger = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df_ledger.empty:
        income = df_ledger[df_ledger['type'].str.contains('Income')]['total'].sum()
        expense = df_ledger[df_ledger['type'].str.contains('Expense')]['total'].sum()
        
        m1, m2 = st.columns(2)
        m1.metric("Earned", f"₹{income:,.0f}")
        m2.metric("Spent", f"₹{expense:,.0f}")
        
        # Action Card View for Mobile
        for _, row in df_ledger.iterrows():
            card_class = "income-card" if "Income" in row['type'] else "expense-card"
            st.markdown(f'''
                <div class="{card_class}">
                    <small>{row['date']}</small><br>
                    <b>{row['item']}</b> <span style="float:right;">₹{row['total']}</span>
                </div>
            ''', unsafe_allow_html=True)
        
        with st.expander("➕ Log New Expense"):
            e_item = st.text_input("Expense Item")
            e_amt = st.number_input("Amount (₹)", min_value=0)
            e_s = st.selectbox("Select Season", ["Kharif", "Rabi", "Zaid"], key="e_khata_mob")
            if st.button("Save Expense"):
                add_entry("Expense", e_item, "N/A", e_amt, e_s)
                st.rerun()
