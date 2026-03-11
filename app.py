import streamlit as st
import pandas as pd
import json
import random
import plotly.express as px
import requests
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import LabelEncoder

# 🌾 Import your modular data files
from schemes_db import get_state_schemes, get_central_schemes
try:
    from crop_master import all_crops
except ImportError:
    all_crops = []

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="ASES: Agri-Smart Ecosystem", layout="wide", page_icon="🌾")

# 🔑 OpenWeatherMap API Key
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .main-card { 
        padding: 25px; border-radius: 12px; 
        background-color: #FFFFFF !important; 
        border: 1px solid #2481CC; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
        margin-bottom: 20px;
    }
    .scheme-card {
        padding: 20px; border-radius: 12px;
        background-color: #e3f2fd; border-left: 8px solid #1976d2;
        margin-bottom: 15px;
    }
    .central-card {
        padding: 20px; border-radius: 12px;
        background-color: #f1f8e9; border-left: 8px solid #2e7d32;
        margin-bottom: 15px;
    }
    .highlight-text { color: #2481CC !important; font-weight: bold; }
    .stButton>button { border-radius: 8px; background-color: #2e7d32; color: white; width: 100%; }
    .call-btn {
        background-color: #28a745 !important; color: white !important;
        padding: 12px; border-radius: 8px; text-decoration: none;
        display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }
    [data-testid="stSidebar"] { background-color: #243139 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINES ---
@st.cache_data
def load_agri_data():
    crops = {
        'Crop Name': ['Wheat', 'Rice', 'Cotton', 'Maize', 'Groundnut', 'Soybean', 'Mustard', 'Sugarcane', 'Chickpea', 'Potato'],
        'Soil Type': ['Alluvial', 'Alluvial', 'Black Soil', 'Red Soil', 'Sandy', 'Black Soil', 'Alluvial', 'Loamy', 'Heavy Soil', 'Sandy Loam'],
        'Sowing Month': [11, 6, 6, 6, 5, 6, 10, 2, 10, 10],
        'Cost per Acre': [15000, 25000, 20000, 12000, 18000, 16000, 14000, 30000, 13000, 35000]
    }
    return pd.DataFrame(crops)

df = load_agri_data()
le = LabelEncoder()
df['Soil_Idx'] = le.fit_transform(df['Soil Type'])

# --- 3. SESSION STATE ---
if 'temp' not in st.session_state: st.session_state.temp = 25
if 'hum' not in st.session_state: st.session_state.hum = 50
if 'soil_pref' not in st.session_state: st.session_state.soil_pref = "Alluvial"
if 'selected_machine' not in st.session_state: st.session_state.selected_machine = "Tractor"

# --- 4. NAVIGATION & SIDEBAR ---
# Load states for the selectbox from your schemes_db
state_list = list(get_state_schemes().keys())

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    st.title("ASES NAVIGATION")
    tab = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🌾 Crop Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📈 Price Trends", "📒 Agri Khata"])
    
    st.markdown("---")
    st_loc = st.selectbox("Your State", state_list if state_list else ["Bihar"])
    dt_loc = st.text_input("Your District", "Patna")
    
    if st.button("Update Local Weather"):
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={st_loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            if res.get("cod") == 200:
                st.session_state.temp, st.session_state.hum = res['main']['temp'], res['main']['humidity']
                st.success(f"Weather synced for {st_loc}!")
            else:
                st.error(f"Weather API Error: {res.get('message')}")
        except: st.error("Connection Error")

# --- 5. TABS LOGIC ---

if tab == "🏠 Dashboard":
    st.title(f"👨‍🌾 Command Center")
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperature", f"{st.session_state.temp}°C")
    col2.metric("Humidity", f"{st.session_state.hum}%")
    col3.metric("Location Status", f"{dt_loc}, {st_loc}")
    st.info("Check 'Govt Schemes' tab for state-specific subsidies!")

elif tab == "🌾 Crop Engine":
    st.title("AgriAI Smart Recommendations")
    soil_opts = ["Alluvial", "Black Soil", "Red Soil", "Sandy"]
    s_cols = st.columns(4)
    for i, s in enumerate(soil_opts):
        if s_cols[i].button(s): st.session_state.soil_pref = s
    
    st.markdown(f"Current Soil: **{st.session_state.soil_pref}**")
    bud = st.slider("Investment Budget (₹/Acre)", 5000, 50000, 15000)
    
    if st.button("🚀 FIND BEST CROPS"):
        X = df[['Soil_Idx', 'Sowing Month', 'Cost per Acre']]
        knn = NearestNeighbors(n_neighbors=2).fit(X)
        u_idx = le.transform([st.session_state.soil_pref])[0]
        _, idx = knn.kneighbors([[u_idx, 6, bud]])
        for _, row in df.iloc[idx[0]].iterrows():
            st.markdown(f'<div class="main-card"><h3>{row["Crop Name"]}</h3><p>Cost: ₹{row["Cost per Acre"]}</p></div>', unsafe_allow_html=True)

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
            m_cols = st.columns(2)
            for idx, (m_name, m_icon) in enumerate(machine_types[category]):
                if m_cols[idx % 2].button(f"{m_icon} {m_name}", key=f"rent_{m_name}"):
                   st.session_state.selected_machine = m_name

    st.markdown(f"**Currently Finding:** <span class='highlight-text'>{st.session_state.selected_machine}</span>", unsafe_allow_html=True)
    search_query = f"{st.session_state.selected_machine}+Rental+in+{dt_loc}+{st_loc}"
    st.link_button(f"🔍 Search Commercial {st.session_state.selected_machine} Centers", f"https://www.google.com/search?q={search_query}", use_container_width=True)
    st.markdown(f'<a href="tel:18001801551" class="call-btn" style="background:#ffc107 !important; color:black !important;">📞 Call Govt CHC Helpline</a>', unsafe_allow_html=True)

elif tab == "📚 Knowledge Hub":
    st.title("📚 Crop Resource Library")
    search = st.text_input("🔍 Search Crop Name:", "").strip()
    if search:
        filtered = [c for c in all_crops if search.lower() in c['Crop'].lower()]
        for item in filtered:
            with st.expander(f"📖 {item['Crop']} - Detailed Guidelines", expanded=True):
                st.write(f"**Season:** {item['Season']} | **NPK:** {item['N-P-K']}")
                st.write(f"**Soil:** {item['Soil']} | **Water:** {item['Water']}")
                st.info(f"💡 {item['Pro-Tip']}")
    st.markdown("---")
    st.dataframe(pd.DataFrame(all_crops), use_container_width=True, hide_index=True)

elif tab == "🏛️ Govt Schemes":
    st.title("🏛️ Agricultural Welfare & Registration Portal")
    
    # --- Instructions Section ---
    with st.expander("📖 How to use this Portal", expanded=True):
        st.write("""
        1. **Select Category:** Choose between 'State-Specific' or 'Central Govt' schemes.
        2. **Update Location:** If you don't see your state, change it in the **Sidebar** on the left.
        3. **Register:** Click the '🔗 Visit Official Portal' link to open the government registration page in a new tab.
        """)

    # Load data from modular file
    state_schemes = get_state_schemes()
    central_schemes = get_central_schemes()

    choice = st.radio("Select Scheme Type", ["State-Specific Schemes", "Central Govt Schemes"], horizontal=True)

    if choice == "State-Specific Schemes":
        st.subheader(f"📍 Active Schemes in {st_loc}")
        if st_loc in state_schemes:
            s = state_schemes[st_loc]
            st.markdown(f"""
                <div class="scheme-card">
                    <h2>🌟 {s['name']}</h2>
                    <p style="font-size:18px;">{s['desc']}</p>
                    <a href="{s['link']}" target="_blank" style="color:#1976d2; font-weight:bold; font-size:20px;">
                        🔗 Visit Official {st_loc} Registration Portal
                    </a>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No state-specific data found for the selected location.")

    else:
        st.subheader("🇮🇳 Pan-India Central Government Schemes")
        for cs in central_schemes:
            st.markdown(f"""
                <div class="central-card">
                    <h3>🏢 {cs['name']}</h3>
                    <p>{cs['desc']}</p>
                    <a href="{cs['link']}" target="_blank" style="color:#2e7d32; font-weight:bold;">🔗 Open Registration Portal</a>
                </div>
            """, unsafe_allow_html=True)

elif tab == "📈 Price Trends":
    st.title("📈 Market Price Forecasting")
    data_p = pd.DataFrame({"Month": ["Jan", "Feb", "Mar", "Apr"], "Price": [2200, 2450, 2300, 2600]})
    st.plotly_chart(px.line(data_p, x="Month", y="Price", title="Price Trend for Wheat (Sample)"))

elif tab == "📒 Agri Khata":
    st.title("📒 Financial Ledger")
    st.write("Track your farming expenses and income here.")
