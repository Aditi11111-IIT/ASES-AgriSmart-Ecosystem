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

# --- 2. CONFIGURATION & TRICOLOR STYLING ---
st.set_page_config(page_title="ASES Mobile", layout="wide", page_icon="🌾")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #2e7d32 !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .main-card { padding: 20px; border-radius: 12px; background-color: #FFFFFF; border: 2px solid #2e7d32; margin-bottom: 15px; }
    .scheme-card { padding: 20px; border-radius: 12px; background-color: #fff3e0; border-left: 8px solid #ff9800; margin-bottom: 15px; }
    .stButton>button { border-radius: 12px; height: 3.5em; background-color: #2e7d32; color: white; width: 100%; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #ff9800; }
    .ledger-card { padding: 12px; border-radius: 10px; margin-bottom: 8px; border: 1px solid #eee; background: white; }
    .income-text { color: #2e7d32; font-weight: bold; }
    .expense-text { color: #ff9800; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOCATION DATA (MODULAR DISTRICTS) ---
# This dictionary maps states to their corresponding districts
districts_map = {
    "Bihar": ["Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur", "Bhojpur", "Buxar", "Darbhanga", "Gaya", "Patna"],
    "Punjab": ["Amritsar", "Barnala", "Bathinda", "Ferozepur", "Gurdaspur", "Jalandhar", "Ludhiana", "Patiala"],
    "Uttar Pradesh": ["Agra", "Aligarh", "Ayodhya", "Kanpur", "Lucknow", "Prayagraj", "Varanasi"],
    "Maharashtra": ["Ahmednagar", "Amravati", "Aurangabad", "Nagpur", "Nashik", "Pune", "Thane"]
}

# --- 4. DATA & SESSION STATE ---
df, le_encoder = get_agri_dataframe()
if 'temp' not in st.session_state: st.session_state.temp = 25
if 'hum' not in st.session_state: st.session_state.hum = 50
if 'soil_pref' not in st.session_state: st.session_state.soil_pref = "Alluvial"
if 'selected_machine' not in st.session_state: st.session_state.selected_machine = "Tractor"

# --- 5. SIDEBAR (DISTRICT CHOICE IMPLEMENTED) ---
state_list = list(get_state_schemes().keys()) if get_state_schemes() else list(districts_map.keys())

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    st.title("ASES NAVIGATION")
    tab = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🌾 Crop Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📈 Price Trends", "📒 Agri Khata"])
    st.markdown("---")
    
    # User chooses State first
    st_loc = st.selectbox("Choose State", state_list)
    
    # Districts dropdown updates based on State choice
    available_districts = districts_map.get(st_loc, ["Patna"])
    dt_loc = st.selectbox("Choose District", available_districts)
    
    if st.button("🔄 Sync Local Weather", use_container_width=True):
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={dt_loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            if res.get("cod") == 200:
                st.session_state.temp, st.session_state.hum = res['main']['temp'], res['main']['humidity']
                st.success(f"Weather updated for {dt_loc}!")
                st.rerun()
        except: st.error("Weather Service Unavailable")

# --- 6. TABS LOGIC ---

if tab == "🏠 Dashboard":
    st.title("👨‍🌾 Command Center")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperature", f"{st.session_state.temp}°C")
    c2.metric("Humidity", f"{st.session_state.hum}%")
    c3.metric("District", dt_loc)
    st.markdown(f'<div class="main-card" style="border-left: 8px solid #ff9800;"><b>Status:</b> Actively tracking conditions in {dt_loc}, {st_loc}.</div>', unsafe_allow_html=True)

elif tab == "🌾 Crop Engine":
    st.title("Smart Recommendations")
    soil_opts = ["Alluvial", "Black Soil", "Red Soil", "Sandy"]
    s_cols = st.columns(2)
    for i, s in enumerate(soil_opts):
        if s_cols[i % 2].button(s, use_container_width=True): st.session_state.soil_pref = s
    st.info(f"Selected Soil: **{st.session_state.soil_pref}**")
    bud = st.slider("Budget (₹/Acre)", 5000, 50000, 15000)
    if st.button("🚀 FIND BEST CROPS"):
        recs = recommend_crops(df, le_encoder, st.session_state.soil_pref, bud)
        for _, row in recs.iterrows():
            st.markdown(f'<div class="main-card"><h3 style="color:#2e7d32;">{row["Crop Name"]}</h3><p>Cost: <b>₹{row["Cost per Acre"]}</b></p></div>', unsafe_allow_html=True)

elif tab == "🚜 Rental Hub":
    st.title(f"🚜 Rental Machinery: {dt_loc}")
    machine_types = {
        "Preparation": [("Rotavator", "🚜"), ("Power Tiller", "⚙️")],
        "Sowing": [("Seed Drill", "🌱"), ("Rice Transplanter", "🌾")],
        "Harvesting": [("Combine Harvester", "🌾✨"), ("Thresher", "🌪️")]
    }
    m_tabs = st.tabs(list(machine_types.keys()))
    for i, category in enumerate(machine_types.keys()):
        with m_tabs[i]:
            m_cols = st.columns(2)
            for idx, (m_name, m_icon) in enumerate(machine_types[category]):
                if m_cols[idx % 2].button(f"{m_icon} {m_name}", key=f"rent_{m_name}", use_container_width=True):
                    st.session_state.selected_machine = m_name
    st.success(f"Selected: {st.session_state.selected_machine}")
    st.link_button("🔍 Find Centers Nearby", f"https://www.google.com/search?q={st.session_state.selected_machine}+Rental+in+{dt_loc}", use_container_width=True)
    st.markdown(f'<a href="tel:18001801551" style="background:#ff9800; color:white; text-decoration:none; padding:15px; border-radius:12px; display:block; text-align:center; font-weight:bold;">📞 Call Agri-Helpline</a>', unsafe_allow_html=True)

elif tab == "📚 Knowledge Hub":
    st.title("📚 Resource Library")
    search = st.text_input("🔍 Search Crop:", "").strip()
    if search:
        filtered = [c for c in all_crops if search.lower() in c['Crop'].lower()]
        for item in filtered:
            with st.expander(f"📖 {item['Crop']}"):
                st.write(f"**Season:** {item['Season']} | **NPK:** {item['N-P-K']}")
                st.info(f"💡 {item['Pro-Tip']}")
    st.dataframe(pd.DataFrame(all_crops), use_container_width=True, hide_index=True)

elif tab == "🏛️ Govt Schemes":
    st.title("🏛️ Welfare Portal")
    state_schemes = get_state_schemes()
    central_schemes = get_central_schemes()
    choice = st.radio("Category", ["State", "Central"], horizontal=True)
    if choice == "State":
        s = state_schemes.get(st_loc, {"name": "General Assistance", "desc": "Visit local office", "link": "#"})
        st.markdown(f'<div class="scheme-card"><h2>🌟 {s["name"]}</h2><p>{s["desc"]}</p><a href="{s["link"]}" target="_blank" style="color:#ff9800; font-weight:bold;">🔗 Open Portal</a></div>', unsafe_allow_html=True)
    else:
        for cs in central_schemes:
            st.markdown(f'<div class="main-card" style="border-left: 8px solid #2e7d32;"><h3>🏢 {cs["name"]}</h3><p>{cs["desc"]}</p></div>', unsafe_allow_html=True)

elif tab == "📈 Price Trends":
    st.title("📈 Market Prices")
    if all_crops:
        crop_names = [c['Crop'] for c in all_crops]
        sel_crop = st.selectbox("Select Crop", crop_names)
        weight = st.number_input("Quantity (Q)", min_value=0.1, value=10.0)
        season_sel = st.selectbox("Tag Season", ["Kharif", "Rabi", "Zaid"])
        base_price = 2000 + (hash(sel_crop) % 4000)
        total_val = base_price * weight
        st.metric("Estimated Market Value", f"₹{total_val:,.2f}")
        if st.button("📓 Log to Agri Khata"):
            add_entry("Income (Sale)", sel_crop, weight, total_val, season_sel)
            st.toast("Entry added successfully!")
        
        months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
        trend_prices = [base_price * 0.95, base_price * 1.02, base_price * 0.98, base_price * 1.05, base_price * 1.10, base_price]
        fig = px.line(pd.DataFrame({"Month": months, "Price": trend_prices}), x="Month", y="Price", markers=True, color_discrete_sequence=["#2e7d32"])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0), plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

elif tab == "📒 Agri Khata":
    st.title("📒 Seasonal Digital Ledger")
    filter_season = st.selectbox("🔍 Filter Season", ["All Seasons", "Kharif", "Rabi", "Zaid"])
    conn = sqlite3.connect('agri_khata.db')
    query = "SELECT * FROM ledger" if filter_season == "All Seasons" else f"SELECT * FROM ledger WHERE season='{filter_season}'"
    df_ledger = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df_ledger.empty:
        inc = df_ledger[df_ledger['type'].str.contains('Income')]['total'].sum()
        exp = df_ledger[df_ledger['type'].str.contains('Expense')]['total'].sum()
        c1, c2 = st.columns(2)
        c1.metric("Revenue (Green)", f"₹{inc:,.0f}")
        c2.metric("Investment (Orange)", f"₹{exp:,.0f}")
        
        for _, row in df_ledger.iterrows():
            is_income = "Income" in row['type']
            t_class = "income-text" if is_income else "expense-text"
            border_color = "#2e7d32" if is_income else "#ff9800"
            st.markdown(f'''<div class="ledger-card" style="border-left: 6px solid {border_color};">
                <small>{row['date']} | {row['season']}</small><br>
                <b>{row['item']}</b> <span class="{t_class}" style="float:right;">₹{row['total']}</span>
                </div>''', unsafe_allow_html=True)
        
        with st.expander("➕ Add New Record"):
            e_item = st.text_input("Expense Name")
            e_amt = st.number_input("Amount (₹)", min_value=0)
            e_s = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"], key="e_khata")
            if st.button("Save Entry", use_container_width=True):
                add_entry("Expense", e_item, "N/A", e_amt, e_s)
                st.rerun()
