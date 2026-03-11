import streamlit as st
import pandas as pd
import json
import random
import plotly.express as px
import requests
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import LabelEncoder

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="ASES: Agri-Smart Ecosystem", layout="wide", page_icon="🌾")

# 🔑 Updated OpenWeatherMap API Key
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
    .highlight-text { color: #2481CC !important; font-weight: bold; }
    .stButton>button { border-radius: 8px; background-color: #2e7d32; color: white; width: 100%; }
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

def load_schemes():
    try:
        with open('schemes_db.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading schemes_db.json: {e}")
        return {}

df = load_agri_data()
schemes_data = load_schemes()
le = LabelEncoder()
df['Soil_Idx'] = le.fit_transform(df['Soil Type'])

# --- 3. SESSION STATE ---
if 'temp' not in st.session_state: st.session_state.temp = 25
if 'hum' not in st.session_state: st.session_state.hum = 50
if 'soil_pref' not in st.session_state: st.session_state.soil_pref = "Alluvial"

# --- 4. NAVIGATION & SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    st.title("ASES NAVIGATION")
    tab = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🌾 Crop Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📈 Price Trends", "📒 Agri Khata"])
    
    st.markdown("---")
    st_loc = st.selectbox("Your State", list(schemes_data.keys()) if schemes_data else ["Bihar"])
    
    if st.button("Update Local Weather"):
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={st_loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            
            if res.get("cod") == 200:
                st.session_state.temp = res['main']['temp']
                st.session_state.hum = res['main']['humidity']
                st.success(f"Weather synced for {st_loc}!")
            else:
                st.error(f"Weather API Error: {res.get('message')}")
                # Fallback data if key is inactive
                st.session_state.temp = random.randint(22, 32)
                st.session_state.hum = random.randint(45, 65)
        except Exception as e:
            st.error(f"Connection Error: {e}")

# --- 5. TABS LOGIC ---

if tab == "🏠 Dashboard":
    st.title(f"👨‍🌾 Command Center")
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperature", f"{st.session_state.temp}°C")
    col2.metric("Humidity", f"{st.session_state.hum}%")
    col3.metric("Location Status", st_loc)
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
        recs = df.iloc[idx[0]]
        for _, row in recs.iterrows():
            st.markdown(f'<div class="main-card"><h3>{row["Crop Name"]}</h3><p>Cost: ₹{row["Cost per Acre"]}</p></div>', unsafe_allow_html=True)

elif tab == "🚜 Rental Hub":
    st.title("🚜 Rental Machinery Desk")
    machine = st.text_input("Machine Type", "Tractor")
    st.link_button(f"🔍 Search Rental Centers", f"https://www.google.com/search?q={machine}+Rental+in+{st_loc}")

elif tab == "📚 Knowledge Hub":
    try:
        from crop_master import all_crops
    except ImportError:
        st.error("Missing crop_master.py")
        all_crops = []

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
    st.subheader("📊 All Crops Tabular View")
    st.dataframe(pd.DataFrame(all_crops), use_container_width=True, hide_index=True)

elif tab == "🏛️ Govt Schemes":
    st.title(f"🏛️ Agricultural Schemes: {st_loc}")
    if st_loc in schemes_data:
        scheme = schemes_data[st_loc]
        st.markdown(f"""
            <div class="scheme-card">
                <h2>🌟 {scheme['name']}</h2>
                <p style="font-size:18px;">{scheme['desc']}</p>
                <a href="{scheme['link']}" target="_blank" style="color:#1976d2; font-weight:bold;">🔗 Visit Official Portal</a>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("No specific scheme found for this location.")

elif tab == "📈 Price Trends":
    st.title("📈 Market Price Forecasting")
    data_p = pd.DataFrame({"Month": ["Jan", "Feb", "Mar", "Apr"], "Price": [2200, 2450, 2300, 2600]})
    st.plotly_chart(px.line(data_p, x="Month", y="Price", title="Price Trend for Wheat (Sample)"))

elif tab == "📒 Agri Khata":
    st.title("📒 Financial Ledger")
    st.write("Track your farming expenses and income here.")
