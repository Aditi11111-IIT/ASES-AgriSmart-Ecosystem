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

# --- 2. MOBILE-FIRST STYLING (ENHANCED) ---
st.set_page_config(page_title="ASES Mobile", layout="wide", page_icon="🌾")

st.markdown("""
    <style>
    /* Mobile optimization for cards */
    .main-card { 
        padding: 15px; border-radius: 15px; 
        background-color: #FFFFFF; border: 1px solid #e0e0e0; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 12px;
    }
    .metric-box {
        background: #f8f9fa; padding: 10px; border-radius: 10px;
        text-align: center; border: 1px solid #eee;
    }
    .stButton>button { 
        border-radius: 12px; height: 3em; font-weight: bold;
        background-color: #2e7d32; color: white;
    }
    /* Mobile text adjustments */
    @media (max-width: 600px) {
        .stMetric label { font-size: 0.8rem !important; }
        .stMetric div { font-size: 1.2rem !important; }
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

# --- 5. SIDEBAR (Preserved) ---
state_list = list(get_state_schemes().keys())
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=100)
    st.title("ASES Menu")
    tab = st.radio("Navigate", ["🏠 Dashboard", "🌾 Crop Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📈 Price Trends", "📒 Agri Khata"])
    st.markdown("---")
    st_loc = st.selectbox("State", state_list if state_list else ["Bihar"])
    dt_loc = st.text_input("District", "Patna")
    if st.button("🔄 Sync Weather"):
        st.toast("Weather Updated!") # Short feedback for mobile

# --- 6. TABS LOGIC (MOBILE OPTIMIZED VIEW) ---

if tab == "🏠 Dashboard":
    st.title("👨‍🌾 Home")
    # Using container for better mobile spacing
    with st.container():
        c1, c2, c3 = st.columns(3)
        c1.metric("🌡️ Temp", f"{st.session_state.temp}°C")
        c2.metric("💧 Hum", f"{st.session_state.hum}%")
        c3.metric("📍 Loc", dt_loc)
    st.markdown(f'<div class="main-card"><b>Status:</b> Recommended sowing season active in {st_loc}.</div>', unsafe_allow_html=True)

elif tab == "🌾 Crop Engine":
    st.title("Smart Crop Finder")
    soil_opts = ["Alluvial", "Black Soil", "Red Soil", "Sandy"]
    # Grid-like button layout for touch
    cols = st.columns(2)
    for idx, s in enumerate(soil_opts):
        if cols[idx % 2].button(s, use_container_width=True): 
            st.session_state.soil_pref = s
    
    st.write(f"Selected: **{st.session_state.soil_pref}**")
    bud = st.slider("Budget (₹/Acre)", 5000, 50000, 15000)
    
    if st.button("🚀 GET RECOMMENDATIONS", use_container_width=True):
        recs = recommend_crops(df, le_encoder, st.session_state.soil_pref, bud)
        for _, row in recs.iterrows():
            st.markdown(f'''
                <div class="main-card">
                    <h3 style="margin:0; color:#2e7d32;">{row["Crop Name"]}</h3>
                    <p style="margin:0;">Est. Cost: <b>₹{row["Cost per Acre"]}</b></p>
                </div>
            ''', unsafe_allow_html=True)

elif tab == "🚜 Rental Hub":
    st.title("Machinery Rental")
    machine_types = {
        "Prep": [("Rotavator", "🚜")],
        "Sow": [("Seed Drill", "🌱")],
        "Harvest": [("Thresher", "🌪️")]
    }
    m_tabs = st.tabs(list(machine_types.keys()))
    for i, category in enumerate(machine_types.keys()):
        with m_tabs[i]:
            for m_name, m_icon in machine_types[category]:
                if st.button(f"{m_icon} Rent {m_name}", key=f"m_{m_name}", use_container_width=True):
                    st.session_state.selected_machine = m_name
    
    st.info(f"Finding: {st.session_state.selected_machine}")
    st.link_button(f"🔍 Search Near {dt_loc}", f"https://www.google.com/search?q={st.session_state.selected_machine}+Rental+in+{dt_loc}", use_container_width=True)

elif tab == "📚 Knowledge Hub":
    st.title("Crop Library")
    search = st.text_input("🔍 Search Crop", "").strip()
    if search:
        filtered = [c for c in all_crops if search.lower() in c['Crop'].lower()]
        for item in filtered:
            with st.expander(f"📖 {item['Crop']}"):
                st.write(f"**Season:** {item['Season']}")
                st.info(item['Pro-Tip'])
    st.dataframe(pd.DataFrame(all_crops), use_container_width=True, hide_index=True)

elif tab == "🏛️ Govt Schemes":
    st.title("Govt Welfare")
    state_schemes = get_state_schemes()
    s = state_schemes.get(st_loc, {"name": "Assistance", "desc": "Visit Block Office", "link": "#"})
    st.markdown(f'''
        <div class="scheme-card">
            <h4>{s["name"]}</h4>
            <p style="font-size:0.9rem;">{s["desc"]}</p>
            <a href="{s["link"]}" target="_blank">Register Now →</a>
        </div>
    ''', unsafe_allow_html=True)

elif tab == "📈 Price Trends":
    st.title("Market Prices")
    if all_crops:
        crop_names = [c['Crop'] for c in all_crops]
        sel_crop = st.selectbox("Crop", crop_names)
        weight = st.number_input("Quantity (Q)", min_value=0.1, value=5.0)
        season_sel = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"])
        
        base_price = 2000 + (hash(sel_crop) % 4000)
        total_val = base_price * weight
        st.success(f"Est. Value: ₹{total_val:,.2f}")
        
        if st.button("📓 Add to Khata", use_container_width=True):
            add_entry("Income", sel_crop, weight, total_val, season_sel)
            st.toast("Saved!")

        # Graph preserved
        months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
        trend_prices = [base_price * 0.95, base_price * 1.05, base_price * 0.98, base_price * 1.02, base_price * 1.10, base_price]
        fig = px.line(pd.DataFrame({"Month": months, "Price": trend_prices}), x="Month", y="Price", markers=True, line_shape="spline", color_discrete_sequence=["#2e7d32"])
        fig.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=300)
        st.plotly_chart(fig, use_container_width=True)

elif tab == "📒 Agri Khata":
    st.title("Digital Ledger")
    filter_season = st.selectbox("Filter Season", ["All Seasons", "Kharif", "Rabi", "Zaid"])
    
    conn = sqlite3.connect('agri_khata.db')
    query = "SELECT * FROM ledger" if filter_season == "All Seasons" else f"SELECT * FROM ledger WHERE season='{filter_season}'"
    df_ledger = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df_ledger.empty:
        income = df_ledger[df_ledger['type'].str.contains('Income')]['total'].sum()
        expense = df_ledger[df_ledger['type'].str.contains('Expense')]['total'].sum()
        
        # Mobile-friendly Metrics
        m1, m2 = st.columns(2)
        m1.metric("Earned", f"₹{income:,.0f}")
        m2.metric("Spent", f"₹{expense:,.0f}")
        
        # CARD VIEW for Ledger (Better for Mobile)
        for _, row in df_ledger.iterrows():
            color = "#e8f5e9" if "Income" in row['type'] else "#ffebee"
            st.markdown(f'''
                <div style="background:{color}; padding:12px; border-radius:10px; margin-bottom:8px; border:1px solid #ddd;">
                    <small>{row['date']} | {row['season']}</small><br>
                    <b>{row['item']}</b>: <span style="float:right;">₹{row['total']}</span>
                </div>
            ''', unsafe_allow_html=True)
        
        with st.expander("➕ Add New Expense"):
            e_item = st.text_input("Item")
            e_amt = st.number_input("Amount", min_value=0)
            e_s = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"], key="e_mob")
            if st.button("Save Record", use_container_width=True):
                add_entry("Expense", e_item, "N/A", e_amt, e_s)
                st.rerun()
