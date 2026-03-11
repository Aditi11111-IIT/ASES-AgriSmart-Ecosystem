import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# 🌾 Modular Imports (Strictly Preserved) [cite: 7-13]
from crop_engine_data import get_agri_dataframe, recommend_crops
from schemes_db import get_state_schemes, get_central_schemes
try:
    from crop_master import all_crops
except ImportError:
    all_crops = []

# --- 1. DATABASE SETUP (STRICTLY PRESERVED)  ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ledger
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT, type TEXT, item TEXT, qty TEXT, total REAL, season TEXT)''') [cite: 18-20]
    conn.commit()
    conn.close()

def add_entry(entry_type, item, qty, total, season):
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO ledger (date, type, item, qty, total, season) VALUES (?,?,?,?,?,?)",
              (date, entry_type, item, str(qty), total, season)) [cite: 27-28]
    conn.commit()
    conn.close()

init_db()

# --- 2. CONFIGURATION & MOBILE STYLING (PRESERVED & ENHANCED) [cite: 32-49] ---
st.set_page_config(page_title="ASES Mobile", layout="wide", page_icon=" 🌾 ")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7" [cite: 34]

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; } [cite: 37]
    .main-card { padding: 20px; border-radius: 12px; background-color: #FFFFFF !important; border: 1px solid #2481CC; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 15px; } [cite: 38]
    .scheme-card { padding: 20px; border-radius: 12px; background-color: #e3f2fd; border-left: 8px solid #1976d2; margin-bottom: 15px; } [cite: 40]
    .central-card { padding: 20px; border-radius: 12px; background-color: #f1f8e9; border-left: 8px solid #2e7d32; margin-bottom: 15px; } [cite: 41]
    .stButton>button { border-radius: 12px; height: 3.5em; background-color: #2e7d32; color: white; width: 100%; font-weight: bold; } [cite: 43]
    
    /* Ledger Card Enhancements */
    .ledger-card { padding: 12px; border-radius: 10px; margin-bottom: 8px; border: 1px solid #ddd; }
    .income-text { color: #2e7d32; font-weight: bold; }
    .expense-text { color: #d32f2f; font-weight: bold; }

    @media (max-width: 600px) {
        .stMetric label { font-size: 0.9rem !important; }
        .stMetric div { font-size: 1.4rem !important; }
    }
    [data-testid="stSidebar"] { background-color: #243139 !important; } [cite: 46]
    [data-testid="stSidebar"] * { color: #ffffff !important; } [cite: 47]
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOAD DATA & SESSION STATE [cite: 50-56] ---
df, le_encoder = get_agri_dataframe()
if 'temp' not in st.session_state: st.session_state.temp = 25 [cite: 53]
if 'hum' not in st.session_state: st.session_state.hum = 50 [cite: 54]
if 'soil_pref' not in st.session_state: st.session_state.soil_pref = "Alluvial" [cite: 55]
if 'selected_machine' not in st.session_state: st.session_state.selected_machine = "Tractor" [cite: 56]

# --- 5. SIDEBAR (PRESERVED) [cite: 57-72] ---
state_list = list(get_state_schemes().keys()) [cite: 58]
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=100) [cite: 60]
    st.title("ASES NAVIGATION") [cite: 61]
    tab = st.radio("SELECT SERVICE", [" 🏠  Dashboard", " 🌾  Crop Engine", " 🚜  Rental Hub", " 📚  Knowledge Hub", " 🏛️  Govt Schemes", " 📈  Price Trends", " 📒  Agri Khata"]) [cite: 62]
    st_loc = st.selectbox("Your State", state_list if state_list else ["Bihar"]) [cite: 63]
    dt_loc = st.text_input("Your District", "Patna") [cite: 64]
    
    if st.button("Update Local Weather", use_container_width=True): [cite: 65]
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={dt_loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            if res.get("cod") == 200:
                st.session_state.temp, st.session_state.hum = res['main']['temp'], res['main']['humidity'] [cite: 70]
                st.success("Weather synced!") [cite: 71]
                st.rerun()
        except: st.error("Connection Error") [cite: 72]

# --- 6. TABS LOGIC (PRESERVED & MOBILE-OPTIMIZED) ---

if tab == " 🏠  Dashboard":
    st.title(" 👨‍🌾  Command Center") [cite: 75]
    c1, c2, c3 = st.columns(3) [cite: 76]
    c1.metric("Temp", f"{st.session_state.temp}°C") [cite: 77]
    c2.metric("Hum", f"{st.session_state.hum}%") [cite: 78]
    c3.metric("Loc", dt_loc) [cite: 79]

elif tab == " 🌾  Crop Engine":
    st.title("AgriAI Recommendations") [cite: 81]
    soil_opts = ["Alluvial", "Black Soil", "Red Soil", "Sandy"] [cite: 82]
    s_cols = st.columns(2) # Changed to 2 for mobile fit
    for i, s in enumerate(soil_opts):
        if s_cols[i % 2].button(s, use_container_width=True): st.session_state.soil_pref = s [cite: 85]
    st.markdown(f"Current Soil: **{st.session_state.soil_pref}**") [cite: 86]
    bud = st.slider("Budget (₹/Acre)", 5000, 50000, 15000) [cite: 87]
    if st.button(" 🚀  FIND BEST CROPS"): [cite: 88]
        recs = recommend_crops(df, le_encoder, st.session_state.soil_pref, bud) [cite: 89]
        for _, row in recs.iterrows():
            st.markdown(f'<div class="main-card"><h3>{row["Crop Name"]}</h3><p>Cost: ₹{row["Cost per Acre"]}</p></div>', unsafe_allow_html=True) [cite: 91]

elif tab == " 🚜  Rental Hub":
    st.title(f" 🚜  Rental Hub: {dt_loc}") [cite: 93]
    machine_types = {
        "Preparation": [("Rotavator", " 🚜 "), ("Power Tiller", " ⚙️ ")], [cite: 95]
        "Sowing": [("Seed Drill", " 🌱 "), ("Rice Transplanter", " 🌾 ")], [cite: 96]
        "Harvesting": [("Combine Harvester", " 🌾✨ "), ("Thresher", " 🌪️ ")] [cite: 97]
    }
    m_tabs = st.tabs(list(machine_types.keys())) [cite: 99]
    for i, category in enumerate(machine_types.keys()):
        with m_tabs[i]:
            m_cols = st.columns(2) [cite: 102]
            for idx, (m_name, m_icon) in enumerate(machine_types[category]):
                if m_cols[idx % 2].button(f"{m_icon} {m_name}", key=f"rent_{m_name}", use_container_width=True): [cite: 104]
                    st.session_state.selected_machine = m_name [cite: 105]
    st.markdown(f"**Selected:** {st.session_state.selected_machine}") [cite: 106]
    st.link_button(" 🔍  Search Centers", f"https://www.google.com/search?q={st.session_state.selected_machine}+Rental+in+{dt_loc}", use_container_width=True) [cite: 107]
    st.markdown(f'<a href="tel:18001801551" class="call-btn" style="background:#ffc107 !important; color:black !important; text-decoration:none; padding:12px; border-radius:8px; display:block; text-align:center; font-weight:bold;"> 📞  Call Helpline</a>', unsafe_allow_html=True) [cite: 108]

elif tab == " 📚  Knowledge Hub":
    st.title(" 📚  Resource Library") [cite: 110]
    search = st.text_input(" 🔍  Search Crop Name:", "").strip() [cite: 111]
    if search:
        filtered = [c for c in all_crops if search.lower() in c['Crop'].lower()] [cite: 113]
        for item in filtered:
            with st.expander(f" 📖  {item['Crop']}", expanded=True): [cite: 115]
                st.write(f"**Season:** {item['Season']} | **NPK:** {item['N-P-K']}") [cite: 116]
                st.info(f" 💡  {item['Pro-Tip']}") [cite: 117]
    st.dataframe(pd.DataFrame(all_crops), use_container_width=True, hide_index=True) [cite: 118]

elif tab == " 🏛️  Govt Schemes":
    st.title(" 🏛️  Welfare Portal") [cite: 120]
    state_schemes = get_state_schemes() [cite: 121]
    central_schemes = get_central_schemes() [cite: 122]
    choice = st.radio("Category", ["State", "Central"], horizontal=True) [cite: 123]
    if choice == "State":
        s = state_schemes.get(st_loc, {"name": "Assistance", "desc": "Visit office", "link": "#"}) [cite: 125]
        st.markdown(f'<div class="scheme-card"><h2> 🌟  {s["name"]}</h2><p>{s["desc"]}</p><a href="{s["link"]}" target="_blank"> 🔗  Portal</a></div>', unsafe_allow_html=True) [cite: 126]
    else:
        for cs in central_schemes:
            st.markdown(f'<div class="central-card"><h3> 🏢  {cs["name"]}</h3><p>{cs["desc"]}</p></div>', unsafe_allow_html=True) [cite: 129]

elif tab == " 📈  Price Trends":
    st.title(" 📈  Price Calculator") [cite: 131]
    if all_crops:
        crop_names = [c['Crop'] for c in all_crops] [cite: 133]
        sel_crop = st.selectbox("Select Crop", crop_names) [cite: 135]
        weight = st.number_input("Quantity (Q)", min_value=0.1, value=10.0) [cite: 136]
        season_sel = st.selectbox("Tag Season", ["Kharif", "Rabi", "Zaid"]) [cite: 137]
        base_price = 2000 + (hash(sel_crop) % 4000) [cite: 138]
        total_val = base_price * weight [cite: 139]
        st.metric("Total Value", f"₹{total_val:,.2f}") [cite: 140]
        if st.button(" 📓  Save to Agri Khata", use_container_width=True): [cite: 141]
            add_entry("Income (Sale)", sel_crop, weight, total_val, season_sel) [cite: 142]
            st.toast("Saved!") [cite: 143]
        
        months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"] [cite: 145]
        trend_prices = [base_price * 0.95, base_price * 1.02, base_price * 0.98, base_price * 1.05, base_price * 1.10, base_price] [cite: 146]
        fig = px.line(pd.DataFrame({"Month": months, "Price": trend_prices}), x="Month", y="Price", markers=True, line_shape="spline", color_discrete_sequence=["#2e7d32"]) [cite: 147]
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, use_container_width=True) [cite: 148]

elif tab == " 📒  Agri Khata":
    st.title(" 📒  Digital Ledger") [cite: 150]
    filter_season = st.selectbox(" 🔍  Filter Season", ["All Seasons", "Kharif", "Rabi", "Zaid"]) [cite: 151]
    conn = sqlite3.connect('agri_khata.db') [cite: 152]
    query = "SELECT * FROM ledger" if filter_season == "All Seasons" else f"SELECT * FROM ledger WHERE season='{filter_season}'" [cite: 153]
    df_ledger = pd.read_sql_query(query, conn) [cite: 154]
    conn.close() [cite: 155]
    
    if not df_ledger.empty:
        inc = df_ledger[df_ledger['type'].str.contains('Income')]['total'].sum() [cite: 157]
        exp = df_ledger[df_ledger['type'].str.contains('Expense')]['total'].sum() [cite: 158]
        st.columns(2)[0].metric("Revenue", f"₹{inc:,.0f}")
        st.columns(2)[1].metric("Investment", f"₹{exp:,.0f}")
        
        # MOBILE-FRIENDLY LEDGER CARDS
        for _, row in df_ledger.iterrows():
            t_style = "income-text" if "Income" in row['type'] else "expense-text"
            st.markdown(f'''<div class="ledger-card">
                <small>{row['date']} | {row['season']}</small><br>
                <b>{row['item']}</b> <span class="{t_style}" style="float:right;">₹{row['total']}</span>
                </div>''', unsafe_allow_html=True)
        
        with st.expander(" ➕  Log Expense"): [cite: 164]
            e_item = st.text_input("Expense Name") [cite: 165]
            e_amt = st.number_input("Amount (₹)", min_value=0) [cite: 166]
            e_s = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"], key="e_khata") [cite: 167]
            if st.button("Save Record", use_container_width=True): [cite: 168]
                add_entry("Expense", e_item, "N/A", e_amt, e_s) [cite: 169]
                st.rerun() [cite: 170]
